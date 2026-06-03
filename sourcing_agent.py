
import requests
import json
import urllib.parse
import asyncio
from playwright.async_api import async_playwright
import re
import os

PROFILE_DIR = "./naukri_profile"

OLLAMA_API_URL = 'http://10.153.204.33:11434/api/generate'
MODEL_NAME = 'llama3:latest'

def resolve_ollama_config():
    import requests
    # Try localhost first
    try:
        r = requests.get("http://10.153.204.33:11434/api/tags", timeout=1.5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            for preferred in ["gemma4:e4b", "qwen2.5-coder:14b", "llama3:latest"]:
                if preferred in models:
                    return "http://10.153.204.33:11434/api/generate", preferred
            if models:
                return "http://10.153.204.33:11434/api/generate", models[0]
    except Exception:
        pass

 
    # Try remote IP next
    try:
        r = requests.get("http://10.153.204.33:11434/api/tags", timeout=1.5)
        if r.status_code == 200:
            return "http://10.153.204.33:11434/api/generate", "llama3:latest"
    except Exception:
        pass

    # Default fallback
    return "http://10.153.204.33:11434/api/generate", "gemma4:e4b"

OLLAMA_API_URL, MODEL_NAME = resolve_ollama_config()
print(f"DEBUG: Resolved Ollama config to {OLLAMA_API_URL} with model {MODEL_NAME}", flush=True)

def is_candidate_active_in_30_days(active_text):
    if not active_text:
        return True # Default to true if not specified
    
    text = active_text.lower().strip()
    
    # Positive matches for active in last 30 days / 1 month
    if any(x in text for x in ["today", "yesterday", "day ago", "days ago", "7 days", "15 days", "30 days", "1 month"]):
        # Check if it specifies a number of days or months
        # e.g., "active 45 days ago"
        match_days = re.search(r'(\d+)\s+days\s+ago', text)
        if match_days:
            days = int(match_days.group(1))
            return days <= 30
            
        match_months = re.search(r'(\d+)\s+month(s)?\s+ago', text)
        if match_months:
            months = int(match_months.group(1))
            return months <= 1
            
        return True
        
    # If it says "active in last 3 months", "active in last 6 months", "active 2 months ago"
    if any(x in text for x in ["month", "months", "year", "years"]):
        # If it contains "1 month" it's ok, but others like "2 months", "3 months" are invalid
        match_months_last = re.search(r'last\s+(\d+)\s+month', text)
        if match_months_last:
            months = int(match_months_last.group(1))
            return months <= 1
            
        return False
        
    return True # Fallback to True to not miss candidates if layout changes slightly

def is_notice_period_within_30_days(np_text):
    if not np_text or np_text.strip() == "" or np_text == "N/A":
        return True # Default to true if not specified
    
    text = np_text.lower().strip()
    
    # Immediate or serving notice are always <= 30 days
    if any(x in text for x in ["immediate", "serving", "serve"]):
        return True
        
    # Check for days
    match_days = re.search(r'(\d+)\s+day', text)
    if match_days:
        days = int(match_days.group(1))
        return days <= 30
        
    # Check for months
    match_months = re.search(r'(\d+)\s+month', text)
    if match_months:
        months = int(match_months.group(1))
        return months <= 1
        
    # If it says "1 month"
    if "1 month" in text or "one month" in text:
        return True
        
    # If it mentions longer notice periods explicitly
    if any(x in text for x in ["45 days", "60 days", "90 days", "2 month", "3 month", "two month", "three month"]):
        return False
        
    return True # Default to true for safety

def extract_notice_period_from_card_text(card_txt):
    if not card_txt:
        return "N/A"
    
    import re
    raw_lines = [line.strip() for line in card_txt.split("\n") if line.strip()]
    
    # Process pipes: if any line contains pipes, split them into sub-lines
    lines = []
    for line in raw_lines:
        if "|" in line:
            lines.extend([p.strip() for p in line.split("|") if p.strip()])
        else:
            lines.append(line)
    
    # 1. Look for explicit notice period indicators
    for line in lines:
        line_lower = line.lower()
        if "notice period" in line_lower:
            return line
            
    # 2. Look for standalone/badge lines matching typical notice period formats
    for line in lines:
        line_lower = line.lower()
        if line_lower in ["immediate", "immediate joiner", "serving notice", "serving notice period", "serving np"]:
            return line
            
        if len(line) < 25:
            if re.match(r'^\d+\s*month(s)?$', line, re.IGNORECASE):
                return line
            if re.match(r'^\d+\s*day(s)?$', line, re.IGNORECASE):
                return line
                
    return "N/A"

async def ensure_boolean_toggle_on(page):
    print("📊 Ensuring Boolean toggle is turned ON...", flush=True)
    try:
        # 1. First, check the actual checkbox state (ground truth)
        cb = await page.query_selector("input[name='toggleSwitch']")
        if cb:
            is_checked = await cb.is_checked()
            if is_checked:
                print("📊 Boolean toggle is ALREADY ON (verified via checkbox state).", flush=True)
                return True
            else:
                print("📊 Boolean toggle is OFF (verified via checkbox state). Clicking toggle...", flush=True)
                # Click the parent label or the wrapper to toggle state
                parent = await page.query_selector(".toggle-switch-wrap, label.ts-switch, label.boolean-toggle")
                if parent:
                    await parent.click()
                    await page.wait_for_timeout(2000)
                    return True

        # 2. Fallback: check if the toggle label class explicitly indicates it's OFF
        off_toggle = await page.query_selector("label.boolean-toggle.off, label.ts-switch.off")
        if off_toggle:
            print("📊 Boolean toggle is currently OFF. Clicking to turn it ON...", flush=True)
            await off_toggle.click()
            await page.wait_for_timeout(2000)
            return True
            
        # 3. Fallback: check if it's already ON by class
        on_toggle = await page.query_selector("label.boolean-toggle.on, label.ts-switch.on")
        if on_toggle:
            print("📊 Boolean toggle is ALREADY ON. No click needed.", flush=True)
            return True
            
        # 4. Fallback: check by text label
        lbl = await page.query_selector(".toggle-switch-label")
        if lbl:
            txt = (await lbl.inner_text()).lower()
            if "boolean off" in txt:
                print("📊 Boolean toggle is OFF (by text label). Clicking wrapper...", flush=True)
                # Try clicking wrapper or label
                parent = await page.query_selector(".toggle-switch-wrap, label.ts-switch, label.boolean-toggle") or lbl
                await parent.click()
                await page.wait_for_timeout(2000)
                return True
            elif "boolean on" in txt:
                print("📊 Boolean toggle is ALREADY ON (by text label).", flush=True)
                return True
    except Exception as e:
        print(f"📊 Error ensuring Boolean toggle is ON: {e}", flush=True)
    return False

async def ensure_boolean_toggle_off(page):
    print("📊 Ensuring Boolean toggle is turned OFF...", flush=True)
    try:
        # 1. First, check the actual checkbox state (ground truth)
        cb = await page.query_selector("input[name='toggleSwitch']")
        if cb:
            is_checked = await cb.is_checked()
            if not is_checked:
                print("📊 Boolean toggle is ALREADY OFF (verified via checkbox state).", flush=True)
                return True
            else:
                print("📊 Boolean toggle is ON (verified via checkbox state). Clicking toggle to turn OFF...", flush=True)
                # Click the parent label or the wrapper to toggle state
                parent = await page.query_selector(".toggle-switch-wrap, label.ts-switch, label.boolean-toggle")
                if parent:
                    await parent.click()
                    await page.wait_for_timeout(2000)
                    return True

        # 2. Fallback: check if the toggle label class explicitly indicates it's ON
        on_toggle = await page.query_selector("label.boolean-toggle.on, label.ts-switch.on")
        if on_toggle:
            print("📊 Boolean toggle is currently ON. Clicking to turn it OFF...", flush=True)
            await on_toggle.click()
            await page.wait_for_timeout(2000)
            return True
            
        # 3. Fallback: check if it's already OFF by class
        off_toggle = await page.query_selector("label.boolean-toggle.off, label.ts-switch.off")
        if off_toggle:
            print("📊 Boolean toggle is ALREADY OFF. No click needed.", flush=True)
            return True
            
        # 4. Fallback: check by text label
        lbl = await page.query_selector(".toggle-switch-label")
        if lbl:
            txt = (await lbl.inner_text()).lower()
            if "boolean on" in txt:
                print("📊 Boolean toggle is ON (by text label). Clicking wrapper to turn OFF...", flush=True)
                parent = await page.query_selector(".toggle-switch-wrap, label.ts-switch, label.boolean-toggle") or lbl
                await parent.click()
                await page.wait_for_timeout(2000)
                return True
            elif "boolean off" in txt:
                print("📊 Boolean toggle is ALREADY OFF (by text label).", flush=True)
                return True
    except Exception as e:
        print(f"📊 Error ensuring Boolean toggle is OFF: {e}", flush=True)
    return False

async def market_scan_search(query, min_exp=2, max_exp=10, max_pages=5, profile_path=None):
    """
    Fast market scan — reads card data across multiple pages WITHOUT opening profiles.
    Uses the SAME UI flow as perform_authenticated_search (persistent context + boolean toggle).
    Returns ALL candidates found for Excel export.
    """
    user_data_dir = profile_path or PROFILE_DIR
    all_candidates = []

    # Parse query parameter (could be dictionary of separate keywords or string)
    mandatory_skills = []
    optional_skills = []
    if isinstance(query, dict):
        mandatory_val = query.get('mandatory_skills') or query.get('mandatory_keywords') or []
        optional_val = query.get('optional_skills') or query.get('optional_keywords') or []
        
        if isinstance(mandatory_val, list):
            mandatory_skills = mandatory_val
        else:
            mandatory_skills = [s.strip() for s in str(mandatory_val).split(",") if s.strip()]
            
        if isinstance(optional_val, list):
            optional_skills = optional_val
        else:
            optional_skills = [s.strip() for s in str(optional_val).split(",") if s.strip()]
    else:
        # If it's a string, treat it as a single mandatory skill
        mandatory_skills = [s.strip() for s in str(query).split(",") if s.strip()]

    async with async_playwright() as p:
        # Auto-heal stale lock file
        lock_file = os.path.join(user_data_dir, "SingletonLock")
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print("Market scan: Cleared stale browser lock.", flush=True)
            except Exception:
                pass

        exec_path = get_chromium_executable_path()
        headless_mode = is_headless_required()

        launch_args = ["--disable-http2", "--disable-blink-features=AutomationControlled"]
        if headless_mode:
            launch_args += ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        else:
            launch_args.append("--start-maximized")

        print(f"📊 Market scan: Launching Chromium (headless={headless_mode}) at {user_data_dir}...", flush=True)
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
            # Step 1: Navigate to Resdex (same as main sourcing agent)
            await page.goto("https://recruit.naukri.com", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            await page.goto("https://resdex.naukri.com", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            if "login" in page.url.lower():
                print("📊 Market scan: Session expired — redirected to login.", flush=True)
                return []

            # Auto-heal concurrent lock screen
            try:
                content = await page.content()
                if "Someone is already logged into Resdex" in content:
                    reset_btn = await page.wait_for_selector(
                        "button:has-text('Reset Subuser'), input[value*='Reset Subuser']", timeout=5000
                    )
                    if reset_btn:
                        await reset_btn.click()
                        await page.wait_for_timeout(10000)
            except Exception:
                pass

            # Step 2: Ensure Boolean toggle is OFF
            await ensure_boolean_toggle_off(page)

            # Step 3: Enter keywords as chips/tags
            # Helper to find current active keywords input
            async def get_active_keywords_input():
                for selector in [
                    "input[name='ezKeywordsAny']", 
                    "input[placeholder*='skills']", 
                    "input[placeholder*='Skills']", 
                    "[class*='keyword-input'] input", 
                    "textarea"
                ]:
                    try:
                        el = await page.wait_for_selector(selector, timeout=2000)
                        if el and await el.is_visible():
                            return el
                    except Exception:
                        pass
                return None

            # Type and add all mandatory skills
            for skill in mandatory_skills:
                try:
                    el = await get_active_keywords_input()
                    if not el:
                        print(f"Warning: Could not locate keywords input to enter mandatory skill: {skill}")
                        continue
                    
                    print(f"Adding mandatory skill: {skill}", flush=True)
                    await el.focus()
                    await el.fill("")
                    await page.keyboard.type(skill, delay=50)
                    await page.wait_for_timeout(1000)
                    
                    dropdown_item = await page.query_selector(
                        ".autocomplete-suggestion, [class*='suggestion'] div, #suggestor-listbox [role='option'], .suggestor-wrapper [role='option'], [id*='listbox'] [role='option'], [class*='listbox'] [role='option'], .suggestor-box + div [role='option']"
                    )
                    if dropdown_item:
                        await dropdown_item.click()
                    else:
                        await page.keyboard.press("Enter")
                    await page.wait_for_timeout(3000)
                except Exception as skill_err:
                    print(f"Could not enter mandatory skill '{skill}': {skill_err}", flush=True)

            # Type and add all optional skills
            for skill in optional_skills:
                try:
                    el = await get_active_keywords_input()
                    if not el:
                        print(f"Warning: Could not locate keywords input to enter optional skill: {skill}")
                        continue
                    
                    print(f"Adding optional skill: {skill}", flush=True)
                    await el.focus()
                    await el.fill("")
                    await page.keyboard.type(skill, delay=50)
                    await page.wait_for_timeout(1000)
                    
                    dropdown_item = await page.query_selector(
                        ".autocomplete-suggestion, [class*='suggestion'] div, #suggestor-listbox [role='option'], .suggestor-wrapper [role='option'], [id*='listbox'] [role='option'], [class*='listbox'] [role='option'], .suggestor-box + div [role='option']"
                    )
                    if dropdown_item:
                        await dropdown_item.click()
                    else:
                        await page.keyboard.press("Enter")
                    await page.wait_for_timeout(500)
                except Exception as skill_err:
                    print(f"Could not enter optional skill '{skill}': {skill_err}", flush=True)

            # Mark Mandatory Skills as Starred (Only the 2nd mandatory skill needs to be manually starred, since the 1st is starred by default)
            if len(mandatory_skills) > 1:
                skill_to_star = mandatory_skills[1]
                try:
                    tag = await page.wait_for_selector(
                        f"button.star-tag-wrapper:has-text('{skill_to_star}'), button[aria-label='{skill_to_star}'], .tag-label:has-text('{skill_to_star}'), span:has-text('{skill_to_star}'), .tag:has-text('{skill_to_star}')", 
                        timeout=3000
                    )
                    if tag:
                        star_btn = await tag.query_selector("i.star, .star, .star-icon, [class*='star']")
                        click_target = star_btn if star_btn else tag
                        await click_target.click()
                        print(f"Starred mandatory skill (2nd skill): {skill_to_star}", flush=True)
                        await page.wait_for_timeout(500)
                except Exception as star_err:
                    print(f"Could not star mandatory skill {skill_to_star}: {star_err}", flush=True)

            # Step 4: Set experience filter
            try:
                min_field = await page.wait_for_selector("input[placeholder*='Min'], #minExp, [name='minExp']", timeout=5000)
                if min_field:
                    await min_field.fill(str(min_exp))
                max_field = await page.wait_for_selector("input[placeholder*='Max'], #maxExp, [name='maxExp']", timeout=5000)
                if max_field:
                    await max_field.fill(str(max_exp))
                print(f"📊 Market scan: Exp filter set: {min_exp}-{max_exp}y", flush=True)
            except Exception:
                print("📊 Market scan: Could not set experience filter.", flush=True)

            # Step 5: Click Search
            search_btn = await page.query_selector("button:has-text('Search candidates')")
            if search_btn:
                await search_btn.click()
            else:
                await page.keyboard.press("Enter")

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(8000)
            print("📊 Market scan: Search submitted, waiting for results...", flush=True)

            # Step 6: Scrape cards page by page using Next button
            for page_num in range(1, max_pages + 1):
                print(f"📊 Market scan: Scraping page {page_num}/{max_pages}...", flush=True)

                card_selectors = [".tuple", ".tuple-container", "[class*='tuple']", ".candidate-card"]
                cards = []
                for sel in card_selectors:
                    cards = await page.query_selector_all(sel)
                    if cards:
                        break

                if not cards:
                    print(f"📊 Market scan: No cards on page {page_num}. Stopping.", flush=True)
                    break

                print(f"📊 Market scan: Found {len(cards)} cards on page {page_num}.", flush=True)

                for card in cards:
                    try:
                        name_el = await card.query_selector(".name, .title, [class*='name']")
                        name = (await name_el.inner_text()).strip() if name_el else ""
                        if not name:
                            continue

                        # Experience — try selector first, fallback to regex on full card text
                        exp_el = await card.query_selector(".exp, [class*='exp'], [class*='experience'], .info-item")
                        exp = (await exp_el.inner_text()).strip() if exp_el else ""
                        if not exp or exp == "N/A" or not any(c.isdigit() for c in exp):
                            card_txt_for_exp = await card.inner_text()
                            import re as _re
                            m = _re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', card_txt_for_exp, _re.IGNORECASE)
                            exp = m.group(0).strip() if m else "N/A"

                        current_el = await card.query_selector(".current, .designation, [class*='current']")
                        current = (await current_el.inner_text()).strip() if current_el else "N/A"

                        loc_el = await card.query_selector(".loc, [class*='loc'], [class*='location']")
                        location = (await loc_el.inner_text()).strip() if loc_el else "N/A"

                        # Notice period — robust card text extraction using helper
                        notice = "N/A"
                        try:
                            card_full = await card.inner_text()
                            notice = extract_notice_period_from_card_text(card_full)
                        except Exception:
                            pass


                        active_el = await card.query_selector(".active-date-info, [class*='active-date']")
                        active_text = (await active_el.inner_text()).strip() if active_el else ""
                        if not active_text:
                            card_txt = await card.inner_text()
                            for line in card_txt.split("\n"):
                                if "active" in line.lower():
                                    active_text = line.strip()
                                    break
                        is_active_30 = is_candidate_active_in_30_days(active_text) if active_text else None
                        active_display = "✅ Active (30d)" if is_active_30 else ("❌ Inactive" if active_text else "Unknown")

                        skills_el = await card.query_selector(".key-skills, [class*='skill']")
                        skills = (await skills_el.inner_text()).strip() if skills_el else "N/A"

                        link_el = await card.query_selector("a[href*='profile'], .name a, a[href*='preview']")
                        link = await link_el.get_attribute("href") if link_el else None
                        if link and not link.startswith("http"):
                            link = "https://resdex.naukri.com" + link

                        all_candidates.append({
                            "name": name,
                            "experience": exp,
                            "current": current,
                            "location": location,
                            "notice_period": notice,
                            "active_status": active_display,
                            "is_active_30d": is_active_30,
                            "skills": skills,
                            "email": "Hidden (unlock in Resdex)",
                            "profile_link": link or ""
                        })
                    except Exception:
                        continue

                print(f"📊 Market scan: Running total = {len(all_candidates)} candidates.", flush=True)

                # Go to next page if not last
                if page_num < max_pages:
                    try:
                        next_btn = await page.query_selector(
                            "[data-testid='next-page'], button[data-testid='next-page'], "
                            "button:has-text('Next'), a:has-text('Next'), [aria-label='Next'], "
                            ".ico-expand.next"
                        )
                        if next_btn:
                            # Scroll next button into view if needed
                            try:
                                await next_btn.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            try:
                                await next_btn.click(timeout=3000)
                            except Exception:
                                await next_btn.evaluate("el => el.click()")
                            await page.wait_for_timeout(5000)
                        else:
                            print("📊 Market scan: No Next button found. Reached last page.", flush=True)
                            break
                    except Exception as nav_err:
                        print(f"📊 Market scan: Pagination error: {nav_err}", flush=True)
                        break

        except Exception as e:
            print(f"📊 Market scan error: {e}", flush=True)
        finally:
            await context.close()

    print(f"📊 Market scan complete. Total candidates collected: {len(all_candidates)}", flush=True)
    return all_candidates


def deterministic_keywords_fallback(jd, for_market_analysis=False):
    import re
    # Simple regex extraction to grab key terms from the JD
    words = re.findall(r'\b[A-Za-z0-9+#\-\.]+\b', jd)
    
    # Generic stop words to filter out
    stop_words = {"job", "description", "title", "role", "requirements", "and", "or", "to", "the", "in", "of", "with", "a", "for"}
    keywords = [w for w in words if w.lower() not in stop_words and len(w) > 2]
    
    # Heuristic: First key term is treated as primary role title
    title = keywords[0] if keywords else "Software Engineer"
    optional = keywords[1:5] if len(keywords) > 1 else []
    
    # Extract experience range
    min_exp = 2
    max_exp = 8
    jd_lower = jd.lower()
    exp_matches = re.findall(r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)', jd_lower)
    if exp_matches:
        try:
            min_exp = int(exp_matches[0][0])
            max_exp = int(exp_matches[0][1])
        except Exception:
            pass
    else:
        exp_single = re.findall(r'(\d+)\s*\+\s*(?:years?|yrs?)', jd_lower)
        if exp_single:
            try:
                min_exp = int(exp_single[0])
                max_exp = min_exp + 5
            except Exception:
                pass

    # Extract Location (Simple Substring Check)
    location = "N/A"
    indian_cities = ["bangalore", "bengaluru", "pune", "hyderabad", "chennai", "noida", "mumbai", "gurgaon", "delhi", "kolkata", "ahmedabad"]
    for city in indian_cities:
        if city in jd_lower:
            location = "Bangalore" if city in ["bangalore", "bengaluru"] else city.capitalize()
            break

    # Extract Notice Period (Simple Substring Check)
    notice_period = "N/A"
    if "immediate" in jd_lower or "serving notice" in jd_lower:
        notice_period = "Immediate"
    elif "15 days" in jd_lower:
        notice_period = "15 Days"
    elif "30 days" in jd_lower or "1 month" in jd_lower:
        notice_period = "30 Days"

    return {
        "primary_keywords": keywords[:5],
        "mandatory_skills": [title],
        "optional_skills": optional,
        "min_exp": min_exp,
        "max_exp": max_exp,
        "location": location,
        "notice_period": notice_period
    }


def verify_notice_period_in_jd(np, jd):
    np_lower = np.lower()
    jd_lower = jd.lower()
    if not np or np_lower == "n/a":
        return False
        
    # Check simple direct match first
    np_clean = re.sub(r'[^0-9a-z]', '', np_lower)
    jd_clean = re.sub(r'[^0-9a-z]', '', jd_lower)
    if np_clean in jd_clean:
        return True
        
    # Map normalized notice periods to common variations
    if "serving" in np_lower or "currently" in np_lower:
        terms = ["serving", "immediate", "lwd", "last working", "active", "resigned"]
        return any(t in jd_lower for t in terms)
    if "15" in np_lower or "0" in np_lower:
        terms = ["15", "immediate", "serving", "join immediately", "joiners", "0-15"]
        return any(t in jd_lower for t in terms)
    if "1 month" in np_lower or "30" in np_lower or "one month" in np_lower:
        terms = ["30", "1 month", "one month", "30 days", "month"]
        return any(t in jd_lower for t in terms)
    if "2 month" in np_lower or "60" in np_lower:
        terms = ["60", "2 month", "two month", "60 days"]
        return any(t in jd_lower for t in terms)
    if "3 month" in np_lower or "90" in np_lower:
        terms = ["90", "3 month", "three month", "90 days"]
        return any(t in jd_lower for t in terms)
        
    return False


def get_search_keywords(jd, for_market_analysis=False):
    if for_market_analysis:
        prompt = f"""
        You are a Senior Technical Sourcer extracting keywords for WIDE-FUNNEL Talent Market Analysis.
        Identify target location and notice period if specified in the JD.

        TASKS:
        1. Extract the required Experience Range (Min/Max years).
        2. Identify ALL core technical keywords from the JD (do not limit or truncate, extract all of them).
        3. Determine which of these are core mandatory skills and which are optional.

        CRITICAL RULES:
        1. Extract ONLY clean, atomic technology/skill names (e.g. "React", "TypeScript", "TRDP", "IEC-61131").
        2. Do NOT include conversational text, headers, or descriptions.
        3. Do NOT include parenthetical explanations. Each skill in the JSON arrays must be a single, short keyword/tag (1-3 words max).
        4. "mandatory_skills" MUST contain ALL core technical skills and domains mentioned in the JD (e.g., "ADAS", "Computer Vision", "Automated Driving", "Automated Parking", "Image Processing"). Do NOT leave "mandatory_skills" empty.
        5. "optional_skills" MUST contain all other nice-to-have or secondary skills.

        Return ONLY valid JSON:
        {{
            "primary_keywords": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8"],
            "boolean_query": "\"Skill1\" AND \"Skill2\" AND \"Skill3\"",
            "mandatory_skills": ["core_skill_1", "core_skill_2", "core_skill_3", "core_skill_4", "core_skill_5", "core_skill_6"],
            "optional_skills": ["opt1", "opt2", "opt3"],
            "min_exp": 2,
            "max_exp": 8,
            "location": "",
            "notice_period": ""
        }}

        JD:
        {jd}
        """
    else:
        prompt = f"""
        You are a Senior Technical Sourcer. Extract skills, location, and notice period from the JD.

        CRITICAL RULES:
        1. Extract ONLY clean, atomic technology/skill names (e.g. "React", "TypeScript", "TRDP", "IEC-61131").
        2. Do NOT include conversational text, headers, or descriptions.
        3. Do NOT include parenthetical explanations. Each skill in the JSON arrays must be a single, short keyword/tag (1-3 words max).
        4. "mandatory_skills" MUST contain ALL core, non-negotiable technical skills required for the role (e.g., "ADAS", "Computer Vision", "Automated Driving", "Automated Parking", "Image Processing", "C++"). Do NOT leave "mandatory_skills" empty.
        5. Extract all skills mentioned in the JD. Do not restrict the list to just a few; include all of them.

        Return ONLY valid JSON:
        {{
            "primary_keywords": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8"],
            "mandatory_skills": ["mandatory_skill_1", "mandatory_skill_2", "mandatory_skill_3", "mandatory_skill_4", "mandatory_skill_5"],
            "optional_skills": ["opt1", "opt2", "opt3"],
            "min_exp": 2,
            "max_exp": 8,
            "location": "",
            "notice_period": ""
        }}

        JD:
        {jd}
        """
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        raw_json = json.loads(response.json().get('response'))

        # Simple Substring Truth-Check for Location & Notice Period to prevent Hallucination
        loc = str(raw_json.get("location") or "").strip()
        if not loc or loc.lower() == "n/a" or loc.lower() not in jd.lower():
            raw_json["location"] = "N/A"
        else:
            raw_json["location"] = loc

        np = str(raw_json.get("notice_period") or "").strip()
        if verify_notice_period_in_jd(np, jd):
            raw_json["notice_period"] = np
        else:
            raw_json["notice_period"] = "N/A"

        # Defensive fallback: If mandatory_skills is empty but primary_keywords has content, copy them over
        if not raw_json.get("mandatory_skills") and raw_json.get("primary_keywords"):
            raw_json["mandatory_skills"] = raw_json["primary_keywords"]

        print("DEBUG: Keywords successfully generated by LLM (Ollama). Result:", raw_json, flush=True)
        return raw_json
    except Exception as e:
        print(f"Error getting keywords: {e}. Running deterministic fallback parser...")
        fallback_res = deterministic_keywords_fallback(jd, for_market_analysis=for_market_analysis)
        print("DEBUG: Keywords generated by deterministic fallback parser. Result:", fallback_res, flush=True)
        return fallback_res


def get_chromium_executable_path():
    import os
    import sys
    
    # 1. Allow override via environment variables
    env_path = os.environ.get("PLAYWRIGHT_CHROME_PATH") or os.environ.get("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
        
    # 2. Check standard Ubuntu snap path
    snap_path = "/snap/bin/chromium"
    if os.path.exists(snap_path):
        return snap_path
        
    # 3. Check other common Linux paths
    if sys.platform.startswith("linux"):
        for path in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]:
            if os.path.exists(path):
                return path
                
    # 4. Fallback: let Playwright use its own bundled Chromium
    return None

def is_headless_required():
    import os
    import sys
    
    # Priority 1: User explicitly configured via environment variable
    env_val = os.environ.get("PLAYWRIGHT_HEADLESS")
    if env_val is not None:
        return env_val.lower() in ("true", "1", "yes")
        
    # Priority 2: Auto-detect if GUI DISPLAY is available on non-Windows systems
    if sys.platform != "win32":
        display = os.environ.get("DISPLAY")
        if not display:
            print("WARNING: No DISPLAY environment variable found (headless environment detected). Running in headless mode...", flush=True)
            return True
            
    # Default to False for visual debugging on local GUI systems
    return False

async def perform_authenticated_search(query, min_exp=2, max_exp=8, page_num=1, profile_path=None):
    experience_range = (min_exp, max_exp)
    user_data_dir = profile_path or PROFILE_DIR
    
    # Parse query parameter (could be dictionary of separate keywords or string)
    mandatory = ""
    optional = ""
    boolean_query = ""
    if isinstance(query, dict):
        mandatory_val = query.get('mandatory_skills') or query.get('mandatory_keywords') or ''
        optional_val = query.get('optional_skills') or query.get('optional_keywords') or ''
        boolean_query = query.get('boolean_query') or ''
        
        if isinstance(mandatory_val, list):
            mandatory = ", ".join(mandatory_val)
        else:
            mandatory = str(mandatory_val)
            
        if isinstance(optional_val, list):
            optional = ", ".join(optional_val)
        else:
            optional = str(optional_val)
            
        # Safe Fallback: if boolean_query is empty, construct it dynamically!
        if not boolean_query:
            if mandatory and optional:
                opt_terms = [t.strip() for t in optional.split(",") if t.strip()]
                opt_joined = " OR ".join(opt_terms)
                mand_terms = [t.strip() for t in mandatory.split(",") if t.strip()]
                mand_joined = " AND ".join(mand_terms)
                boolean_query = f"({mand_joined}) AND ({opt_joined})"
            elif mandatory:
                mand_terms = [t.strip() for t in mandatory.split(",") if t.strip()]
                boolean_query = " AND ".join(mand_terms)
            else:
                boolean_query = " ".join(query.get('primary_keywords', []))
    else:
        boolean_query = query

    async with async_playwright() as p:
        context = None
        try:
            # Auto-heal: delete stale Chromium process singleton lock files if present
            import os
            lock_file = os.path.join(user_data_dir, "SingletonLock")
            if os.path.exists(lock_file):
                print(f"Stale browser lock found at {lock_file}. Healing directory...", flush=True)
                try:
                    os.remove(lock_file)
                    print("Stale browser lock successfully cleared.", flush=True)
                except Exception as rm_err:
                    print(f"Could not remove lock file: {rm_err}", flush=True)

            exec_path = get_chromium_executable_path()
            headless_mode = is_headless_required()
            
            # Base launch arguments
            launch_args = [
                "--disable-http2",
                "--disable-blink-features=AutomationControlled"
            ]
            
            if headless_mode:
                launch_args.extend([
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ])
                viewport_setting = {"width": 1280, "height": 800}
            else:
                launch_args.append("--start-maximized")
                viewport_setting = None # Let it maximize
                
            print(f"Launching Chromium: path={exec_path}, headless={headless_mode} at {user_data_dir}", flush=True)
            
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=exec_path,
                headless=headless_mode,
                viewport=viewport_setting,
                ignore_https_errors=False,
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                args=launch_args
            )

            page = (
                context.pages[0]
                if context.pages
                else await context.new_page()
            )
            
            print(f"Starting live search for: {query}")
            await page.goto(
                "https://recruit.naukri.com",
                wait_until="domcontentloaded",
                timeout=60000
            )

            await page.wait_for_timeout(5000)

            await page.goto(
                "https://resdex.naukri.com",
                wait_until="domcontentloaded",
                timeout=60000
            )
            current_url = page.url
            print("CURRENT URL:", current_url)
            await page.screenshot(path="after_resdex_load.png")
            await page.wait_for_timeout(5000)
            
            # Check for Expired Session redirect
            if "login" in page.url.lower():
                print("Session completely expired. Redirection to login screen detected.", flush=True)
                return {"error": "session_expired"}
                
            # Auto-Heal: Check if "Someone is already logged into Resdex" lock screen appears
            try:
                print("Checking for session lock / concurrent login screen...", flush=True)
                page_content = await page.content()
                is_locked = "Someone is already logged into Resdex" in page_content
                
                if is_locked:
                    print("Found 'Someone is already logged into Resdex' lock screen. Searching for Reset Subuser button...", flush=True)
                    reset_btn = await page.wait_for_selector(
                        "button:has-text('Reset Subuser'), input[value*='Reset Subuser'], a:has-text('Reset Subuser'), text=Reset Subuser, #resetSubuser, input[type='button'][value*='Reset']", 
                        timeout=5000
                    )
                    if reset_btn:
                        print("Found Reset Subuser button. Clicking Reset Subuser to unlock session...", flush=True)
                        await reset_btn.click()
                        await page.wait_for_timeout(10000) # Wait 10 seconds for reset and redirect to complete
                        print("Session successfully reset and logged in. Current URL:", page.url, flush=True)
                        await page.screenshot(path="after_session_reset.png")
                        
                        # Re-verify if we got unlocked
                        re_content = await page.content()
                        if "Someone is already logged into Resdex" in re_content:
                            print("Clicking Reset Subuser succeeded but we are still locked on the page.", flush=True)
                            return {"error": "session_locked"}
                    else:
                        print("Reset Subuser button not found on concurrent lock screen.", flush=True)
                        return {"error": "session_locked"}
            except Exception as reset_err:
                print(f"Error checking or resetting concurrent session: {reset_err}. Continuing search...", flush=True)
                # If we are stuck on the lock screen, stop immediately rather than timing out
                try:
                    re_content = await page.content()
                    if "Someone is already logged into Resdex" in re_content:
                        return {"error": "session_locked"}
                except Exception:
                    pass
            
            
            # 1. Target standard Resdex keywords input field and enter skills
            mandatory_skills = query.get("mandatory_skills", [])
            optional_skills = query.get("optional_skills", [])
            
            # Helper to find current active keywords input
            async def get_active_keywords_input():
                for selector in [
                    "input[name='ezKeywordsAny']", 
                    "input[placeholder*='skills']", 
                    "input[placeholder*='Skills']", 
                    "[class*='keyword-input'] input", 
                    "textarea"
                ]:
                    try:
                        el = await page.wait_for_selector(selector, timeout=2000)
                        if el and await el.is_visible():
                            return el
                    except Exception:
                        pass
                return None

            # Type and add all mandatory skills
            for skill in mandatory_skills:
                try:
                    el = await get_active_keywords_input()
                    if not el:
                        print(f"Warning: Could not locate keywords input to enter mandatory skill: {skill}")
                        continue
                    
                    print(f"Adding mandatory skill: {skill}", flush=True)
                    await el.focus()
                    await el.fill("")
                    await page.keyboard.type(skill, delay=50)
                    await page.wait_for_timeout(1000)
                    
                    dropdown_item = await page.query_selector(
                        ".autocomplete-suggestion, [class*='suggestion'] div, #suggestor-listbox [role='option'], .suggestor-wrapper [role='option'], [id*='listbox'] [role='option'], [class*='listbox'] [role='option'], .suggestor-box + div [role='option']"
                    )
                    if dropdown_item:
                        await dropdown_item.click()
                    else:
                        await page.keyboard.press("Enter")
                    await page.wait_for_timeout(3000)
                except Exception as skill_err:
                    print(f"Could not enter mandatory skill '{skill}': {skill_err}", flush=True)

            # Type and add all optional skills
            for skill in optional_skills:
                try:
                    el = await get_active_keywords_input()
                    if not el:
                        print(f"Warning: Could not locate keywords input to enter optional skill: {skill}")
                        continue
                    
                    print(f"Adding optional skill: {skill}", flush=True)
                    await el.focus()
                    await el.fill("")
                    await page.keyboard.type(skill, delay=50)
                    await page.wait_for_timeout(1000)
                    
                    dropdown_item = await page.query_selector(
                        ".autocomplete-suggestion, [class*='suggestion'] div, #suggestor-listbox [role='option'], .suggestor-wrapper [role='option'], [id*='listbox'] [role='option'], [class*='listbox'] [role='option'], .suggestor-box + div [role='option']"
                    )
                    if dropdown_item:
                        await dropdown_item.click()
                    else:
                        await page.keyboard.press("Enter")
                    await page.wait_for_timeout(500)
                except Exception as skill_err:
                    print(f"Could not enter optional skill '{skill}': {skill_err}", flush=True)

            # 2. Mark Mandatory Skills as Starred (Only the 2nd mandatory skill needs to be manually starred, since the 1st is starred by default)
            if len(mandatory_skills) > 1:
                skill_to_star = mandatory_skills[1]
                try:
                    tag = await page.wait_for_selector(
                        f"button.star-tag-wrapper:has-text('{skill_to_star}'), button[aria-label='{skill_to_star}'], .tag-label:has-text('{skill_to_star}'), span:has-text('{skill_to_star}'), .tag:has-text('{skill_to_star}')", 
                        timeout=3000
                    )
                    if tag:
                        star_btn = await tag.query_selector("i.star, .star, .star-icon, [class*='star']")
                        click_target = star_btn if star_btn else tag
                        await click_target.click()
                        print(f"Starred mandatory skill (2nd skill): {skill_to_star}", flush=True)
                        await page.wait_for_timeout(500)
                except Exception as star_err:
                    print(f"Could not star mandatory skill {skill_to_star}: {star_err}", flush=True)

            # 3. Add Experience Filter from JD
            try:
                print(f"Setting Experience Filter: {min_exp} to {max_exp} years...")
                min_field = await page.wait_for_selector("input[placeholder*='Min'], #minExp, [name='minExp']", timeout=5000)
                if min_field:
                    await min_field.fill(str(min_exp))
                max_field = await page.wait_for_selector("input[placeholder*='Max'], #maxExp, [name='maxExp']", timeout=5000)
                if max_field:
                    await max_field.fill(str(max_exp))
            except Exception as exp_err:
                print(f"Could not set experience filter: {exp_err}")

            # 4. Location Search Input
            target_location = query.get("location", "N/A")
            if target_location and target_location != "N/A":
                try:
                    loc_input = await page.wait_for_selector(
                        "input[name='locations'], input[placeholder*='location'], input[name*='location'], input[name='location']", 
                        timeout=5000
                    )
                    if loc_input:
                        await loc_input.focus()
                        await loc_input.fill("")
                        await page.keyboard.type(target_location, delay=50)
                        await page.wait_for_timeout(1000)
                        suggestion = await page.query_selector(
                            ".autocomplete-suggestion, [class*='suggestion'] div, #suggestor-listbox [role='option'], .suggestor-wrapper [role='option'], [id*='listbox'] [role='option'], [class*='listbox'] [role='option']"
                        )
                        if suggestion:
                            await suggestion.click()
                        else:
                            await page.keyboard.press("Enter")
                        print(f"Location filter applied: {target_location}")
                except Exception as loc_err:
                    print(f"Could not apply Location filter: {loc_err}")

            # 5. Apply Notice Period Checkbox
            target_np = query.get("notice_period", "N/A")
            if target_np and target_np != "N/A":
                try:
                    # In Resdex.html, notice period chips are under #noticePeriodTags
                    # Map the target notice period text to one of the chip titles:
                    # "0 - 15 days", "1 month", "2 months", "3 months", "Currently serving notice period"
                    np_mapping = []
                    np_lower = target_np.lower()
                    if "immediate" in np_lower or "serving" in np_lower:
                        np_mapping.append("currently serving notice period")
                    if "15" in np_lower:
                        np_mapping.append("0 - 15 days")
                    if "30" in np_lower or "1 month" in np_lower:
                        np_mapping.append("1 month")
                    if "2 month" in np_lower:
                        np_mapping.append("2 months")
                    if "3 month" in np_lower:
                        np_mapping.append("3 months")
                        
                    if np_mapping:
                        chips = await page.query_selector_all("#noticePeriodTags .selectable-chip")
                        for chip in chips:
                            span = await chip.query_selector("span.txt")
                            if span:
                                title = (await span.evaluate("el => el.getAttribute('title') || el.textContent || ''")).strip().lower()
                                is_selected = await chip.evaluate("el => el.classList.contains('selected')")
                                
                                should_select = False
                                for target in np_mapping:
                                    if target in title:
                                        should_select = True
                                        break
                                
                                if should_select and not is_selected:
                                    print(f"Selecting notice period chip: {title}", flush=True)
                                    await chip.evaluate("el => el.click()")
                                    await page.wait_for_timeout(200)
                                elif not should_select and is_selected:
                                    # Don't unselect "Any" chip unless we are selecting a specific one
                                    if "any" in title:
                                        continue
                                    print(f"Unselecting notice period chip: {title}", flush=True)
                                    await chip.evaluate("el => el.click()")
                                    await page.wait_for_timeout(200)
                    print(f"Notice Period filter applied: {target_np}")
                except Exception as np_err:
                    print(f"Could not apply Notice Period filter: {np_err}")

            # 6. Apply Salary Filter (Exp * 3)
            try:
                avg_exp = (min_exp + max_exp) / 2
                target_salary = int(avg_exp * 3)
                print(f"Applying Salary Filter: {target_salary} LPA")
            except:
                pass

            # Click Search
            search_btn = await page.query_selector("button:has-text('Search candidates')")
            if search_btn:
                await search_btn.click()
            else:
                await page.keyboard.press("Enter")
                
            await page.wait_for_load_state("networkidle")
            
            # Handle Pagination if page_num > 1
            if page_num > 1:
                for p_i in range(page_num - 1):
                    next_btn = await page.query_selector(
                        "[data-testid='next-page'], button[data-testid='next-page'], "
                        "button:has-text('Next'), a:has-text('Next'), [aria-label='Next'], "
                        ".ico-expand.next"
                    )
                    if next_btn:
                        try:
                            await next_btn.click(timeout=3000)
                        except Exception:
                            await next_btn.evaluate("el => el.click()")
                        await page.wait_for_timeout(5000)
                    else:
                        print(f"Could not find Next button for page pagination step {p_i + 2}")
                        break

            # 5. Extract Detailed Results (Top 10)
            results = []
            print("Waiting for results grid to stabilize...", flush=True)
            await page.wait_for_timeout(10000)
            
            # Try multiple card selectors for v3
            card_selectors = [".tuple", ".tuple-container", "[class*='tuple']", ".candidate-card"]
            cards = []
            for sel in card_selectors:
                cards = await page.query_selector_all(sel)
                if cards:
                    print(f"Found {len(cards)} cards using selector: {sel}")
                    break
            
            if not cards:
                print("No candidate cards found. Results page might not have loaded correctly.")
                await page.screenshot(path="resdex_v3_no_results.png")
                return []

            pool_candidates = []  # ALL candidates found on page (for 'Other Candidates' table)
            deep_analyzed_names = set()  # Track who got deep-analyzed

            for card in cards:
                try:
                    # 1. Find name and link
                    name_el = await card.query_selector(".name, .title, [class*='name']")
                    name = (await name_el.inner_text()).strip() if name_el else "Unknown Candidate"
                    if not name or name == "Unknown Candidate":
                        continue
                    
                    link_el = await card.query_selector("a[href*='profile'], .name a")
                    profile_url = await link_el.get_attribute("href") if link_el else None
                    
                    exp_el = await card.query_selector(".exp, [class*='exp']")
                    exp_text = (await exp_el.inner_text()).strip() if exp_el else "N/A"
                    
                    skills_el = await card.query_selector(".key-skills, .may-know, .skill-container")
                    context_text = (await skills_el.inner_text()).strip() if skills_el else ""

                    np_el = await card.query_selector("span:has-text('days'), span:has-text('month'), [class*='notice']")
                    np_text = (await np_el.inner_text()).strip() if np_el else "N/A"
                    
                    # Fallback to card text parsing if selector returns N/A (e.g. nested in generic div)
                    if np_text == "N/A":
                        card_txt = await card.inner_text()
                        np_text = extract_notice_period_from_card_text(card_txt)

                    # 2. Check candidate activity level from DOM
                    activity_text = ""
                    try:
                        # Search for elements containing 'Active' or class indicators
                        activity_el = await card.query_selector("[class*='active-date'], .active-date-info, span:has-text('Active'), [class*='tuple-footer'] span:has-text('Active'), [class*='tuple-meta'] span:has-text('Active')")
                        if activity_el:
                            activity_text = await activity_el.inner_text()
                        else:
                            # Fallback to scanning lines of card text for 'Active'
                            card_txt = await card.inner_text()
                            for line in card_txt.split("\n"):
                                if "active" in line.lower():
                                    activity_text = line
                                    break
                    except Exception as act_parse_err:
                        print(f"Error checking activity status for {name}: {act_parse_err}", flush=True)

                    activity_text = activity_text.strip()
                    
                    # 3. Apply Strict Active filter (<= 30 Days)
                    if not is_candidate_active_in_30_days(activity_text):
                        print(f"⏩ Filtering out {name} - inactive over 30 days: '{activity_text}'", flush=True)
                        continue
                        
                    # 4. Apply Strict Notice Period filter (<= 30 Days / 1 Month)
                    if not is_notice_period_within_30_days(np_text):
                        print(f"⏩ Filtering out {name} - notice period is too long: '{np_text}'", flush=True)
                        continue

                    # 5. Always add to pool list if they pass the active and notice period filters
                    full_profile_url = ("https://resdex.naukri.com" + profile_url) if profile_url and not profile_url.startswith("http") else (profile_url or page.url)
                    if name not in [c["name"] for c in pool_candidates]:
                        pool_candidates.append({
                            "name": name,
                            "exp": exp_text,
                            "notice_period": np_text,
                            "link": full_profile_url
                        })

                    # 6. Stop deep-scraping if we already have 10 deep results
                    if len(results) >= 10:
                        continue

                    phone_text = "Hidden"
                    email_text = "Hidden"
                    
                    # DEEP EXTRACTION: Open Profile in new tab to read Experience & Projects (0 Credits Used)
                    experience_text = ""
                    if profile_url:
                        if not profile_url.startswith("http"):
                            profile_url = "https://resdex.naukri.com" + profile_url
                        
                        print(f"Opening profile for {name} to scrape experience...", flush=True)
                        profile_page = await context.new_page()
                        await profile_page.goto(profile_url, wait_until="domcontentloaded")
                        await profile_page.wait_for_timeout(3000)
                        
                        try:
                            # PRIORITY 1: Click "Attached CV" tab and extract the actual uploaded resume
                            # This is what candidates like Alby Wilson use instead of filling Naukri profile fields
                            attached_cv_text = ""
                            cv_tab = await profile_page.query_selector("#tab-videoAndCv, button[id*='videoAndCv'], button:has-text('Attached CV')")
                            if cv_tab:
                                cv_tab_selected = await cv_tab.get_attribute("aria-selected")
                                if cv_tab_selected != "true":
                                    await cv_tab.click()
                                    await profile_page.wait_for_timeout(2000)  # wait for tab content to load
                                
                                # Try to grab the resume text from the now-active CV tab panel
                                cv_panel_selectors = [
                                    "[role='tabpanel'][id*='videoAndCv']",
                                    "[aria-labelledby='tab-videoAndCv']",
                                    ".cv-preview-container",
                                    ".resume-preview-wrapper",
                                    "[class*='cvPreview']",
                                    "[class*='resumePreview']"
                                ]
                                for sel in cv_panel_selectors:
                                    cv_el = await profile_page.query_selector(sel)
                                    if cv_el:
                                        txt = await cv_el.inner_text()
                                        if txt and len(txt.strip()) > 100:
                                            attached_cv_text = txt.strip()
                                            print(f"✅ Scraped Attached CV tab content for {name} ({len(attached_cv_text)} chars).", flush=True)
                                            break

                            if attached_cv_text:
                                combined_texts = ["=== ATTACHED RESUME ===", attached_cv_text]
                                experience_text = "\n\n".join(combined_texts)
                            else:
                                # PRIORITY 2: Profile detail tab — .profile-width-content (Naukri structured profile)
                                # Go back to the Profile detail tab if needed
                                profile_tab = await profile_page.query_selector("#tab-profile, button[id='tab-profile'], button:has-text('Profile detail')")
                                if profile_tab:
                                    profile_tab_selected = await profile_tab.get_attribute("aria-selected")
                                    if profile_tab_selected != "true":
                                        await profile_tab.click()
                                        await profile_page.wait_for_timeout(1500)

                                profile_content_el = await profile_page.query_selector(".profile-width-content, .profile-content")
                                if profile_content_el:
                                    profile_full_text = await profile_content_el.inner_text()
                                    if profile_full_text and len(profile_full_text.strip()) > 100:
                                        combined_texts = ["=== NAUKRI PROFILE ===", profile_full_text.strip()]
                                        experience_text = "\n\n".join(combined_texts)
                                        print(f"⚠️ No attached CV — using Profile detail tab for {name} ({len(profile_full_text)} chars).", flush=True)

                                # PRIORITY 3: Individual work-exp-card elements
                                if not experience_text:
                                    job_descs = []
                                    desc_els = await profile_page.query_selector_all("div.work-exp-card div.desc")
                                    for desc_el in desc_els:
                                        txt = await desc_el.inner_text()
                                        if txt:
                                            job_descs.append(txt.strip())
                                    desig_els = await profile_page.query_selector_all("div.work-exp-card div.desig")
                                    for desig_el in desig_els:
                                        txt = await desig_el.inner_text()
                                        if txt:
                                            job_descs.append(txt.strip())
                                    project_descs = []
                                    proj_els = await profile_page.query_selector_all(".cv-project, .project-details")
                                    for proj_el in proj_els:
                                        txt = await proj_el.inner_text()
                                        if txt and len(txt.strip()) > 20:
                                            project_descs.append(txt.strip())
                                    combined_texts = []
                                    if job_descs:
                                        combined_texts.append("=== WORK EXPERIENCE ===")
                                        combined_texts.extend(job_descs)
                                    if project_descs:
                                        combined_texts.append("=== PROJECTS ===")
                                        combined_texts.extend(project_descs)
                                    if not combined_texts:
                                        body_el = await profile_page.query_selector("body")
                                        if body_el:
                                            body_txt = await body_el.inner_text()
                                            if body_txt:
                                                combined_texts.append("=== RAW PROFILE TEXT ===")
                                                combined_texts.append(body_txt[:5000])
                                    experience_text = "\n\n".join(combined_texts)
                                    print(f"⚠️ Fell back to work-exp-card for {name}.", flush=True)

                            print(f"\n==========================================")
                            print(f"📄 SCRAPED TEXT FOR: {name}")
                            print(f"==========================================")
                            print(experience_text[:1000] if experience_text.strip() else "[NO TEXT FOUND]")
                            print(f"==========================================\n")
                        except Exception as scrape_err:
                            print(f"Could not scrape DOM profile for {name}: {scrape_err}")
                        
                        await profile_page.close()

                    results.append({
                        "name": name.strip(),
                        "exp": exp_text.strip(),
                        "context": context_text.strip(),
                        "notice_period": np_text.strip(),
                        "phone": phone_text.strip(),
                        "email": email_text.strip(),
                        "link": profile_url or page.url,
                        "experience_text": experience_text
                    })
                    deep_analyzed_names.add(name.strip())
                except Exception as e:
                    print(f"Error extracting profile: {e}")
                    continue
            
            print(f"Successfully extracted {len(results)} deep-analyzed leads.")
            
            # Build 'Other Candidates' = pool_candidates minus the ones we deep-analyzed
            other_candidates = [
                c for c in pool_candidates
                if c['name'] not in deep_analyzed_names
            ]
            print(f"Other candidates in pool (not deep-analyzed): {len(other_candidates)}", flush=True)
            
            return {"deep_results": results, "other_candidates": other_candidates}
        except Exception as e:
            print(f"Live search error: {e}")
            try:
                if 'page' in locals() and page:
                    await page.screenshot(path="live_search_error.png")
                    print("Screenshot of search failure saved to live_search_error.png", flush=True)
                    
                    # Safe fallback checks inside exception handler
                    current_url = page.url
                    if "login" in current_url.lower():
                        return {"error": "session_expired"}
                    
                    page_content = await page.content()
                    if "Someone is already logged into Resdex" in page_content:
                        return {"error": "session_locked"}
            except Exception as ss_err:
                print(f"Could not save debug screenshot or diagnose: {ss_err}", flush=True)
            return []
        finally:
            if context:
                await context.close()

def simulate_naukri_search(data):
    primary = data.get('primary_keywords', [])
    secondary = data.get('secondary_keywords', [])
    
    # Construct a clean keyword chip display string for the UI
    mand_skills = data.get('mandatory_skills', [])
    opt_skills = data.get('optional_skills', [])
    
    display_parts = []
    if mand_skills:
        display_parts.append(f"Mandatory: {', '.join(mand_skills)}")
    if opt_skills:
        display_parts.append(f"Optional: {', '.join(opt_skills)}")
        
    boolean_display = " | ".join(display_parts) if display_parts else " ".join(primary)
    
    return {
        "keywords_used": primary + secondary,
        "boolean_query": boolean_display,
        "simulated_leads": []
    }