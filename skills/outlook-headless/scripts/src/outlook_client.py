import asyncio
import os
import json
import re
import base64
from typing import List, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

try:
    from .models import EmailMessage, EmailSearchResult, SearchCriteria
    from .parser import OutlookParser
except ImportError:
    from models import EmailMessage, EmailSearchResult, SearchCriteria
    from parser import OutlookParser

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = os.path.expanduser("~/.gemini/skills/outlook-headless/user_data")
DOWNLOAD_DIR = os.path.expanduser("~/.gemini/skills/outlook-headless/downloads")

class OutlookClient:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.context: Optional[BrowserContext] = None
        self.p = None
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

    async def __aenter__(self):
        self.p = await async_playwright().start()
        self.context = await self.p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=self.headless,
            viewport={"width": 1280, "height": 1000}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.p:
            await self.p.stop()

    async def is_logged_in(self) -> bool:
        """Check if we are currently logged in by looking for inbox elements."""
        if not self.context:
            return False
        page = self.context.pages[0]
        try:
            # Try to go to a neutral internal page or just check current
            if page.url == "about:blank":
                await page.goto("https://outlook.office.com/mail/", wait_until="networkidle")
            
            # Look for a common element in the logged-in inbox
            # 'div[role="main"]' or the search box is usually a good sign
            await page.wait_for_selector('input[placeholder="Search"]', timeout=10000)
            return True
        except:
            return False

    async def search(self, criteria: SearchCriteria, limit: int = 5, list_only: bool = False, raw: bool = False, download_images: bool = False) -> List[EmailMessage]:
        if not self.context:
            raise RuntimeError("Client not initialized. Use 'async with OutlookClient() as client:'")

        page = self.context.pages[0]
        
        # Determine base URL based on folder
        url = "https://outlook.office.com/mail/"
        if criteria.folder:
            folder_map = {
                "Deleted Items": "deleteditems",
                "Sent Items": "sentitems",
                "Drafts": "drafts",
                "Junk Email": "junkemail",
                "Archive": "archive"
            }
            path = folder_map.get(criteria.folder, criteria.folder.lower().replace(" ", ""))
            url += path
            
        print(f"Navigating to: {url}")
        await page.goto(url)
        
        # Verify Auth
        if not await self.is_logged_in():
            print("ERROR: Not logged in. Please run 'uv run src/setup_auth.py' first.")
            return []

        # Trigger search if a query or specific filters (other than folder) are provided
        query = criteria.to_outlook_query()
        
        has_search_params = any([
            criteria.query, criteria.from_sender, criteria.to_recipient, 
            criteria.subject, criteria.after, criteria.before, 
            criteria.unread_only, criteria.importance
        ])

        if has_search_params:
            print(f"Searching for: {query}")
            await page.keyboard.press("Alt+Q")
            await asyncio.sleep(1) 
            
            search_input = page.get_by_placeholder("Search")
            if not await search_input.is_visible():
                search_input = page.locator('input[placeholder="Search"]')
                await search_input.click()

            await search_input.fill(query)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3) 

        # Results are usually in div[role="option"] or div[role="row"] depending on view
        results = []
        seen_identifiers = set()

        async def extract_item_data(item):
            item_text = await item.inner_text()
            lines = [l.strip() for l in item_text.split("\n") if l.strip()]
            if not lines: return None
            
            # Use specific identifiers if available, or heuristic
            list_sender = lines[0]
            list_subject = lines[1] if len(lines) > 1 else "No Subject"
            snippet = lines[2] if len(lines) > 2 else ""
            
            identifier = f"{list_sender}|{list_subject}|{snippet[:20]}"
            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                return EmailMessage(
                    id=f"list-{len(results)}",
                    subject=list_subject,
                    sender=list_sender,
                    body=f"[Snippet] {snippet}"
                ), (item, list_sender, list_subject, snippet)
            return None

        print(f"Collecting up to {limit} items via ArrowDown iteration...")
        
        # Ensure the list is visible and clickable
        await page.wait_for_selector('div[role="option"], div[role="row"], div[data-convid]', timeout=20000)
        
        # Focus the list by clicking a visible item
        items = page.locator('div[role="option"], div[role="row"], div[data-convid]')
        found_items = await items.count()
        if found_items > 0:
            # Click the first one to establish focus
            try:
                await items.first.click(timeout=5000)
            except:
                # If click fails, try to focus it
                await items.first.focus()
            await asyncio.sleep(1.0)
        else:
            print("No items found to iterate.")
            return []

        # Iterative collection using a Scroll-Wait-Collect loop
        print(f"Collecting up to {limit} items...")
        
        # Find the scrollable container for the message list
        # Usually it's the parent of the items with an overflow
        scroll_container_selector = 'div[role="main"] div[aria-label="Message list"]'
        
        results = []
        seen_identifiers = set()
        consecutive_no_new = 0
        
        while len(results) < limit and consecutive_no_new < 10:
            # 1. Collect currently visible items
            current_items = page.locator('div[role="option"], div[role="row"], div[data-convid]')
            item_count = await current_items.count()
            new_in_this_pass = 0
            
            for i in range(item_count):
                try:
                    item = current_items.nth(i)
                    item_text = await item.inner_text()
                    if not item_text.strip(): continue
                    
                    # Deep Search on the list item itself for persistent email metadata
                    item_emails = await item.evaluate("""el => {
                        let emails = new Set();
                        let re = /[\\w\\.-]+@[\\w\\.-]+\\.\\w+/g;
                        for (let attr of el.attributes) {
                            let matches = attr.value.match(re);
                            if (matches) matches.forEach(m => emails.add(m));
                        }
                        let all = el.querySelectorAll('*');
                        for (let child of all) {
                            for (let attr of child.attributes) {
                                let matches = attr.value.match(re);
                                if (matches) matches.forEach(m => emails.add(m));
                            }
                        }
                        return Array.from(emails);
                    }""")
                    
                    # Check for unread status
                    aria_label = await item.get_attribute("aria-label")
                    is_read = True
                    if aria_label and aria_label.lower().startswith("unread"):
                        is_read = False
                    
                    msg = OutlookParser.parse_list_item(item_text, len(results), is_read=is_read)
                    if not msg: continue
                    
                    # If we found an email in the list item, it's very likely the sender's
                    if item_emails:
                        msg.sender = item_emails[0]
                    
                    identifier = f"{msg.sender}|{msg.subject}|{msg.body[:30]}"
                    if identifier not in seen_identifiers:
                        seen_identifiers.add(identifier)
                        new_in_this_pass += 1
                        
                        if list_only:
                            results.append(msg)
                        else:
                            # For full extraction, we need the locator and the parsed headers
                            results.append((item, msg))
                            
                        if len(results) >= limit:
                            break
                except:
                    continue
            
            if new_in_this_pass > 0:
                consecutive_no_new = 0
                print(f"Progress: {len(results)} items collected...")
            else:
                consecutive_no_new += 1

            # 2. Scroll to trigger pagination
            # We scroll to the bottom of the current list
            try:
                # Use JS to scroll the container if possible
                container = page.locator(scroll_container_selector).first
                if await container.count() > 0:
                    await container.evaluate("el => el.scrollTop += 1000")
                else:
                    # Fallback to general page down
                    await page.keyboard.press("PageDown")
            except:
                await page.keyboard.press("PageDown")
                
            # 3. Wait for hydration/network
            await asyncio.sleep(1.5)

        print(f"Final collection count: {len(results)}")
        if list_only:
            return results

        # For non-list-only, we now have a list of (locator, msg_with_headers)
        final_results = []
        for i, (item, list_msg) in enumerate(results):
            try:
                await item.click()
                await asyncio.sleep(2.0) # More time for full load

                # 1. Targeted Header Extraction
                # Outlook often puts headers in a specific area
                header_area = page.locator('div[role="main"] div[aria-label="Message header"], div[role="main"] div[role="group"]')
                
                extracted_sender = list_msg.sender
                extracted_subject = list_msg.subject
                extracted_to = []
                extracted_cc = []
                extracted_ts = list_msg.timestamp

                try:
                    # 1. Subject
                    subject_el = page.locator('div[role="main"] div[role="heading"][aria-level="2"]').first
                    if await subject_el.count() > 0:
                        extracted_subject = await subject_el.inner_text()

                    # 2. Deep Search for Emails in the Reading Pane
                    # This script finds all unique strings that look like emails in any attribute or text node
                    # specifically in the header/reading pane area.
                    pane_emails = await page.evaluate("""() => {
                        let emails = new Set();
                        let re = /[\\w\\.-]+@[\\w\\.-]+\\.\\w+/g;
                        
                        // Look specifically in the reading pane area
                        let pane = document.querySelector('div[role="main"]');
                        if (!pane) return [];
                        
                        let all = pane.querySelectorAll('*');
                        for (let el of all) {
                            // Check all attributes
                            for (let attr of el.attributes) {
                                let matches = attr.value.match(re);
                                if (matches) matches.forEach(m => emails.add(m));
                            }
                            // Check text nodes directly
                            for (let node of el.childNodes) {
                                if (node.nodeType === 3) {
                                    let matches = node.textContent.match(re);
                                    if (matches) matches.forEach(m => emails.add(m));
                                }
                            }
                        }
                        return Array.from(emails);
                    }""")
                    
                    if pane_emails:
                        # Heuristic: First email is usually the sender
                        extracted_sender = pane_emails[0]
                        # Others are likely recipients
                        if len(pane_emails) > 1:
                            extracted_to = pane_emails[1:]
                except Exception as e:
                    print(f"Non-critical deep header extraction failure for item {i}: {e}")

                # 2. Extract Document Body
                # First, attempt to expand all collapsed messages in the thread
                try:
                    # Look for anything that might be a collapsed message or "show all" INSIDE the reading pane
                    reading_pane = page.locator('div[role="main"]')
                    expand_selectors = [
                        'div[aria-expanded="false"]',
                        'div[aria-label*="messages"]', # e.g. "9 messages"
                        'button:has-text("Show more")',
                        'button:has-text("Show all")'
                    ]
                    for selector in expand_selectors:
                        buttons = reading_pane.locator(selector)
                        count = await buttons.count()
                        print(f"DEBUG: Found {count} expansion candidates for selector {selector} in reading pane")
                        for j in range(count):
                            try:
                                btn = buttons.nth(j)
                                label = (await btn.get_attribute("aria-label") or "").lower()
                                text = (await btn.inner_text() or "").lower()
                                
                                if "reaction" in label or "like" in label:
                                    continue
                                    
                                if await btn.is_visible():
                                    print(f"DEBUG: Clicking expansion candidate: label={label[:20]}, text={text[:20]}")
                                    await btn.click()
                                    await asyncio.sleep(0.5)
                            except: continue
                    
                    # Wait for expansion
                    await asyncio.sleep(2.0)
                except Exception as e:
                    print(f"Non-critical expansion failure: {e}")

                if raw:
                    # Quick Raw Dump mode: extract all text from the reading pane in one go
                    pane = page.locator('div[role="main"]')
                    raw_text = await pane.inner_text()
                    final_results.append(EmailMessage(
                        id=f"raw-{i}",
                        subject=extracted_subject,
                        sender="Conversation Thread",
                        body=raw_text
                    ))
                    continue

                # Now extract all messages
                documents = page.locator('div[role="document"]')
                doc_count = await documents.count()
                print(f"DEBUG: Found {doc_count} documents in reading pane")
                
                if doc_count == 0:
                    # Try a broader selector if doc_count is 0
                    documents = page.locator('div[aria-label="Message body"]')
                    doc_count = await documents.count()
                    print(f"DEBUG: Found {doc_count} documents with fallback selector")

                if doc_count == 0:
                    final_results.append(list_msg)
                    continue

                for j in range(doc_count):
                    doc = documents.nth(j)
                    await doc.scroll_into_view_if_needed()
                    doc_html = await doc.inner_html()
                    
                    # Try to find headers specifically for THIS document
                    # Headers are usually in a sibling or parent div
                    # We look for "From: ", "To: ", "Mon 3/23..." etc in the vicinity
                    
                    current_sender = extracted_sender
                    current_ts = extracted_ts
                    current_to = []
                    
                    try:
                        # Search "up" from the document to find its header container
                        # In Outlook, headers and bodies are often siblings inside a common parent
                        header_info = await doc.evaluate("""doc => {
                            let parent = doc.parentElement;
                            while (parent && parent.getAttribute('role') !== 'main') {
                                // Look for buttons or spans with "From:" or sender names
                                let fromBtn = parent.querySelector('button[aria-label^="From:"], span[aria-label^="From:"]');
                                
                                // Find any div/span that looks like a date/timestamp
                                let tsEl = null;
                                let headings = parent.querySelectorAll('div[role="heading"], span');
                                for (let h of headings) {
                                    if (h.innerText.includes('/') && (h.innerText.includes('AM') || h.innerText.includes('PM'))) {
                                        tsEl = h;
                                        break;
                                    }
                                }
                                
                                if (fromBtn || tsEl) {
                                    return {
                                        sender: fromBtn ? fromBtn.getAttribute('aria-label').replace('From: ', '') : null,
                                        timestamp: tsEl ? tsEl.innerText : null
                                    };
                                }
                                parent = parent.parentElement;
                            }
                            return null;
                        }""")
                        
                        if header_info:
                            if header_info['sender']: current_sender = header_info['sender']
                            if header_info['timestamp']: current_ts = header_info['timestamp']
                    except: pass

                    # Use parser for document with HTML
                    full_msg = OutlookParser.parse_document(
                        doc_html=doc_html, 
                        message_id=f"{i}-{j}",
                        sender=current_sender,
                        subject=extracted_subject,
                        timestamp=current_ts,
                        to=extracted_to,
                        cc=extracted_cc
                    )

                    # Optional Image Download
                    if download_images and full_msg.images:
                        for idx, img in enumerate(full_msg.images):
                            if not img.src: continue
                            
                            try:
                                # Convert blob or external src to local file
                                b64_data = await page.evaluate("""async (src) => {
                                    try {
                                        const response = await fetch(src);
                                        const blob = await response.blob();
                                        return new Promise((resolve) => {
                                            const reader = new FileReader();
                                            reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                            reader.readAsDataURL(blob);
                                        });
                                    } catch (e) { return null; }
                                }""", img.src)
                                
                                if b64_data:
                                    filename = f"img_{full_msg.id.replace('-', '_')}_{idx}.png"
                                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(base64.b64decode(b64_data))
                                    img.local_path = filepath
                                    print(f"Downloaded image to: {filepath}")
                            except Exception as e:
                                print(f"Failed to download image {idx}: {e}")

                    final_results.append(full_msg)
                    
                    if len(final_results) >= limit:
                        break
            except Exception as e:
                print(f"Failed to extract item {i}: {e}")
                list_msg.body += f" [Error during full extract: {e}]"
                final_results.append(list_msg)
            
            if len(final_results) >= limit:
                break
                
        return final_results
                
        return results

async def quick_search(query: str, limit: int = 5):
    criteria = SearchCriteria(query=query)
    async with OutlookClient(headless=True) as client:
        return await client.search(criteria, limit=limit)
