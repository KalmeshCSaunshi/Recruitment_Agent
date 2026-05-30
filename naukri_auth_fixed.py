# import asyncio
# import os
# from playwright.async_api import async_playwright

# PROFILE_DIR = "./naukri_profile"

# LOGIN_URL = "https://www.naukri.com/recruit/login"


# async def main():
#     async with async_playwright() as p:

#         try:
#             context = await p.chromium.launch_persistent_context(
#                 user_data_dir=PROFILE_DIR,
#                 headless=False,
#                 viewport={"width": 1366, "height": 768},
#                 args=[
#                     "--disable-blink-features=AutomationControlled",
#                     "--start-maximized"
#                 ]
#             )
#         except Exception as e:
#             if "XServer" in str(e) or "DISPLAY" in str(e):
#                 print("\n" + "!" * 60)
#                 print("ERROR: No display found! This server has no screen.")
#                 print("Please run this command instead:")
#                 print(f"xvfb-run python3 {os.path.basename(__file__)}")
#                 print("!" * 60 + "\n")
#             raise e

#         page = context.pages[0] if context.pages else await context.new_page()

#         # Anti-bot protections
#         await page.add_init_script("""
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined
#             });

#             window.chrome = {
#                 runtime: {}
#             };

#             Object.defineProperty(navigator, 'plugins', {
#                 get: () => [1, 2, 3, 4, 5]
#             });

#             Object.defineProperty(navigator, 'languages', {
#                 get: () => ['en-US', 'en']
#             });
#         """)

#         print("Opening Naukri Login Page...")

#         await page.goto(LOGIN_URL)

#         print("\n" + "=" * 60)
#         print("LOGIN MANUALLY")
#         print("1. Enter Email")
#         print("2. Enter Password")
#         print("3. Complete OTP / CAPTCHA")
#         print("4. Wait for dashboard")
#         print("=" * 60)

#         while True:
#             await asyncio.sleep(5)

#             current_url = page.url.lower()

#             print(f"Current URL: {current_url}")

#             if (
#                 "recruit.naukri.com" in current_url
#                 or "resdex.naukri.com" in current_url
#             ) and "login" not in current_url:

#                 print("\nLogin successful.")
#                 print("Session saved successfully.")
#                 break

#         input("\nPress ENTER to close browser...")

#         await context.close()


# if __name__ == "__main__":
#     asyncio.run(main())




# import asyncio
# from playwright.async_api import async_playwright
# import sys

# async def save_auth():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         context = await browser.new_context()
#         page = await context.new_page()
        
#         login_url = "https://www.naukri.com/recruit/login?msg=TO&URL=https%3A%2F%2Frecruit.naukri.com"
#         await page.goto(login_url)
        
#         print("\n" + "="*50)
#         print("1. Log in manually in the browser window.")
#         print("2. Once you are on the Resdex Dashboard, press ENTER here in the console.")
#         print("="*50 + "\n")
        
#         # Wait for user to press enter in the terminal
#         # Since we are running in a background command, we might need a different way.
#         # Let's try to detect the dashboard URL more broadly.
        
#         while True:
#             current_url = page.url
#             if "recruit.naukri.com" in current_url and "login" not in current_url:
#                 print(f"Logged in detected at: {current_url}")
#                 break
#             await asyncio.sleep(2)
        
#         print("Saving session...")
#         await asyncio.sleep(5)
#         await context.storage_state(path="naukri_auth.json")
#         print("Session saved successfully to naukri_auth.json")
#         await browser.close()

# if __name__ == "__main__":
#     asyncio.run(save_auth())




import asyncio
from playwright.async_api import async_playwright

PROFILE_DIR = "./naukri_profile"

LOGIN_URL = (
    "https://www.naukri.com/recruit/login"
    "?msg=TO&URL=https%3A%2F%2Frecruit.naukri.com"
)

async def save_auth():

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(

            user_data_dir=PROFILE_DIR,

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

        # Anti-bot protections to prevent Naukri from instantly refreshing/challenging the automated page
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

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
                ("recruit.naukri.com" in current_url or "resdex.naukri.com" in current_url)
                and "login" not in current_url
                and "resetlogin" not in current_url
            ):

                print("\nLogin successful.")
                print("Saving persistent browser session...")

                # VERY IMPORTANT
                await page.wait_for_timeout(10000)

                break

            await asyncio.sleep(3)

        print("\nSession saved successfully.")
        print(f"Profile saved in: {PROFILE_DIR}")

        await context.close()


if __name__ == "__main__":

    asyncio.run(save_auth())