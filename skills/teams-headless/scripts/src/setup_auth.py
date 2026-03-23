import asyncio
import os
from playwright.async_api import async_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = os.path.expanduser("~/.gemini/skills/teams-headless/user_data")

async def run():
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
        print("Please log in. Once you see your Teams chat list, return here.")
        input("Press Enter here after you have fully logged in...")
        await context.close()
        print(f"Auth session saved to {USER_DATA_DIR}")

if __name__ == "__main__":
    asyncio.run(run())
