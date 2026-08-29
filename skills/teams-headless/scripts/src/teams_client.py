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
    """XDG_STATE_HOME — persistent state that must survive reboots.
    Not safe to delete. Default: ~/.local/state/agent-skills/teams-headless/"""
    base = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    path = os.path.join(base, "agent-skills", "teams-headless", subdir)
    os.makedirs(path, exist_ok=True)
    return path

def _cache_dir(subdir: str) -> str:
    """XDG_CACHE_HOME — non-essential, safe to delete.
    Default: ~/.cache/agent-skills/teams-headless/"""
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    path = os.path.join(base, "agent-skills", "teams-headless", subdir)
    os.makedirs(path, exist_ok=True)
    return path

CHROME_PATH = _default_chrome_path()
USER_DATA_DIR = _state_dir("user_data")   # browser profile + login cookies
DOWNLOAD_DIR = _cache_dir("downloads")    # temp files — safe to delete


class TeamsClient:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.context: Optional[BrowserContext] = None
        self.p = None

    async def __aenter__(self):
        self.p = await async_playwright().start()
        self.context = await self.p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=self.headless,
            viewport={"width": 1280, "height": 900}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.p:
            await self.p.stop()

    async def _navigate_and_wait(self, page: Page):
        """Navigate to Teams and wait for the app to load."""
        await page.goto("https://teams.microsoft.com/v2/")

        # Dismiss "Apply and restart" banner if present
        await asyncio.sleep(3)
        await page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button'));
            let restart = btns.find(b => b.innerText.includes('Apply and restart'));
            if (restart) restart.click();
        }""")
        await asyncio.sleep(2)

    async def is_logged_in(self) -> bool:
        """Check if we are currently logged in to Teams."""
        if not self.context:
            return False
        page = self.context.pages[0]
        try:
            await self._navigate_and_wait(page)
            await page.wait_for_selector(
                'input[data-tid="AUTOSUGGEST_INPUT"], '
                'div[data-tid="chat-list"], '
                'button[data-tid="3b64df9d-7e97-4d9c-ac5c-2e0a5d8e6f40"]',
                timeout=15000
            )
            return True
        except:
            return False

    async def _switch_to_chat(self, page: Page):
        """Click the Chat tab in Teams."""
        try:
            await page.evaluate("""() => {
                let btn = document.querySelector('button[data-tid="3b64df9d-7e97-4d9c-ac5c-2e0a5d8e6f40"]');
                if (btn) btn.click();
            }""")
            await asyncio.sleep(3)
        except:
            pass

    async def _search_and_select(self, page: Page, target_name: str):
        """Search for a chat/meeting by name and click it."""
        print(f"Searching for: {target_name}...")
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

            print(f"Selected: {target_name}")

            # Poll for content appearance
            for _ in range(15):
                for f in page.frames:
                    try:
                        if await f.locator('div[data-tid="message-body"]').count() > 0:
                            return
                    except:
                        continue
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Error during search/selection: {e}")

    async def get_messages(self, target_name: Optional[str] = None, limit: int = 10) -> List[TeamsMessage]:
        """Extract recent chat messages."""
        if not self.context:
            raise RuntimeError("Client not initialized. Use 'async with TeamsClient() as client:'")

        page = self.context.pages[0]
        await self._navigate_and_wait(page)
        await self._switch_to_chat(page)

        if target_name:
            await self._search_and_select(page, target_name)

        print("Extracting messages...")
        messages = []
        for frame in page.frames:
            try:
                elements = await frame.locator('div[data-tid="chat-pane-item"]').all()
                if not elements:
                    continue

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

                if messages:
                    break
            except:
                continue

        return messages

    async def get_meeting_recap(self, target_name: str) -> List[TeamsMessage]:
        """Extract meeting recap/transcript from a Teams meeting chat."""
        if not self.context:
            raise RuntimeError("Client not initialized. Use 'async with TeamsClient() as client:'")

        page = self.context.pages[0]
        await self._navigate_and_wait(page)
        await self._switch_to_chat(page)
        await self._search_and_select(page, target_name)
        await asyncio.sleep(5)

        # Find and click "View recap"
        print("Looking for 'View recap' button...")
        try:
            recap_btn = page.locator('button:has-text("View recap")').last
            await recap_btn.click()
            print("Clicked 'View recap'. Waiting for hydration...")
            await asyncio.sleep(10)

            transcript_tab = page.locator(
                'button[role="tab"]:has-text("Transcript"), '
                'div[role="tab"]:has-text("Transcript")'
            ).first
            if await transcript_tab.count() > 0:
                await transcript_tab.click()
                print("Switched to Transcript tab.")
                await asyncio.sleep(5)

            # Extract transcript content
            print("Extracting transcript...")
            for frame in page.frames:
                try:
                    transcript_elements = await frame.evaluate("""() => {
                        let res = [];
                        let els = document.querySelectorAll(
                            'div[data-tid="transcript-item"], '
                            + 'div.ui-transcript__item, '
                            + 'div[role="listitem"]'
                        );
                        for (let el of els) {
                            if (el.innerText && el.innerText.length > 5) {
                                res.push(el.innerText.trim());
                            }
                        }
                        return res;
                    }""")

                    if transcript_elements:
                        print(f"Found {len(transcript_elements)} transcript segments.")
                        return [TeamsMessage(
                            author="Transcript",
                            body="\n".join(transcript_elements)
                        )]
                except:
                    continue

            # Fallback: grab whatever is in the main area
            main_text = await page.locator('div[data-tid="app-layout-area--main"]').inner_text()
            return [TeamsMessage(author="Recap Fallback", body=main_text)]

        except Exception as e:
            print(f"Failed to extract recap: {e}")
            return []


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Teams Headless Client")
    parser.add_argument("name", nargs="?", help="Chat or meeting name to search for")
    parser.add_argument("--recap", action="store_true", help="Extract meeting recap/transcript")
    parser.add_argument("--check-auth", action="store_true", help="Check if authenticated")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of messages")
    parser.add_argument("--show-ui", action="store_true", help="Show browser UI")
    args = parser.parse_args()

    async def main():
        async with TeamsClient(headless=not args.show_ui) as client:
            if args.check_auth:
                logged_in = await client.is_logged_in()
                status = {"authenticated": logged_in, "user_data": USER_DATA_DIR}
                print(json.dumps(status, indent=2))
                return

            if args.recap:
                if not args.name:
                    print("Error: Name required for recap.", file=sys.stderr)
                    sys.exit(1)
                results = await client.get_meeting_recap(args.name)
            else:
                results = await client.get_messages(args.name, args.limit)

            output = [r.model_dump() for r in results]
            print(json.dumps(output, indent=2, ensure_ascii=False))

    asyncio.run(main())
