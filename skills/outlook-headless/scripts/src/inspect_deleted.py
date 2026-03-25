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
            headless=False,
            viewport={"width": 1280, "height": 900}
        )
        page = context.pages[0]
        url = "https://outlook.office.com/mail/deleteditems"
        await page.goto(url)
        print(f"Opened: {url}")
        print("Chrome is open for inspection. Close the browser or press Enter here to finish.")
        input("Press Enter to close and return...")
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
