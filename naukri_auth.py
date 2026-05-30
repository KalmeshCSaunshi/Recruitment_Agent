import asyncio
from playwright.async_api import async_playwright

PROFILE_DIR = "./naukri_profile"

LOGIN_URL = (
    "https://www.naukri.com/recruit/login"
    "?msg=TO&URL=https%3A%2F%2Frecruit.naukri.com"
)

def get_chromium_executable_path():
    import os
    import sys
    env_path = os.environ.get("PLAYWRIGHT_CHROME_PATH") or os.environ.get("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    snap_path = "/snap/bin/chromium"
    if os.path.exists(snap_path):
        return snap_path
    if sys.platform.startswith("linux"):
        for path in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]:
            if os.path.exists(path):
                return path
    return None

async def save_auth():

    async with async_playwright() as p:
        
        exec_path = get_chromium_executable_path()

        context = await p.chromium.launch_persistent_context(

            user_data_dir=PROFILE_DIR,
            
            executable_path=exec_path,

            headless=False,

            viewport={"width": 1280, "height": 800},
            
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",

            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        print("Opening Naukri login page...")

        await page.goto(LOGIN_URL)

        print("\n" + "=" * 60)
        print("LOGIN MANUALLY")
        print("1. Enter Email")
        print("2. Enter Password")
        print("3. Complete OTP / CAPTCHA")
        print("4. Wait until dashboard fully loads")
        print("=" * 60)

        while True:

            current_url = page.url.lower()

            print(f"Current URL: {current_url}")

            if (
                "recruit.naukri.com" in current_url
                and "login" not in current_url
            ):

                print("\nLogin successful.")
                print("Saving persistent browser session...")

                # VERY IMPORTANT
                await page.wait_for_timeout(15000)

                break

            await asyncio.sleep(3)

        print("\nSession saved successfully.")
        print(f"Profile saved in: {PROFILE_DIR}")

        await context.close()


if __name__ == "__main__":

    asyncio.run(save_auth())