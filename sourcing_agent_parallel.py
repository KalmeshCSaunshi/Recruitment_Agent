# import requests
# import json
# import urllib.parse
# import asyncio
# from playwright.async_api import async_playwright

# OLLAMA_API_URL = 'http://localhost:11434/api/generate'
# MODEL_NAME = 'llama3:latest'

# def extract_json(text):
#     if not text: return None
#     try:
#         # 1. Direct parse
#         return json.loads(text)
#     except:
#         try:
#             # 2. Find anything between { }
#             match = re.search(r'\{.*\}', text, re.DOTALL)
#             if match:
#                 clean = match.group(0)
#                 # Quick fixes
#                 clean = clean.replace("'", '"')
#                 clean = re.sub(r'(\w+):', r'"\1":', clean)
#                 return json.loads(clean)
#         except:
#             return None

# def get_search_keywords(jd):
#     import re
#     prompt = f"Identify 3-5 technical keywords and a boolean query for this JD. Return ONLY JSON: {{\"primary_keywords\": [], \"boolean_query\": \"\"}}\n\nJD: {jd[:2000]}"
#     try:
#         payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
#         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
#         data = extract_json(response.json().get('response', ''))
#         if data: return data
#     except: pass
#     return {"primary_keywords": ["Software"], "boolean_query": "Software"}

# async def perform_authenticated_search(query, min_exp=2, max_exp=8, page_num=1):
#     import os, re, random
#     PROFILE_DIR = "./naukri_profile"
#     async with async_playwright() as p:
#         context = await p.chromium.launch_persistent_context(
#             user_data_dir=PROFILE_DIR,
#             headless=True,
#             ignore_https_errors=True,
#             user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             args=[
#                 "--disable-http2", 
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 "--disable-blink-features=AutomationControlled",
#                 "--disable-infobars",
#                 "--window-position=0,0",
#                 "--window-size=1280,720",
#                 "--disable-features=IsolateOrigins,site-per-process",
#                 "--force-fieldtrials=HTTP2ScaleHolBlocking/Disabled"
#             ]
#         )
#         page = context.pages[0] if context.pages else await context.new_page()

#         try:
#             # Anti-bot protections
#             await page.add_init_script("""
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
#                     get: () => ['en-US', 'en']
#                 });
#             """)

#             print(f"Starting live search for: {query}")

#             try:
#                 # Retry logic for navigation
#                 for attempt in range(3):
#                     try:
#                         print(f"Navigation attempt {attempt+1}...")
#                         await page.goto("https://www.naukri.com", wait_until="commit", timeout=30000)
#                         await asyncio.sleep(2)
#                         await page.goto("https://resdex.naukri.com/v3", wait_until="load", timeout=60000)
#                         print("Navigated to Resdex successfully.")
#                         break
#                     except Exception as e:
#                         print(f"Attempt {attempt+1} failed: {e}")
#                         if attempt == 2: raise e
#                         await asyncio.sleep(5)
#             except Exception as e:
#                 print(f"All navigation attempts failed: {e}")
#                 try:
#                     await page.screenshot(path="final_timeout.png", timeout=5000)
#                 except:
#                     pass
#                 return []
# import requests
# import json
# import urllib.parse
# import asyncio
# from playwright.async_api import async_playwright

# OLLAMA_API_URL = 'http://localhost:11434/api/generate'
# MODEL_NAME = 'llama3:latest'

# def extract_json(text):
#     if not text: return None
#     try:
#         # 1. Direct parse
#         return json.loads(text)
#     except:
#         try:
#             # 2. Find anything between { }
#             match = re.search(r'\{.*\}', text, re.DOTALL)
#             if match:
#                 clean = match.group(0)
#                 # Quick fixes
#                 clean = clean.replace("'", '"')
#                 clean = re.sub(r'(\w+):', r'"\1":', clean)
#                 return json.loads(clean)
#         except:
#             return None

# def get_search_keywords(jd):
#     import re
#     prompt = f"Identify 3-5 technical keywords and a boolean query for this JD. Return ONLY JSON: {{\"primary_keywords\": [], \"boolean_query\": \"\"}}\n\nJD: {jd[:2000]}"
#     try:
#         payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
#         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
#         data = extract_json(response.json().get('response', ''))
#         if data: return data
#     except: pass
#     return {"primary_keywords": ["Software"], "boolean_query": "Software"}

# async def perform_authenticated_search(query, min_exp=2, max_exp=8, page_num=1):
#     import os, re, random
#     PROFILE_DIR = "./naukri_profile"
#     async with async_playwright() as p:
#         context = await p.chromium.launch_persistent_context(
#             user_data_dir=PROFILE_DIR,
#             headless=True,
#             ignore_https_errors=True,
#             user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             args=[
#                 "--disable-http2", 
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 "--disable-blink-features=AutomationControlled",
#                 "--disable-infobars",
#                 "--window-position=0,0",
#                 "--window-size=1280,720",
#                 "--disable-features=IsolateOrigins,site-per-process",
#                 "--force-fieldtrials=HTTP2ScaleHolBlocking/Disabled"
#             ]
#         )
#         page = context.pages[0] if context.pages else await context.new_page()

#         try:
#             # Anti-bot protections
#             await page.add_init_script("""
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
#                     get: () => ['en-US', 'en']
#                 });
#             """)

#             print(f"Starting live search for: {query}")

#             try:
#                 # Retry logic for navigation
#                 for attempt in range(3):
#                     try:
#                         print(f"Navigation attempt {attempt+1}...")
#                         await page.goto("https://www.naukri.com", wait_until="commit", timeout=30000)
#                         await asyncio.sleep(2)
#                         await page.goto("https://resdex.naukri.com/v3", wait_until="load", timeout=60000)
#                         print("Navigated to Resdex successfully.")
#                         break
#                     except Exception as e:
#                         print(f"Attempt {attempt+1} failed: {e}")
#                         if attempt == 2: raise e
#                         await asyncio.sleep(5)
#             except Exception as e:
#                 print(f"All navigation attempts failed: {e}")
#                 try:
#                     await page.screenshot(path="final_timeout.png", timeout=5000)
#                 except:
#                     pass
#                 return []

#             # Wait for page to be ready
#             await asyncio.sleep(5)
#             await page.screenshot(path="after_load.png")
#             print(f"DEBUG: Current URL: {page.url}")

#             if "login" in page.url.lower():
#                 print("Session expired or redirected to login. Please log in manually in the popup.")
#                 await asyncio.sleep(30) # Give time to login

#             # Try multiple ways to find the keyword input
#             keyword_selectors = [
#                 "input[placeholder*='skills']",
#                 "input[placeholder*='Keywords']",
#                 "#skill-input",
#                 ".keyword-input",
#                 "input[name='keywords']",
#                 "input[name='ezKeywordsAny']",
#                 "input[type='text']"
#             ]
            
#             search_input = None
#             for selector in keyword_selectors:
#                 try:
#                     search_input = await page.wait_for_selector(selector, timeout=5000)
#                     if search_input:
#                         print(f"Found search input: {selector}")
#                         break
#                 except:
#                     continue

#             if not search_input:
#                 print("Search input not found. Trying manual Tab + Type...")
#                 await page.keyboard.press("Tab")
#                 await page.keyboard.type(query)
#             else:
#                 await search_input.click()
#                 await asyncio.sleep(1)
#                 await search_input.fill(query)
#                 print(f"Keywords entered: {query}")

#             await asyncio.sleep(1)
#             await page.keyboard.press("Enter")

#             # Search Button (Backup)
#             try:
#                 search_btn_selectors = ["button:has-text('Search')", ".search-btn", "#search-button"]
#                 for btn in search_btn_selectors:
#                     if await page.is_visible(btn):
#                         await page.click(btn)
#                         print(f"Clicked search button: {btn}")
#                         break
#             except:
#                 pass

#             print("Waiting for results...")
#             await asyncio.sleep(10)

#             # Pagination
#             if page_num > 1:
#                 for _ in range(page_num - 1):
#                     try:
#                         await page.click("text=Next")
#                         await asyncio.sleep(5)
#                     except:
#                         break

#             # Candidate Cards
#             card_selectors = [".tuple", ".tuple-container", ".candidate-card", "[class*='tuple']"]
#             cards = []
#             for selector in card_selectors:
#                 try:
#                     cards = await page.query_selector_all(selector)
#                     if cards:
#                         print(f"Found {len(cards)} cards.")
#                         break
#                 except:
#                     pass

#             results = []
#             if not cards:
#                 print("No candidate cards found.")
#                 await page.screenshot(path="no_results.png")
#                 return []

#             for index, card in enumerate(cards[:10], start=1):
#                 try:
#                     print(f"Processing candidate {index}")
#                     name = "Candidate " + str(index)
#                     exp_text = "N/A"
#                     np_text = "N/A"
#                     profile_url = None

#                     # Try to get real name
#                     name_el = await card.query_selector(".name, .title, .tuple-name, .name-text, [class*='name']")
#                     if name_el:
#                         name = (await name_el.inner_text()).strip()

#                     # Experience
#                     try:
#                         exp_el = await card.query_selector(".exp, .tuple-exp, .exp-text, [class*='exp']")
#                         if exp_el:
#                             exp_text = (await exp_el.inner_text()).strip()
#                     except:
#                         pass

#                     # Notice Period
#                     try:
#                         np_el = await card.query_selector(".tuple-np, .np-text, [class*='notice'], [class*='np']")
#                         if np_el:
#                             np_text = (await np_el.inner_text()).strip()
#                     except:
#                         pass
#                     # Skills
#                     try:
#                         skills_el = await card.query_selector(".key-skills, .skill-container")
#                         if skills_el:
#                             context_text = (await skills_el.inner_text()).strip()
#                         else:
#                             context_text = ""
#                     except:
#                         context_text = ""

#                     # Profile URL
#                     try:
#                         link_el = await card.query_selector("a")
#                         if link_el:
#                             profile_url = await link_el.get_attribute("href")
#                             if profile_url and not profile_url.startswith("http"):
#                                 profile_url = "https://resdex.naukri.com" + profile_url
#                     except:
#                         pass

#                     email_text = "Hidden"
#                     phone_text = "Hidden"

#                     # Results Collection
#                     results.append({
#                         "name": name,
#                         "exp": exp_text,
#                         "context": context_text,
#                         "notice_period": np_text,
#                         "phone": phone_text,
#                         "email": email_text,
#                         "link": profile_url or page.url
#                     })

#                     print(f"Extracted: {name}")
#                     await asyncio.sleep(2)

#                 except Exception as e:
#                     print(f"Error extracting candidate {index}: {e}")

#             print(f"Successfully extracted {len(results)} leads.")
#             return {
#                 "leads": results,
#                 "final_url": page.url
#             }

#         except Exception as e:
#             print(f"Live search error: {e}")
#             try:
#                 await page.screenshot(path="live_search_error.png")
#             except:
#                 pass
#             return [{"error": f"Search failed: {str(e)}"}]

#         finally:
#             await context.close()

# def simulate_naukri_search(data):
#     primary = data.get('primary_keywords', [])
#     secondary = data.get('secondary_keywords', [])
#     boolean = data.get('boolean_query', "")
    
#     # We'll return the keywords so the frontend knows what we searched for
#     return {
#         "keywords_used": primary + secondary,
#         "boolean_query": boolean,
#         "simulated_leads": [] # Will be populated by the live search in app.py
#     }# import requests
# import json
# import urllib.parse
# import asyncio
# from playwright.async_api import async_playwright

# OLLAMA_API_URL = 'http://localhost:11434/api/generate'
# MODEL_NAME = 'llama3:latest'

# def extract_json(text):
#     if not text: return None
#     try:
#         # 1. Direct parse
#         return json.loads(text)
#     except:
#         try:
#             # 2. Find anything between { }
#             match = re.search(r'\{.*\}', text, re.DOTALL)
#             if match:
#                 clean = match.group(0)
#                 # Quick fixes
#                 clean = clean.replace("'", '"')
#                 clean = re.sub(r'(\w+):', r'"\1":', clean)
#                 return json.loads(clean)
#         except:
#             return None

# def get_search_keywords(jd):
#     import re
#     prompt = f"Identify 3-5 technical keywords and a boolean query for this JD. Return ONLY JSON: {{\"primary_keywords\": [], \"boolean_query\": \"\"}}\n\nJD: {jd[:2000]}"
#     try:
#         payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
#         response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
#         data = extract_json(response.json().get('response', ''))
#         if data: return data
#     except: pass
#     return {"primary_keywords": ["Software"], "boolean_query": "Software"}

# async def perform_authenticated_search(query, min_exp=2, max_exp=8, page_num=1):
#     import os, re, random
#     PROFILE_DIR = "./naukri_profile"
#     async with async_playwright() as p:
#         context = await p.chromium.launch_persistent_context(
#             user_data_dir=PROFILE_DIR,
#             headless=True,
#             ignore_https_errors=True,
#             user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             args=[
#                 "--disable-http2", 
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 "--disable-blink-features=AutomationControlled",
#                 "--disable-infobars",
#                 "--window-position=0,0",
#                 "--window-size=1280,720",
#                 "--disable-features=IsolateOrigins,site-per-process",
#                 "--force-fieldtrials=HTTP2ScaleHolBlocking/Disabled"
#             ]
#         )
#         page = context.pages[0] if context.pages else await context.new_page()

#         try:
#             # Anti-bot protections
#             await page.add_init_script("""
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
#                     get: () => ['en-US', 'en']
#                 });
#             """)

#             print(f"Starting live search for: {query}")

#             try:
#                 # Retry logic for navigation
#                 for attempt in range(3):
#                     try:
#                         print(f"Navigation attempt {attempt+1}...")
#                         await page.goto("https://www.naukri.com", wait_until="commit", timeout=30000)
#                         await asyncio.sleep(2)
#                         await page.goto("https://resdex.naukri.com/v3", wait_until="load", timeout=60000)
#                         print("Navigated to Resdex successfully.")
#                         break
#                     except Exception as e:
#                         print(f"Attempt {attempt+1} failed: {e}")
#                         if attempt == 2: raise e
#                         await asyncio.sleep(5)
#             except Exception as e:
#                 print(f"All navigation attempts failed: {e}")
#                 try:
#                     await page.screenshot(path="final_timeout.png", timeout=5000)
#                 except:
#                     pass
#                 return []

#             # Wait for page to be ready
#             await asyncio.sleep(5)
#             await page.screenshot(path="after_load.png")
#             print(f"DEBUG: Current URL: {page.url}")

#             if "login" in page.url.lower():
#                 print("Session expired or redirected to login. Please log in manually in the popup.")
#                 await asyncio.sleep(30) # Give time to login

#             # Try multiple ways to find the keyword input
#             keyword_selectors = [
#                 "input[placeholder*='skills']",
#                 "input[placeholder*='Keywords']",
#                 "#skill-input",
#                 ".keyword-input",
#                 "input[name='keywords']",
#                 "input[name='ezKeywordsAny']",
#                 "input[type='text']"
#             ]
            
#             search_input = None
#             for selector in keyword_selectors:
#                 try:
#                     search_input = await page.wait_for_selector(selector, timeout=5000)
#                     if search_input:
#                         print(f"Found search input: {selector}")
#                         break
#                 except:
#                     continue

#             if not search_input:
#                 print("Search input not found. Trying manual Tab + Type...")
#                 await page.keyboard.press("Tab")
#                 await page.keyboard.type(query)
#             else:
#                 await search_input.click()
#                 await asyncio.sleep(1)
#                 await search_input.fill(query)
#                 print(f"Keywords entered: {query}")

#             await asyncio.sleep(1)
#             await page.keyboard.press("Enter")

#             # Search Button (Backup)
#             try:
#                 search_btn_selectors = ["button:has-text('Search')", ".search-btn", "#search-button"]
#                 for btn in search_btn_selectors:
#                     if await page.is_visible(btn):
#                         await page.click(btn)
#                         print(f"Clicked search button: {btn}")
#                         break
#             except:
#                 pass

#             print("Waiting for results...")
#             await asyncio.sleep(10)

#             # Pagination
#             if page_num > 1:
#                 for _ in range(page_num - 1):
#                     try:
#                         await page.click("text=Next")
#                         await asyncio.sleep(5)
#                     except:
#                         break

#             # Candidate Cards
#             card_selectors = [".tuple", ".tuple-container", ".candidate-card", "[class*='tuple']"]
#             cards = []
#             for selector in card_selectors:
#                 try:
#                     cards = await page.query_selector_all(selector)
#                     if cards:
#                         print(f"Found {len(cards)} cards.")
#                         break
#                 except:
#                     pass

#             results = []
#             if not cards:
#                 print("No candidate cards found.")
#                 await page.screenshot(path="no_results.png")
#                 return []

#             for index, card in enumerate(cards[:10], start=1):
#                 try:
#                     print(f"Processing candidate {index}")
#                     name = "Candidate " + str(index)
#                     exp_text = "N/A"
#                     np_text = "N/A"
#                     profile_url = None

#                     # Try to get real name
#                     name_el = await card.query_selector(".name, .title, .tuple-name, .name-text, [class*='name']")
#                     if name_el:
#                         name = (await name_el.inner_text()).strip()

#                     # Experience
#                     try:
#                         exp_el = await card.query_selector(".exp, .tuple-exp, .exp-text, [class*='exp']")
#                         if exp_el:
#                             exp_text = (await exp_el.inner_text()).strip()
#                     except:
#                         pass

#                     # Notice Period
#                     try:
#                         np_el = await card.query_selector(".tuple-np, .np-text, [class*='notice'], [class*='np']")
#                         if np_el:
#                             np_text = (await np_el.inner_text()).strip()
#                     except:
#                         pass
#                     # Skills
#                     try:
#                         skills_el = await card.query_selector(".key-skills, .skill-container")
#                         if skills_el:
#                             context_text = (await skills_el.inner_text()).strip()
#                         else:
#                             context_text = ""
#                     except:
#                         context_text = ""

#                     # Profile URL
#                     try:
#                         link_el = await card.query_selector("a")
#                         if link_el:
#                             profile_url = await link_el.get_attribute("href")
#                             if profile_url and not profile_url.startswith("http"):
#                                 profile_url = "https://resdex.naukri.com" + profile_url
#                     except:
#                         pass

#                     email_text = "Hidden"
#                     phone_text = "Hidden"

#                     # Results Collection
#                     results.append({
#                         "name": name,
#                         "exp": exp_text,
#                         "context": context_text,
#                         "notice_period": np_text,
#                         "phone": phone_text,
#                         "email": email_text,
#                         "link": profile_url or page.url
#                     })

#                     print(f"Extracted: {name}")
#                     await asyncio.sleep(2)

#                 except Exception as e:
#                     print(f"Error extracting candidate {index}: {e}")

#             print(f"Successfully extracted {len(results)} leads.")
#             return {
#                 "leads": results,
#                 "final_url": page.url
#             }

#         except Exception as e:
#             print(f"Live search error: {e}")
#             try:
#                 await page.screenshot(path="live_search_error.png")
#             except:
#                 pass
#             return [{"error": f"Search failed: {str(e)}"}]

#         finally:
#             await context.close()

# def simulate_naukri_search(data):
#     primary = data.get('primary_keywords', [])
#     secondary = data.get('secondary_keywords', [])
#     boolean = data.get('boolean_query', "")
    
#     # We'll return the keywords so the frontend knows what we searched for
#     return {
#         "keywords_used": primary + secondary,
#         "boolean_query": boolean,
#         "simulated_leads": [] # Will be populated by the live search in app.py
#     }




#             # Wait for page to be ready
#             await asyncio.sleep(5)
#             await page.screenshot(path="after_load.png")
#             print(f"DEBUG: Current URL: {page.url}")

#             if "login" in page.url.lower():
#                 print("Session expired or redirected to login. Please log in manually in the popup.")
#                 await asyncio.sleep(30) # Give time to login

#             # Try multiple ways to find the keyword input
#             keyword_selectors = [
#                 "input[placeholder*='skills']",
#                 "input[placeholder*='Keywords']",
#                 "#skill-input",
#                 ".keyword-input",
#                 "input[name='keywords']",
#                 "input[name='ezKeywordsAny']",
#                 "input[type='text']"
#             ]
            
#             search_input = None
#             for selector in keyword_selectors:
#                 try:
#                     search_input = await page.wait_for_selector(selector, timeout=5000)
#                     if search_input:
#                         print(f"Found search input: {selector}")
#                         break
#                 except:
#                     continue

#             if not search_input:
#                 print("Search input not found. Trying manual Tab + Type...")
#                 await page.keyboard.press("Tab")
#                 await page.keyboard.type(query)
#             else:
#                 await search_input.click()
#                 await asyncio.sleep(1)
#                 await search_input.fill(query)
#                 print(f"Keywords entered: {query}")

#             await asyncio.sleep(1)
#             await page.keyboard.press("Enter")

#             # Search Button (Backup)
#             try:
#                 search_btn_selectors = ["button:has-text('Search')", ".search-btn", "#search-button"]
#                 for btn in search_btn_selectors:
#                     if await page.is_visible(btn):
#                         await page.click(btn)
#                         print(f"Clicked search button: {btn}")
#                         break
#             except:
#                 pass

#             print("Waiting for results...")
#             await asyncio.sleep(10)

#             # Pagination
#             if page_num > 1:
#                 for _ in range(page_num - 1):
#                     try:
#                         await page.click("text=Next")
#                         await asyncio.sleep(5)
#                     except:
#                         break

#             # Candidate Cards
#             card_selectors = [".tuple", ".tuple-container", ".candidate-card", "[class*='tuple']"]
#             cards = []
#             for selector in card_selectors:
#                 try:
#                     cards = await page.query_selector_all(selector)
#                     if cards:
#                         print(f"Found {len(cards)} cards.")
#                         break
#                 except:
#                     pass

#             results = []
#             if not cards:
#                 print("No candidate cards found.")
#                 await page.screenshot(path="no_results.png")
#                 return []

#             for index, card in enumerate(cards[:10], start=1):
#                 try:
#                     print(f"Processing candidate {index}")
#                     name = "Candidate " + str(index)
#                     exp_text = "N/A"
#                     np_text = "N/A"
#                     profile_url = None

#                     # Try to get real name
#                     name_el = await card.query_selector(".name, .title, .tuple-name, .name-text, [class*='name']")
#                     if name_el:
#                         name = (await name_el.inner_text()).strip()

#                     # Experience
#                     try:
#                         exp_el = await card.query_selector(".exp, .tuple-exp, .exp-text, [class*='exp']")
#                         if exp_el:
#                             exp_text = (await exp_el.inner_text()).strip()
#                     except:
#                         pass

#                     # Notice Period
#                     try:
#                         np_el = await card.query_selector(".tuple-np, .np-text, [class*='notice'], [class*='np']")
#                         if np_el:
#                             np_text = (await np_el.inner_text()).strip()
#                     except:
#                         pass
#                     # Skills
#                     try:
#                         skills_el = await card.query_selector(".key-skills, .skill-container")
#                         if skills_el:
#                             context_text = (await skills_el.inner_text()).strip()
#                         else:
#                             context_text = ""
#                     except:
#                         context_text = ""

#                     # Profile URL
#                     try:
#                         link_el = await card.query_selector("a")
#                         if link_el:
#                             profile_url = await link_el.get_attribute("href")
#                             if profile_url and not profile_url.startswith("http"):
#                                 profile_url = "https://resdex.naukri.com" + profile_url
#                     except:
#                         pass

#                     email_text = "Hidden"
#                     phone_text = "Hidden"

#                     # Results Collection
#                     results.append({
#                         "name": name,
#                         "exp": exp_text,
#                         "context": context_text,
#                         "notice_period": np_text,
#                         "phone": phone_text,
#                         "email": email_text,
#                         "link": profile_url or page.url
#                     })

#                     print(f"Extracted: {name}")
#                     await asyncio.sleep(2)

#                 except Exception as e:
#                     print(f"Error extracting candidate {index}: {e}")

#             print(f"Successfully extracted {len(results)} leads.")
#             return {
#                 "leads": results,
#                 "final_url": page.url
#             }

#         except Exception as e:
#             print(f"Live search error: {e}")
#             try:
#                 await page.screenshot(path="live_search_error.png")
#             except:
#                 pass
#             return [{"error": f"Search failed: {str(e)}"}]

#         finally:
#             await context.close()

# def simulate_naukri_search(data):
#     primary = data.get('primary_keywords', [])
#     secondary = data.get('secondary_keywords', [])
#     boolean = data.get('boolean_query', "")
    
#     # We'll return the keywords so the frontend knows what we searched for
#     return {
#         "keywords_used": primary + secondary,
#         "boolean_query": boolean,
#         "simulated_leads": [] # Will be populated by the live search in app.py
#     }






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

def get_search_keywords(jd):
    prompt = f"""
    You are a Senior Technical Sourcer. Analyze the following Job Description and extract high-precision search parameters for Naukri.com.
    
    TASKS:
    1. Extract the required Experience Range (Min/Max years).
    2. Create a HIGH-PRECISION Boolean query (max 200 chars). Combine 3-4 MUST-HAVE technical skills with 'AND'.
    3. Identify 5 core technical keywords.
    
    Return JSON:
    - primary_keywords: [list of 5 skills]
    - boolean_query: "Skill1" AND "Skill2" AND "Skill3"
    - min_exp: number (e.g. 3)
    - max_exp: number (e.g. 8)
    
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
        return json.loads(response.json().get('response'))
    except Exception as e:
        print(f"Error getting keywords: {e}")
        return {"primary_keywords": ["Software Engineer"], "secondary_keywords": [], "boolean_query": "Software Engineer"}

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

async def perform_authenticated_search(query, min_exp=2, max_exp=8, page_num=1):
    experience_range = (min_exp, max_exp)
    async with async_playwright() as p:
        context = None
        try:
            # Auto-heal: delete stale Chromium process singleton lock files if present
            import os
            lock_file = os.path.join(PROFILE_DIR, "SingletonLock")
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
                
            print(f"Launching Chromium: path={exec_path}, headless={headless_mode}", flush=True)
            
            context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
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

            # Anti-bot protections to prevent Naukri from instantly refreshing/invalidating the automated page
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
            
            
            # 1. Turn on Boolean toggle explicitly for v3
            if "AND" in query or "OR" in query:
                print("Enabling Boolean search toggle...")
                try:
                    # Specific selector for Resdex v3 Boolean toggle
                    boolean_toggle = await page.wait_for_selector("span:has-text('Boolean'), .switch-label", timeout=5000)
                    if boolean_toggle:
                        await boolean_toggle.click()
                        print("Boolean toggle clicked.")
                        await page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"Could not click Boolean toggle: {e}")

            # 2. Fill Keywords
            skill_input = await page.wait_for_selector("input[name='ezKeywordsAny']", timeout=10000)
            if skill_input:
                await skill_input.fill(query)
                print(f"Keywords entered: {query}")
                
                # 3. Add Experience Filter from JD
                try:
                    print(f"Setting Experience Filter: {min_exp} to {max_exp} years...")
                    min_field = await page.wait_for_selector("input[placeholder*='Min'], #minExp, [name='minExp']", timeout=5000)
                    if min_field:
                        await min_field.fill(str(min_exp))
                    
                    max_field = await page.wait_for_selector("input[placeholder*='Max'], #maxExp, [name='maxExp']", timeout=5000)
                    if max_field:
                        await max_field.fill(str(max_exp))
                except:
                    print("Could not set experience filter.")

                # 3. Apply Notice Period (30 Days)
                # Resdex v3 often has filters on the left or in 'More Filters'
                try:
                    await page.click("text=Notice Period")
                    await page.click("text=30 Days")
                except: pass

                # 3.5 Apply Activity Filter (Active in Last 30 Days / 1 Month)
                try:
                    print("Applying Activity Filter: Active in last 30 days...", flush=True)
                    # Look for Active in / Activity selector
                    active_dropdown = await page.wait_for_selector("input[placeholder*='Active in'], [name='activeIn'], select[name*='active'], select[name*='activity']", timeout=5000)
                    if active_dropdown:
                        await active_dropdown.click()
                        await page.wait_for_timeout(1000)
                        option = await page.wait_for_selector("text=30 Days, text=1 Month, [data-val='30']", timeout=3000)
                        if option:
                            await option.click()
                            print("Successfully selected '30 Days' / '1 Month' activity filter.", flush=True)
                except Exception as act_err:
                    print(f"Could not apply Active in 30 Days filter on form: {act_err}", flush=True)

                # 4. Apply Salary Filter (Exp * 3)
                # We'll try to find the salary input
                avg_exp = (experience_range[0] + experience_range[1]) / 2
                target_salary = int(avg_exp * 3)
                print(f"Applying Salary Filter: {target_salary} LPA")
                # Selector for salary dropdown/input
                
                # Click Search
                search_btn = await page.query_selector("button:has-text('Search candidates')")
                if search_btn: await search_btn.click()
                else: await page.keyboard.press("Enter")
                
                await page.wait_for_load_state("networkidle")

                # Apply "Last Active 30 Days" filter from results page sidebar if not already applied
                try:
                    print("Checking for Activity filter in search results sidebar...", flush=True)
                    active_filter = await page.wait_for_selector(
                        "text=Last 30 Days, text=Active in last 30 Days, text=Active in 1 month, text=1 Month", 
                        timeout=5000
                    )
                    if active_filter:
                        print("Clicking 'Last 30 Days' Activity filter in sidebar...", flush=True)
                        await active_filter.click()
                        await page.wait_for_timeout(5000)
                        print("Activity filter applied successfully.", flush=True)
                except Exception as filter_err:
                    print(f"Activity filter sidebar element not found or already applied: {filter_err}", flush=True)
                
                # Handle Pagination if page_num > 1
                if page_num > 1:
                    for _ in range(page_num - 1):
                        await page.click("text=Next")
                        await page.wait_for_timeout(5000)

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

                # Gather basic card information first
                candidates_to_scrape = []
                for card in cards:
                    try:
                        if len(candidates_to_scrape) >= 10:
                            print("Collected maximum of 10 active candidates. Stopping card inspection loop.", flush=True)
                            break
                        name_el = await card.query_selector(".name, .title, [class*='name']")
                        name = await name_el.inner_text() if name_el else "Unknown Candidate"
                        
                        link_el = await card.query_selector("a[href*='profile'], .name a")
                        profile_url = await link_el.get_attribute("href") if link_el else None
                        if profile_url and not profile_url.startswith("http"):
                            profile_url = "https://resdex.naukri.com" + profile_url
                            
                        exp_el = await card.query_selector(".exp, [class*='exp']")
                        exp_text = await exp_el.inner_text() if exp_el else "N/A"
                        
                        skills_el = await card.query_selector(".key-skills, .may-know, .skill-container")
                        context_text = await skills_el.inner_text() if skills_el else ""

                        np_el = await card.query_selector("span:has-text('days'), span:has-text('month'), [class*='notice']")
                        np_text = await np_el.inner_text() if np_el else "N/A"
                        
                        # Check candidate activity level from DOM
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

                        if activity_text:
                            print(f"Candidate {name} activity status: '{activity_text}'", flush=True)
                            if not is_candidate_active_in_30_days(activity_text):
                                print(f"⏩ SKIPPING candidate {name} - inactive for over 30 days.", flush=True)
                                continue

                        candidates_to_scrape.append({
                            "name": name,
                            "profile_url": profile_url,
                            "exp": exp_text,
                            "context": context_text,
                            "notice_period": np_text
                        })
                    except Exception as e:
                        print(f"Error reading card: {e}")

                # Dedicated helper to scrape a single profile page concurrently
                async def scrape_single_profile(candidate):
                    name = candidate["name"]
                    profile_url = candidate["profile_url"]
                    if not profile_url:
                        return ""
                    
                    print(f"Opening profile for {name} to scrape experience concurrently...", flush=True)
                    profile_page = await context.new_page()
                    try:
                        # 30 seconds max timeout, wait for domcontentloaded
                        await profile_page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                        await profile_page.wait_for_timeout(2000)
                        
                        # 1. Extract job descriptions from all Work Experience cards
                        job_descs = []
                        desc_els = await profile_page.query_selector_all("div.work-exp-card div.desc")
                        for desc_el in desc_els:
                            txt = await desc_el.inner_text()
                            if txt:
                                job_descs.append(txt.strip())
                        
                        # Include designations as part of experience context
                        desig_els = await profile_page.query_selector_all("div.work-exp-card div.desig")
                        for desig_el in desig_els:
                            txt = await desig_el.inner_text()
                            if txt:
                                job_descs.append(txt.strip())

                        # 2. Extract dedicated projects section (if present)
                        project_descs = []
                        proj_selectors = [".cv-project", ".project-details", "div[class*='project']"]
                        for sel in proj_selectors:
                            proj_els = await profile_page.query_selector_all(sel)
                            for proj_el in proj_els:
                                txt = await proj_el.inner_text()
                                if txt and len(txt.strip()) > 20:
                                    project_descs.append(txt.strip())
                        
                        # Combine all text
                        combined_texts = []
                        if job_descs:
                            combined_texts.append("=== WORK EXPERIENCE ===")
                            combined_texts.extend(job_descs)
                        if project_descs:
                            combined_texts.append("=== PROJECTS ===")
                            combined_texts.extend(project_descs)
                        
                        experience_text = "\n\n".join(combined_texts)
                        print(f"Successfully scraped {len(job_descs)} job cards and {len(project_descs)} projects for {name}.", flush=True)
                        return experience_text
                    except Exception as scrape_err:
                        print(f"Could not scrape DOM profile for {name}: {scrape_err}", flush=True)
                        return ""
                    finally:
                        await profile_page.close()

                # Process in parallel batches of 3 to maximize speed and prevent rate-limiting or heavy resource usage
                batch_size = 3
                for idx in range(0, len(candidates_to_scrape), batch_size):
                    batch = candidates_to_scrape[idx:idx+batch_size]
                    
                    async def process_candidate(candidate):
                        try:
                            experience_text = await scrape_single_profile(candidate)
                            results.append({
                                "name": candidate["name"].strip(),
                                "exp": candidate["exp"].strip(),
                                "context": candidate["context"].strip(),
                                "notice_period": candidate["notice_period"].strip(),
                                "phone": "Hidden",
                                "email": "Hidden",
                                "link": candidate["profile_url"] or page.url,
                                "experience_text": experience_text
                            })
                        except Exception as p_err:
                            print(f"Error processing batch candidate {candidate['name']}: {p_err}", flush=True)
                    
                    tasks = [process_candidate(c) for c in batch]
                    await asyncio.gather(*tasks)
                
                print(f"Successfully extracted {len(results)} leads.")
                return results
            return []
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
    boolean = data.get('boolean_query', "")
    
    # We'll return the keywords so the frontend knows what we searched for
    return {
        "keywords_used": primary + secondary,
        "boolean_query": boolean,
        "simulated_leads": [] # Will be populated by the live search in app.py
    }