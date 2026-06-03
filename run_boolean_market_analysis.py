import os
import sys
import re
import json
import asyncio
import requests
from collections import Counter
from datetime import datetime
from playwright.async_api import async_playwright

# Add current dir to path to import sourcing_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sourcing_agent
from sourcing_agent import (
    is_candidate_active_in_30_days, 
    extract_notice_period_from_card_text,
    PROFILE_DIR,
    get_chromium_executable_path,
    is_headless_required,
    ensure_boolean_toggle_on
)

# 1. Deterministic Match Engine (using negative lookarounds)
def is_keyword_in_text(kw: str, text: str) -> bool:
    kw = kw.strip().lower()
    text = text.lower()
    if not kw or not text:
        return False
    pattern = rf"(?<![a-zA-Z0-9_-]){re.escape(kw)}(?![a-zA-Z0-9_-])"
    return bool(re.search(pattern, text))

def market_analyze_candidate(lead: dict, requirements: list, jd_min_exp: int = 2, jd_max_exp: int = 10) -> dict:
    skills_raw = lead.get('skills', '') or ''
    current_raw = lead.get('current', '') or ''
    experience_text = f"{skills_raw} {current_raw}".lower()

    matched_skills = []
    requirements_analysis = []

    for req in requirements:
        req_name = req.get('display_name', '')
        valid_keywords = [k.lower().strip() for k in req.get('keywords', [req_name])]
        is_mandatory = req.get('mandatory', False)
        found = False
        matching_keyword = ""

        for kw in valid_keywords:
            # 1. Direct match
            if is_keyword_in_text(kw, experience_text):
                found = True
                matching_keyword = kw
                break
            # 2. Singular form
            if kw.endswith('s') and len(kw) > 3 and is_keyword_in_text(kw[:-1], experience_text):
                found = True
                matching_keyword = kw[:-1]
                break
            # 3. Multi-word: all sub-words present
            sub_words = [w.strip() for w in kw.split() if len(w.strip()) > 1]
            if len(sub_words) > 1 and all(is_keyword_in_text(w, experience_text) for w in sub_words):
                found = True
                matching_keyword = sub_words[0]
                break

        if found:
            matched_skills.append(req_name)
            requirements_analysis.append({
                "requirement": req_name, "status": "met",
                "keyword": matching_keyword, "is_mandatory": is_mandatory
            })
        else:
            requirements_analysis.append({
                "requirement": req_name, "status": "not_met",
                "keyword": "NOT_FOUND", "is_mandatory": is_mandatory
            })

    def parse_exp_years(exp_str):
        if not exp_str or exp_str == "N/A":
            return None
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', exp_str, re.IGNORECASE)
        if m:
            return int(float(m.group(1)))
        m2 = re.search(r'(\d+)', exp_str)
        return int(m2.group(1)) if m2 else None

    yrs = parse_exp_years(lead.get('experience', ''))

    mandatory_reqs = [r for r in requirements if r.get('mandatory', False)]
    optional_reqs = [r for r in requirements if not r.get('mandatory', False)]

    if mandatory_reqs:
        met_mandatory_count = sum(
            1 for name in matched_skills
            if any(r.get('display_name') == name and r.get('mandatory', False) for r in mandatory_reqs)
        )
        mand_ratio = met_mandatory_count / len(mandatory_reqs)
        mandatory_score = mand_ratio * 60
    else:
        met_mandatory_count = 0
        mandatory_score = 60
        mand_ratio = 1.0

    if optional_reqs:
        met_optional_count = sum(
            1 for name in matched_skills
            if any(r.get('display_name') == name and not r.get('mandatory', False) for r in optional_reqs)
        )
        optional_score = (met_optional_count / len(optional_reqs)) * 20
    else:
        optional_score = 0
        if mandatory_reqs:
            mandatory_score = mand_ratio * 80
        else:
            mandatory_score = 80

    experience_score = 0
    if yrs is not None:
        if jd_min_exp <= yrs <= jd_max_exp:
            experience_score = 20
        elif (jd_min_exp - 1) <= yrs <= (jd_max_exp + 2):
            experience_score = 10
        else:
            experience_score = 0

    if mandatory_reqs and met_mandatory_count == 0:
        match_percentage = round(experience_score * 0.5)
    else:
        match_percentage = round(mandatory_score + optional_score + experience_score)

    match_percentage = min(100, max(0, match_percentage))

    lead.update({
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "requirements_analysis": requirements_analysis,
    })
    return lead

async def run_boolean_market_analysis(boolean_query: str, min_exp: int = 2, max_exp: int = 10, max_pages: int = 5):
    user_data_dir = PROFILE_DIR
    
    # 1. Parse keywords from boolean query to build candidate analysis requirements
    fallback_keywords = []
    raw_parts = re.split(r'\s+(?:AND|OR|and|or)\s+', boolean_query)
    for part in raw_parts:
        clean_part = re.sub(r'[\(\)"\']', '', part).strip()
        if clean_part and clean_part.upper() not in ("NOT", "AND", "OR", "VS", "THE", "AND/OR"):
            fallback_keywords.append(clean_part)
            
    requirements = []
    for kw in sorted(list(set(fallback_keywords))):
        requirements.append({
            "display_name": kw,
            "keywords": [kw],
            "mandatory": True
        })
        
    print(f"Generated evaluation requirements from Boolean Query: {[r['display_name'] for r in requirements]}")

    # Auto-heal stale lock
    lock_file = os.path.join(user_data_dir, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Cleared stale browser lock.")
        except Exception:
            pass

    exec_path = get_chromium_executable_path()
    headless_mode = is_headless_required()

    launch_args = ["--disable-http2", "--disable-blink-features=AutomationControlled"]
    if headless_mode:
        launch_args += ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
    else:
        launch_args.append("--start-maximized")

    all_candidates = []

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
            await ensure_boolean_toggle_on(page)

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

            # Set Experience limits (0 to 25 to scan the whole market pool)
            print("Setting experience filter: Min=0, Max=25")
            min_input = await page.query_selector("input[name='minExp']")
            if min_input:
                await min_input.fill("0")
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
            
            max_input = await page.query_selector("input[name='maxExp']")
            if max_input:
                await max_input.fill("25")
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

            # Scrape cards page by page
            for page_num in range(1, max_pages + 1):
                print(f"Scraping page {page_num}/{max_pages}...")
                card_selectors = [".tuple", ".tuple-container", "[class*='tuple']", ".candidate-card"]
                cards = []
                for sel in card_selectors:
                    cards = await page.query_selector_all(sel)
                    if cards:
                        break
                if not cards:
                    print(f"No cards found on page {page_num}. Stopping.")
                    break

                for card in cards:
                    try:
                        name_el = await card.query_selector(".name, .title, [class*='name']")
                        name = (await name_el.inner_text()).strip() if name_el else ""
                        if not name:
                            continue

                        exp_el = await card.query_selector(".exp, [class*='exp'], [class*='experience'], .info-item")
                        exp = (await exp_el.inner_text()).strip() if exp_el else ""
                        if not exp or exp == "N/A" or not any(c.isdigit() for c in exp):
                            card_txt_for_exp = await card.inner_text()
                            m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', card_txt_for_exp, re.IGNORECASE)
                            exp = m.group(0).strip() if m else "N/A"

                        current_el = await card.query_selector(".current, .designation, [class*='current']")
                        current = (await current_el.inner_text()).strip() if current_el else "N/A"

                        loc_el = await card.query_selector(".loc, [class*='loc'], [class*='location']")
                        location = (await loc_el.inner_text()).strip() if loc_el else "N/A"

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

                # Go to next page
                if page_num < max_pages:
                    try:
                        next_selector = "[data-testid='next-page'], button[data-testid='next-page'], button:has-text('Next'), a:has-text('Next')"
                        next_btn = await page.query_selector(next_selector)
                        if next_btn:
                            await page.click(next_selector, timeout=5000)
                            await page.wait_for_timeout(5000)
                        else:
                            break
                    except Exception as pg_err:
                        print(f"Pagination click failed: {pg_err}")
                        break

        except Exception as e:
            print(f"❌ Error during scan: {e}")
        finally:
            await context.close()

    if not all_candidates:
        print("❌ No candidates collected. Check session or query.")
        return

    print(f"\n📊 Collected {len(all_candidates)} candidates. Scoring and compiling Market Report...")

    # Score candidates
    scored = []
    for c in all_candidates:
        res = market_analyze_candidate(c, requirements, min_exp, max_exp)
        scored.append(res)

    # ── Compile Summary Stats ──
    def parse_exp_years(exp_str):
        if not exp_str or exp_str == "N/A":
            return None
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yrs?|years?|yr\b|y\b)', exp_str, re.IGNORECASE)
        if m:
            return int(float(m.group(1)))
        m2 = re.search(r'(\d+)', exp_str)
        return int(m2.group(1)) if m2 else None

    buckets = {"0-3y": 0, "3-5y": 0, "5-7y": 0, "7-9y": 0, "9-12y": 0, "12y+": 0}
    match_distribution = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    
    active_30 = sum(1 for c in scored if c.get('is_active_30d') is True)
    notice_30 = sum(1 for c in scored if '30' in str(c.get('notice_period', '')) or 'immediate' in str(c.get('notice_period', '')).lower())
    in_target = 0
    total_match_score = 0
    high_quality_pool = 0
    active_high_quality_pool = 0

    skill_counts = {}
    company_names = []
    city_names = []

    for c in scored:
        yrs = parse_exp_years(c['experience'])
        c['in_target_range'] = False
        if yrs is not None:
            c['in_target_range'] = min_exp <= yrs <= max_exp
            if c['in_target_range']:
                in_target += 1
            if yrs < 3:    buckets["0-3y"] += 1
            elif yrs < 5:  buckets["3-5y"] += 1
            elif yrs < 7:  buckets["5-7y"] += 1
            elif yrs < 9:  buckets["7-9y"] += 1
            elif yrs < 12: buckets["9-12y"] += 1
            else:          buckets["12y+"] += 1

        mp = c.get('match_percentage', 0)
        total_match_score += mp
        
        if mp >= 90:   match_distribution["90-100"] += 1
        elif mp >= 80: match_distribution["80-89"] += 1
        elif mp >= 70: match_distribution["70-79"] += 1
        elif mp >= 60: match_distribution["60-69"] += 1
        else:          match_distribution["<60"] += 1

        if mp >= 80:
            high_quality_pool += 1
            if c.get('is_active_30d') is True:
                active_high_quality_pool += 1

        # Skills normalizer
        c_skills = c.get('skills', '') or ''
        raw_skills = re.split(r'[|,\n]', c_skills)
        for s_raw in raw_skills:
            s_clean = s_raw.replace('Key skills', '').strip()
            if s_clean and s_clean.lower() != 'n/a':
                norm = s_clean.lower()
                display_name = s_clean.upper() if len(s_clean) <= 4 else s_clean
                skill_counts[norm] = skill_counts.get(norm, {"name": display_name, "count": 0})
                skill_counts[norm]["count"] += 1

        # Company parsing
        cur = c.get('current', '')
        if ' at ' in cur:
            company_names.append(cur.split(' at ')[-1].strip())
        elif cur and cur != 'N/A':
            company_names.append(cur.strip())

        # Location parsing
        loc = c.get('location', '')
        if loc and loc != 'N/A':
            city_names.append(loc.split(',')[0].strip())

    total = len(scored)
    avg_match_score = round(total_match_score / total) if total else 0
    top_skills = sorted(skill_counts.values(), key=lambda x: x['count'], reverse=True)[:10]
    top_companies = Counter(company_names).most_common(6)
    top_cities = Counter(city_names).most_common(6)

    # Availability Score & Tightness
    active_pct = (active_30 / total * 100) if total else 0
    notice_pct = (notice_30 / total * 100) if total else 0
    target_pct = (in_target / total * 100) if total else 0
    availability_score = round(min(100, (active_pct * 0.5 + notice_pct * 0.3 + target_pct * 0.2)))

    if in_target >= 30:   tightness = "High Supply"
    elif in_target >= 12: tightness = "Moderate Supply"
    elif in_target >= 5:  tightness = "Low Supply"
    else:                 tightness = "Scarce"

    if total >= 100 and high_quality_pool >= 20:   market_health = "Strong"
    elif total >= 50 and high_quality_pool >= 10:   market_health = "Moderate"
    elif total >= 20 and high_quality_pool >= 3:    market_health = "Tight"
    else:                                           market_health = "Scarce"

    if active_high_quality_pool >= 15:    hiring_difficulty = "Low"
    elif active_high_quality_pool >= 5:     hiring_difficulty = "Medium"
    elif active_high_quality_pool >= 1:     hiring_difficulty = "High"
    else:                                   hiring_difficulty = "Very High"

    # AI narrative prompt
    dist_text = ", ".join([f"{k}: {v}" for k, v in buckets.items() if v > 0])
    company_text = ", ".join([f"{c[0]} ({c[1]})" for c in top_companies[:4]])
    city_text = ", ".join([f"{c[0]} ({c[1]})" for c in top_cities[:4]])

    narrative_prompt = f"""You are a Senior Talent Market Analyst. Write a 4-5 sentence professional market intelligence brief.

Data:
- Role requirement Boolean query: {boolean_query}
- Total candidates found: {total}
- Target experience: {min_exp}-{max_exp} years → {in_target} candidates match ({round(target_pct)}%)
- Active in last 30 days: {active_30} ({round(active_pct)}%)
- Available with short notice (≤30 days): {notice_30}
- Experience distribution: {dist_text}
- Top hiring companies (candidate sources): {company_text}
- Top cities: {city_text}
- Availability Score: {availability_score}/100
- Market Tightness: {tightness}
- Market Health: {market_health}
- Hiring Difficulty: {hiring_difficulty}

Write ONLY the brief paragraph. Be direct, analytical, and professional. Use concrete numbers."""

    # Call Ollama for brief
    narrative = ""
    try:
        from app import OLLAMA_API_URL, MODEL_NAME
        payload = {"model": MODEL_NAME, "prompt": narrative_prompt, "stream": False}
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=25)
        narrative = response.json().get('response', '').strip()
    except Exception:
        narrative = (f"The talent pool for this Boolean query shows {total} candidates with relevant skills on Naukri. "
                     f"Of these, {in_target} ({round(target_pct)}%) fall within the target {min_exp}-{max_exp} year experience range. "
                     f"Market availability is {'high' if availability_score > 60 else 'moderate' if availability_score > 35 else 'tight'} "
                     f"with {active_30} candidates active in the last 30 days.")

    # Print Report
    print("\n" + "="*70)
    print("📋 TALENT MARKET INTELLIGENCE REPORT (BOOLEAN QUERY)")
    print("="*70)
    print(f"Boolean Search:   {boolean_query}")
    print(f"Date Generated:   {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"Target Exp Range: {min_exp}-{max_exp} years ({in_target} matches)")
    print("-" * 70)
    print(f"📊 Total Talent Pool:      {total} candidates")
    print(f"⚡ Availability Score:     {availability_score}/100")
    print(f"🎯 Avg Match Score:        {avg_match_score}%")
    print(f"🟢 Active (Last 30d):      {active_30} ({round(active_pct)}% of pool)")
    print(f"🕒 Short Notice (<=30d):   {notice_30}")
    print("-" * 70)
    print(f"📈 Market Supply Tightness: {tightness}")
    print(f"❤️ Market Health:          {market_health}")
    print(f"🔥 Hiring Difficulty:      {hiring_difficulty}")
    print("-" * 70)
    print("Experience Distribution:")
    for k, v in buckets.items():
        print(f"  {k:<7}: {'■' * v} ({v})")
    print("-" * 70)
    print("Match Score Distribution:")
    for k, v in match_distribution.items():
        print(f"  {k:<7}%: {'■' * v} ({v})")
    print("-" * 70)
    print("Top Sources (Companies):")
    for name, count in top_companies:
        print(f"  - {name:<30}: {count} candidates")
    print("-" * 70)
    print("Top Locations:")
    for name, count in top_cities:
        print(f"  - {name:<30}: {count} candidates")
    print("-" * 70)
    print("Top Skills:")
    for item in top_skills[:6]:
        print(f"  - {item['name']:<30}: {item['count']} candidates")
    print("-" * 70)
    print("📝 ANALYST BRIEF:")
    print(narrative)
    print("="*70)

    # Save to JSON
    out_file = "boolean_market_analysis_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "candidates": scored,
            "summary": {
                "total": total,
                "active_30d": active_30,
                "notice_30d": notice_30,
                "in_target_range": in_target,
                "exp_distribution": buckets,
                "query": boolean_query,
                "jd_target_range": f"{min_exp}-{max_exp} years",
                "availability_score": availability_score,
                "avg_match_score": avg_match_score,
                "tightness": tightness,
                "market_health": market_health,
                "hiring_difficulty": hiring_difficulty,
                "top_companies": [{"name": c[0], "count": c[1]} for c in top_companies],
                "top_cities": [{"name": c[0], "count": c[1]} for c in top_cities],
                "top_skills": top_skills,
                "narrative": narrative
            }
        }, f, indent=2)
    print(f"✅ Market Analysis saved to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        min_exp = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 2
        max_exp = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 10
        pages = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 5
        asyncio.run(run_boolean_market_analysis(query, min_exp, max_exp, pages))
    else:
        query = input("Enter your Boolean query: ").strip()
        if not query:
            print("Query cannot be empty.")
            sys.exit(1)
        
        min_exp_str = input("Enter target minimum experience (default 2): ").strip()
        max_exp_str = input("Enter target maximum experience (default 10): ").strip()
        pages_str = input("Enter number of pages to scan (default 5): ").strip()
        
        min_exp = int(min_exp_str) if min_exp_str.isdigit() else 2
        max_exp = int(max_exp_str) if max_exp_str.isdigit() else 10
        pages = int(pages_str) if pages_str.isdigit() else 5
        
        asyncio.run(run_boolean_market_analysis(query, min_exp, max_exp, pages))
