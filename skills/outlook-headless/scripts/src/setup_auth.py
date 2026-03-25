import asyncio
import os
from playwright.async_api import async_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = os.path.expanduser("~/.gemini/skills/outlook-headless/user_data")

async def run():
    async with async_playwright() as p:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_PATH,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0]
        url = "https://outlook.office.com/mail/?login_hint=shalom.bhooshi%40takeda.com"
        await page.goto(url)
        
        print(f"Opening: {url}")
        print("Please log in to Outlook. Once you see your inbox, return here.")
        input("Press Enter here after you have logged in...")
        
        await context.close()
        print(f"Auth session saved to {USER_DATA_DIR}")

if __name__ == "__main__":
    asyncio.run(run())
