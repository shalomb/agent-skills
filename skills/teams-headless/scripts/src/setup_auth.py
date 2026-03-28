import asyncio
import os
import platform
from playwright.async_api import async_playwright

try:
    from .teams_client import CHROME_PATH, USER_DATA_DIR
except ImportError:
    def _default_chrome_path() -> str:
        env = os.environ.get("CHROME_PATH")
        if env:
            return env
        if platform.system() == "Darwin":
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        for p in ("/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"):
            if os.path.exists(p):
                return p
        return "google-chrome"

    xdg_state = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    USER_DATA_DIR = os.path.join(xdg_state, "agent-skills", "teams-headless", "user_data")
    CHROME_PATH = _default_chrome_path()

async def run():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    print(f"Chrome:    {CHROME_PATH}")
    print(f"User data: {USER_DATA_DIR}")
    print()
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
