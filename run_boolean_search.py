import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Add current dir to path to import sourcing_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sourcing_agent

async def run_search(boolean_query: str, min_exp: int = 2, max_exp: int = 10):
    user_data_dir = sourcing_agent.PROFILE_DIR
    
    # Auto-heal stale lock
    lock_file = os.path.join(user_data_dir, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Cleared stale browser lock.")
        except Exception:
            pass

    exec_path = sourcing_agent.get_chromium_executable_path()
    headless_mode = sourcing_agent.is_headless_required()

    launch_args = ["--disable-http2", "--disable-blink-features=AutomationControlled"]
    if headless_mode:
        launch_args += ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
    else:
        launch_args.append("--start-maximized")

    print(f"Launching Chromium (headless={headless_mode}) at {user_data_dir}...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=exec_path,
            headless=headless_mode,
            viewport={"width": 1280, "height": 800} if headless_mode else None,
            ignore_https_errors=False,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=launch_args
        )

        page = context.pages[0] if context.pages else await context.new_page()

        try:
            print("Navigating to Naukri Resdex...")
            await page.goto("https://recruit.naukri.com", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            await page.goto("https://resdex.naukri.com", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            if "login" in page.url.lower():
                print("❌ Session expired — please log in via the web application first.")
                return

            # Auto-heal concurrent lock screen
            try:
                content = await page.content()
                if "Someone is already logged into Resdex" in content:
                    reset_btn = await page.wait_for_selector(
                        "button:has-text('Reset Subuser'), input[value*='Reset Subuser']", timeout=5000
                    )
                    if reset_btn:
                        print("Found concurrent login screen. Resetting subuser...")
                        await reset_btn.click()
                        await page.wait_for_timeout(10000)
            except Exception:
                pass

            # Ensure Boolean toggle is ON
            print("Turning ON Boolean search toggle...")
            await sourcing_agent.ensure_boolean_toggle_on(page)

            # Locate keywords input
            input_el = await page.wait_for_selector("input[name='ezKeywordsAny']", timeout=10000)
            if not input_el:
                print("❌ Could not find Boolean search input field.")
                return

            print(f"Entering Boolean Query: {boolean_query}")
            await input_el.focus()
            await input_el.fill("")
            await page.keyboard.type(boolean_query, delay=30)
            await page.wait_for_timeout(2000)

            # Set Experience limits
            print(f"Setting experience filter: Min={min_exp}, Max={max_exp}")
            min_input = await page.query_selector("input[name='minExp']")
            if min_input:
                await min_input.fill(str(min_exp))
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
            
            max_input = await page.query_selector("input[name='maxExp']")
            if max_input:
                await max_input.fill(str(max_exp))
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")

            # Click Search Button
            print("Submitting search...")
            try:
                await page.click("button:has-text('Search candidates'), button#adv-search-btn", timeout=5000)
            except Exception:
                await page.keyboard.press("Enter")
            
            print("Waiting for search results...")
            await page.wait_for_timeout(8000)

            # Parse results (names, key skills)
            print("\n" + "="*50)
            print("🔍 BOOLEAN SEARCH RESULTS (Page 1):")
            print("="*50)
            
            card_selectors = [".tuple", ".tuple-container", "[class*='tuple']", ".candidate-card"]
            cards = []
            for sel in card_selectors:
                cards = await page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                print("No candidates found or search page didn't load.")
                await page.screenshot(path="boolean_search_no_results.png")
                return

            for i, card in enumerate(cards[:15]):
                name = "Unknown"
                exp = "N/A"
                skills = "N/A"
                
                name_el = await card.query_selector(".name, [class*='name']")
                if name_el:
                    name = (await name_el.inner_text()).strip()
                
                exp_el = await card.query_selector(".exp, [class*='exp'], .experience")
                if exp_el:
                    exp = (await exp_el.inner_text()).strip()

                skills_el = await card.query_selector(".key-skills, .skills, [class*='skills']")
                if skills_el:
                    skills = (await skills_el.inner_text()).strip().replace("\n", " ")

                print(f"{i+1}. Name: {name} | Exp: {exp}")
                print(f"   Skills: {skills}")
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ Error running search: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        min_exp = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 2
        max_exp = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 10
        asyncio.run(run_search(query, min_exp, max_exp))
    else:
        query = input("Enter your Boolean query: ").strip()
        if not query:
            print("Query cannot be empty.")
            sys.exit(1)
        
        min_exp_str = input("Enter minimum experience (default 2): ").strip()
        max_exp_str = input("Enter maximum experience (default 10): ").strip()
        
        min_exp = int(min_exp_str) if min_exp_str.isdigit() else 2
        max_exp = int(max_exp_str) if max_exp_str.isdigit() else 10
        
        asyncio.run(run_search(query, min_exp, max_exp))
