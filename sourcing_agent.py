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
#                         print("Navigatedboolean to Resdex successfully.")
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
    
    lines = [line.strip() for line in card_txt.split("\n") if line.strip()]
    
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
        # 1. First, check if the toggle is explicitly OFF
        off_toggle = await page.query_selector("label.boolean-toggle.off, label.ts-switch.off")
        if off_toggle:
            print("📊 Boolean toggle is currently OFF. Clicking to turn it ON...", flush=True)
            await off_toggle.click()
            await page.wait_for_timeout(2000)
            return True
            
        # 2. Check if it's already ON
        on_toggle = await page.query_selector("label.boolean-toggle.on, label.ts-switch.on")
        if on_toggle:
            print("📊 Boolean toggle is ALREADY ON. No click needed.", flush=True)
            return True
            
        # 3. Fallback: check by text label
        lbl = await page.query_selector(".toggle-switch-label")
        if lbl:
            txt = (await lbl.inner_text()).lower()
            if "boolean off" in txt:
                print("📊 Boolean toggle is OFF (by text label). Clicking...", flush=True)
                await lbl.click()
                await page.wait_for_timeout(2000)
                return True
            elif "boolean on" in txt:
                print("📊 Boolean toggle is ALREADY ON (by text label).", flush=True)
                return True
                
        # 4. Deep fallback: click if the checkbox is not checked
        cb = await page.query_selector("input[name='toggleSwitch']")
        if cb:
            is_checked = await cb.is_checked()
            if not is_checked:
                print("📊 Checkbox is unchecked. Clicking toggle switch wrapper...", flush=True)
                wrapper = await page.query_selector(".toggle-switch-wrap")
                if wrapper:
                    await wrapper.click()
                    await page.wait_for_timeout(2000)
                    return True
    except Exception as e:
        print(f"📊 Error ensuring Boolean toggle is ON: {e}", flush=True)
    return False

async def market_scan_search(query, min_exp=2, max_exp=10, max_pages=5):
    """
    Fast market scan — reads card data across multiple pages WITHOUT opening profiles.
    Uses the SAME UI flow as perform_authenticated_search (persistent context + boolean toggle).
    Returns ALL candidates found for Excel export.
    """
    all_candidates = []

    # Parse query parameter (could be dictionary of separate keywords or string)
    mandatory = ""
    optional = ""
    boolean_query = ""
    if isinstance(query, dict):
        mandatory = query.get('mandatory_keywords', '')
        optional = query.get('optional_keywords', '')
        boolean_query = query.get('boolean_query', '')
        
        # Safe Fallback: if boolean_query is empty, construct it dynamically!
        if not boolean_query:
            if mandatory and optional:
                opt_terms = [t.strip() for t in optional.split(",") if t.strip()]
                opt_joined = " OR ".join(opt_terms)
                boolean_query = f"({mandatory}) AND ({opt_joined})"
            elif mandatory:
                boolean_query = mandatory
            else:
                boolean_query = " ".join(query.get('primary_keywords', []))
    else:
        boolean_query = query

    async with async_playwright() as p:
        # Auto-heal stale lock file
        lock_file = os.path.join(PROFILE_DIR, "SingletonLock")
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

        print(f"📊 Market scan: Launching Chromium (headless={headless_mode})...", flush=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
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

            # Step 2 & 3: Ensure Boolean toggle is ON and fill the VISIBLE search box with Boolean query
            await ensure_boolean_toggle_on(page)

            skill_input = None
            for selector in [
                "input[name='boolKeywords']:visible", 
                "input[name='booleanKeywordsAny']:visible",
                "input[name='ezKeywordsAny']:visible",
                "textarea:visible", 
                "input[name='boolKeywords']", 
                "input[name='booleanKeywordsAny']",
                "input[name='ezKeywordsAny']"
            ]:
                try:
                    el = await page.wait_for_selector(selector, timeout=2000)
                    if el and await el.is_visible():
                        skill_input = el
                        print(f"📊 Market scan: Found active visible search input using: {selector}", flush=True)
                        break
                except Exception:
                    pass

            if not skill_input:
                # Comprehensive fallback loop
                for fallback_sel in [
                    "input[name='boolKeywords']", 
                    "input[name='booleanKeywordsAny']", 
                    "input[name='ezKeywordsAny']", 
                    "textarea"
                ]:
                    try:
                        el = await page.wait_for_selector(fallback_sel, timeout=2000)
                        if el:
                            skill_input = el
                            print(f"📊 Market scan: Found input via fallback selector: {fallback_sel}", flush=True)
                            break
                    except Exception:
                        pass

            if not skill_input:
                print("📊 Market scan: Could not find search input.", flush=True)
                return []

            await skill_input.fill(boolean_query)
            print(f"📊 Market scan: Query entered: {boolean_query}", flush=True)

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
                            await next_btn.click()
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


def get_search_keywords(jd, for_market_analysis=False):
    if for_market_analysis:
        prompt = f"""
        You are a Senior Technical Sourcer building a Naukri Resdex search query for a WIDE-FUNNEL Talent Market Analysis.
        
        STRATEGY: We want to capture the overall market size and distribution for this specific domain. Therefore, we only want the CORE ROLE DOMAIN as the single mandatory skill. Specific tools, sub-skills, and validation terms must be completely OPTIONAL to ensure a wide but highly accurate candidate pool.
        
        TASKS:
        1. Identify the CORE ROLE DOMAIN or primary role title of this job. This will be the ONLY mandatory skill.
           CRITICAL RULE: The mandatory skill MUST represent the core domain of the job. Do NOT use broad or generic multi-industry terms unless they are the primary focus of the role.
        2. Identify 4-5 optional related skills (tools, validation techniques, protocols).
        3. Build a fallback boolean_query in this exact pattern:
           (core_role_domain) AND (optional_1 OR optional_2 OR optional_3 OR optional_4)
        
        4. Keep total boolean_query under 250 characters.
        5. Extract experience range from the JD.
        6. List 5 primary keywords separately.

        Return ONLY valid JSON:
        {{
            "primary_keywords": ["skill1", "skill2", "skill3", "skill4", "skill5"],
            "mandatory_keywords": "core_role_domain",
            "optional_keywords": "opt1, opt2, opt3, opt4",
            "boolean_query": "(core_role_domain) AND (opt1 OR opt2 OR opt3 OR opt4)",
            "min_exp": 2,
            "max_exp": 8
        }}

        JD:
        {jd}
        """
    else:
        prompt = f"""
        You are a Senior Technical Sourcer building a Naukri Resdex search query.
        
        STRATEGY: Use a WIDE FUNNEL approach to get maximum candidates. Our backend AI will rank and filter them.

        TASKS:
        1. Identify the TOP 2 absolutely critical skills (without which the candidate cannot do this job at all). These will be MANDATORY.
        2. Identify 4-5 other important skills. These will be OPTIONAL.
        3. Build a fallback boolean_query in this exact pattern:
           (mandatory_skill_1) AND (mandatory_skill_2) AND (optional_1 OR optional_2 OR optional_3 OR optional_4)
        
        4. Keep total boolean_query under 250 characters.
        5. Extract experience range from the JD.
        6. List 5 primary keywords separately.

        Return ONLY valid JSON:
        {{
            "primary_keywords": ["skill1", "skill2", "skill3", "skill4", "skill5"],
            "mandatory_keywords": "mandatory_skill_1, mandatory_skill_2",
            "optional_keywords": "opt1, opt2, opt3, opt4",
            "boolean_query": "(mandatory1) AND (mandatory2) AND (opt1 OR opt2 OR opt3 OR opt4)",
            "min_exp": 2,
            "max_exp": 8
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
        return json.loads(response.json().get('response'))
    except Exception as e:
        print(f"Error getting keywords: {e}")
        return {
            "primary_keywords": ["Software Engineer"],
            "mandatory_keywords": "Software Engineer",
            "optional_keywords": "",
            "boolean_query": "Software Engineer",
            "min_exp": 2,
            "max_exp": 8
        }


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
    
    # Parse query parameter (could be dictionary of separate keywords or string)
    mandatory = ""
    optional = ""
    boolean_query = ""
    if isinstance(query, dict):
        mandatory = query.get('mandatory_keywords', '')
        optional = query.get('optional_keywords', '')
        boolean_query = query.get('boolean_query', '')
        
        # Safe Fallback: if boolean_query is empty, construct it dynamically!
        if not boolean_query:
            if mandatory and optional:
                opt_terms = [t.strip() for t in optional.split(",") if t.strip()]
                opt_joined = " OR ".join(opt_terms)
                boolean_query = f"({mandatory}) AND ({opt_joined})"
            elif mandatory:
                boolean_query = mandatory
            else:
                boolean_query = " ".join(query.get('primary_keywords', []))
    else:
        boolean_query = query

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
            
            
            # 1 & 2. Ensure Boolean toggle is ON and fill the VISIBLE search box with Boolean query
            await ensure_boolean_toggle_on(page)

            skill_input = None
            for selector in ["input[name='boolKeywords']:visible", "input[name='boolKeywords']:visible", "textarea:visible", "input[name='boolKeywords']", "input[name='boolKeywords']"]:
                try:
                    el = await page.wait_for_selector(selector, timeout=3000)
                    if el and await el.is_visible():
                        skill_input = el
                        print(f"Found active visible search input using: {selector}", flush=True)
                        break
                except Exception:
                    pass

            if not skill_input:
                # Direct fallback
                skill_input = await page.wait_for_selector("input[name='boolKeywords']", timeout=5000)

            if skill_input:
                await skill_input.fill(boolean_query)
                print(f"Keywords entered: {boolean_query}")
                
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
                                await next_btn.scroll_into_view_if_needed()
                            except: pass
                            await next_btn.click()
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
            return {"deep_results": [], "other_candidates": []}
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