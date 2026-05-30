import asyncio
from playwright.async_api import async_playwright
import json

async def run_search(query):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(storage_state="naukri_auth.json")
        page = await context.new_page()
        
        try:
            search_url = "https://resdex.naukri.com/v3"
            print(f"Navigating to {search_url}")
            await page.goto(search_url, wait_until="networkidle")
            
            await page.wait_for_timeout(5000)
            
            # 1. Turn on Boolean toggle if needed
            if "AND" in query or "OR" in query:
                print("Enabling Boolean search toggle...")
                try:
                    boolean_toggle = await page.wait_for_selector(".switch, [class*='toggle'], [class*='switch']", timeout=5000)
                    if boolean_toggle:
                        await boolean_toggle.click()
                        print("Boolean toggle clicked.")
                except:
                    print("Could not find Boolean toggle, proceeding...")

            # 2. Fill keywords
            print(f"Filling query: {query}")
            # The input identified before was Name=ezKeywordsAny
            await page.fill("input[name='ezKeywordsAny']", query)
            await page.keyboard.press("Enter")
            
            await page.wait_for_timeout(2000)
            
            # 3. Click the actual Search button at the bottom
            print("Clicking 'Search candidates' button...")
            search_btn = await page.query_selector("button:has-text('Search candidates'), .search-button, #search_btn")
            if search_btn:
                await search_btn.click()
            else:
                # Try clicking by coordinates or just press enter again
                await page.keyboard.press("Enter")
                
            print("Search submitted. Waiting for results page...")
            await page.wait_for_timeout(10000)
            await page.screenshot(path="resdex_v3_results_page.png")
            
            # 4. Extract candidates from results page
            results = []
            # In Resdex v3 results, names are usually in <a> tags with specific classes
            # We'll search for anything that looks like a name link
            names = await page.query_selector_all("a[class*='name'], span[class*='name'], .tuple .name")
            
            for i in range(min(10, len(names))):
                name_text = await names[i].inner_text()
                if name_text.strip():
                    results.append({"name": name_text.strip(), "link": await names[i].get_attribute("href")})
            
            return results

        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            print("Task finished. Window staying open for 30 seconds.")
            await page.wait_for_timeout(30000)
            await browser.close()

if __name__ == "__main__":
    q = "(React AND Node.js) AND (\"Full Stack\" OR \"Backend\")"
    leads = asyncio.run(run_search(q))
    print("\n--- CANDIDATES FOUND ---")
    print(json.dumps(leads, indent=2))
