import asyncio
import os
import sys
from playwright.async_api import async_playwright

try:
    from .outlook_client import CHROME_PATH, USER_DATA_DIR
except ImportError:
    # Standalone execution — replicate the path logic
    def _default_chrome_path() -> str:
        import platform
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
    USER_DATA_DIR = os.path.join(xdg_state, "agent-skills", "outlook-headless", "user_data")
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
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0]
        url = "https://outlook.office.com/mail/"
        await page.goto(url)

        print(f"Opened: {url}")
        print("Sign in to Outlook using SSO...")
        print("Waiting for inbox to load (up to 2 minutes)...")

        try:
            # Wait for inbox to load — look for mail list or nav element
            await page.wait_for_selector('[role="main"], [aria-label*="Mail"], .ms-List', timeout=120000)
            print("✓ Inbox detected!")
        except Exception as e:
            print(f"⚠ Timeout waiting for inbox: {e}")
            print("Proceeding anyway — session may still be valid...")

        await context.close()
        print(f"✓ Session saved to {USER_DATA_DIR}")

if __name__ == "__main__":
    asyncio.run(run())
