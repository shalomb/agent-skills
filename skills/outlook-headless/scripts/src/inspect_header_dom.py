import asyncio
import os
from playwright.async_api import async_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = os.path.expanduser("~/.gemini/skills/outlook-headless/user_data")

async def run():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=True
        )
        page = context.pages[0]
        await page.goto("https://outlook.office.com/mail/deleteditems")
        await asyncio.sleep(5)
        
        items = page.locator('div[role="option"], div[role="row"]')
        if await items.count() > 0:
            await items.first.click()
            await asyncio.sleep(5)
            
            print("Running deep search for @...")
            
            # Find all elements anywhere on the page that mention an email
            matches = await page.evaluate("""() => {
                let results = [];
                let all = document.querySelectorAll('*');
                for (let el of all) {
                    let info = { tag: el.tagName, attrs: {} };
                    let found = false;
                    for (let attr of el.attributes) {
                        if (attr.value.includes('@')) {
                            info.attrs[attr.name] = attr.value;
                            found = true;
                        }
                    }
                    // Only check text nodes directly to avoid parent-bloat
                    for (let node of el.childNodes) {
                        if (node.nodeType === 3 && node.textContent.includes('@')) {
                            info.text = node.textContent.trim();
                            found = true;
                        }
                    }
                    if (found) results.push(info);
                }
                return results;
            }""")
            
            for m in matches:
                print(f"Match: {m}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
