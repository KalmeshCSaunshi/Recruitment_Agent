# import asyncio
# from playwright.async_api import async_playwright

# async def find_search_link():
#     async with async_playwright() as p:
#         browser = await p.firefox.launch(headless=False)
#         context = await browser.new_context(storage_state="naukri_auth.json")
#         page = await context.new_page()
        
#         try:
#             print("Navigating to Home...")
#             await page.goto("https://recruit.naukri.com/", wait_until="networkidle")
            
#             # Print all links that contain 'search' or 'resdex'
#             print("Scanning for search links...")
#             links = await page.query_selector_all("a")
#             for link in links:
#                 href = await link.get_attribute("href")
#                 text = await link.inner_text()
#                 if href and ("search" in href.lower() or "resdex" in href.lower()):
#                     print(f"Found Link: {text.strip()} -> {href}")
            
#             await page.wait_for_timeout(10000)
#         except Exception as e:
#             print(f"Error: {e}")
#         finally:
#             await browser.close()

# if __name__ == "__main__":
#     asyncio.run(find_search_link())





import asyncio
from playwright.async_api import async_playwright

async def find_search_link():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(storage_state="naukri_auth.json")
        page = await context.new_page()
        
        try:
            print("Navigating to Home...")
            await page.goto("https://recruit.naukri.com/", wait_until="networkidle")
            
            # Print all links that contain 'search' or 'resdex'
            print("Scanning for search links...")
            links = await page.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href and ("search" in href.lower() or "resdex" in href.lower()):
                    print(f"Found Link: {text.strip()} -> {href}")
            
            await page.wait_for_timeout(10000)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_search_link())