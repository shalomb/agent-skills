import asyncio
import os
import json
import re
import base64
from typing import List, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

try:
    from .models import TeamsMessage, ImageMetadata
    from .parser import TeamsParser
except ImportError:
    from models import TeamsMessage, ImageMetadata
    from parser import TeamsParser

def _default_chrome_path() -> str:
    """Return platform-appropriate Chrome path, overridable via CHROME_PATH env var."""
    import platform
    env = os.environ.get("CHROME_PATH")
    if env:
        return env
    if platform.system() == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    for p in ("/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"):
        if os.path.exists(p):
            return p
    return "google-chrome"  # fallback: rely on PATH

def _state_dir(subdir: str) -> str:
    """XDG_STATE_HOME — persistent state that must survive reboots (e.g. browser session).
    Not safe to delete. Default: ~/.local/state/agent-skills/teams-headless/"""
    base = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    path = os.path.join(base, "agent-skills", "teams-headless", subdir)
    os.makedirs(path, exist_ok=True)
    return path

def _cache_dir(subdir: str) -> str:
    """XDG_CACHE_HOME — non-essential, safe to delete (e.g. downloaded images).
    Default: ~/.cache/agent-skills/teams-headless/"""
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    path = os.path.join(base, "agent-skills", "teams-headless", subdir)
    os.makedirs(path, exist_ok=True)
    return path

CHROME_PATH = _default_chrome_path()
USER_DATA_DIR = _state_dir("user_data")   # browser profile + login cookies
DOWNLOAD_DIR = _cache_dir("downloads")    # temp files — safe to delete

async def get_recent_chat_messages(target_name: Optional[str] = None, limit: int = 10):
    # DOWNLOAD_DIR already created by _cache_dir()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=False, 
            viewport={"width": 1280, "height": 900}
        )
        page = context.pages[0]
        print("Navigating to Teams V2...")
        await page.goto("https://teams.microsoft.com/v2/")

        # Banner Handling
        await asyncio.sleep(5)
        await page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button'));
            let restart = btns.find(b => b.innerText.includes('Apply and restart'));
            if (restart) restart.click();
        }""")

        # Switch to Chat tab
        try:
            await page.evaluate("""() => {
                let btn = document.querySelector('button[data-tid="3b64df9d-7e97-4d9c-ac5c-2e0a5d8e6f40"]');
                if (btn) btn.click();
            }""")
            await asyncio.sleep(5)
        except: pass

        if target_name:
            print(f"Searching for chat: {target_name}...")
            search_input = page.locator('input[data-tid="AUTOSUGGEST_INPUT"]')
            await search_input.click()
            await search_input.fill(target_name)
            await asyncio.sleep(3)
            
            try:
                top_hits = page.locator('div[data-tid="AUTOSUGGEST_GROUP_TOPHITS"]')
                suggestion = top_hits.locator('div[data-tid^="AUTOSUGGEST_SUGGESTION_TOPHITS"]').first
                
                if await suggestion.count() > 0:
                    await suggestion.click()
                else:
                    await page.locator('div[role="listbox"] div[role="option"]').first.click()
                
                print(f"Clicked search result for {target_name}")
                
                # Poll for content appearance
                found_content = False
                for _ in range(15):
                    for f in page.frames:
                        try:
                            if await f.locator('div[data-tid="message-body"]').count() > 0:
                                found_content = True
                                break
                        except: continue
                    if found_content: break
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"Error during search/selection: {e}")

        print("Extracting messages...")
        
        messages = []
        for frame in page.frames:
            try:
                elements = await frame.locator('div[data-tid="chat-pane-item"]').all()
                if not elements: continue
                
                print(f"Found {len(elements)} messages in frame.")
                start_idx = max(0, len(elements) - limit)
                
                for el in elements[start_idx:]:
                    author = "Unknown"
                    author_el = el.locator('span[data-tid="message-author-name"]')
                    if await author_el.count() > 0:
                        author = await author_el.first.inner_text()
                    
                    timestamp = None
                    ts_el = el.locator('time[datetime]')
                    if await ts_el.count() > 0:
                        timestamp = await ts_el.first.get_attribute("datetime") or await ts_el.first.inner_text()

                    body_container = el.locator('div[data-tid="chat-pane-message"], div[data-message-content]')
                    if await body_container.count() > 0:
                        body_html = await body_container.first.inner_html()
                        
                        msg = TeamsParser.parse_message(
                            body_html=body_html,
                            author=author,
                            timestamp=timestamp
                        )
                        messages.append(msg)
                
                if messages: break
            except: continue

        await context.close()
        return [m.model_dump() for m in messages]

async def get_meeting_recap(target_name: str):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=False,
            viewport={"width": 1280, "height": 900}
        )
        page = context.pages[0]
        await page.goto("https://teams.microsoft.com/v2/")

        # Banner & App Switch
        await asyncio.sleep(5)
        await page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button'));
            let restart = btns.find(b => b.innerText.includes('Apply and restart'));
            if (restart) restart.click();
        }""")
        
        try:
            await page.evaluate("""() => {
                let btn = document.querySelector('button[data-tid="3b64df9d-7e97-4d9c-ac5c-2e0a5d8e6f40"]');
                if (btn) btn.click();
            }""")
            await asyncio.sleep(5)
        except: pass

        # Search and Select
        print(f"Searching for chat: {target_name}...")
        search_input = page.locator('input[data-tid="AUTOSUGGEST_INPUT"]')
        await search_input.click()
        await search_input.fill(target_name)
        await asyncio.sleep(3)
        
        try:
            suggestion = page.locator('div[data-tid="AUTOSUGGEST_GROUP_TOPHITS"] div[data-tid^="AUTOSUGGEST_SUGGESTION_TOPHITS"]').first
            if await suggestion.count() > 0:
                await suggestion.click()
            else:
                await page.locator('div[role="listbox"] div[role="option"]').first.click()
            
            print("Chat selected. Waiting for load...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Selection failed: {e}")

        # Find and click "View recap"
        print("Looking for 'View recap' button...")
        try:
            recap_btn = page.locator('button:has-text("View recap")').last
            await recap_btn.click()
            print("Clicked 'View recap'. Waiting for hydration...")
            await asyncio.sleep(10)

            transcript_tab = page.locator('button[role="tab"]:has-text("Transcript"), div[role="tab"]:has-text("Transcript")').first
            if await transcript_tab.count() > 0:
                await transcript_tab.click()
                print("Switched to Transcript tab.")
                await asyncio.sleep(5)

            # Extract Transcript Content
            print("Extracting transcript via deep search...")
            for frame in page.frames:
                try:
                    transcript_elements = await frame.evaluate("""() => {
                        let res = [];
                        let els = document.querySelectorAll('div[data-tid="transcript-item"], div.ui-transcript__item, div[role="listitem"]');
                        for (let el of els) {
                            if (el.innerText && el.innerText.length > 5) {
                                res.push(el.innerText.trim());
                            }
                        }
                        return res;
                    }""")
                    
                    if transcript_elements:
                        print(f"Found {len(transcript_elements)} transcript segments.")
                        await context.close()
                        return [{"author": "Transcript", "body": "\\n".join(transcript_elements)}]
                except: continue

            main_text = await page.locator('div[data-tid="app-layout-area--main"]').inner_text()
            await context.close()
            return [{"author": "Recap Fallback", "body": main_text}]

        except Exception as e:
            print(f"Failed to extract recap: {e}")
            await context.close()
            return []

if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?")
    parser.add_argument("--recap", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.recap:
        if not args.name:
            print("Error: Name required for recap.")
            sys.exit(1)
        results = asyncio.run(get_meeting_recap(args.name))
    else:
        results = asyncio.run(get_recent_chat_messages(args.name, args.limit))
    
    print(json.dumps(results, indent=2))
