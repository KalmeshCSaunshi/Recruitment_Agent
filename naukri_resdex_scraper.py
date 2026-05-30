from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def search_naukri_resdex(username, password, query):
    options = Options()
    options.add_argument("--headless")
    
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    results = []
    
    try:
        # 1. Login
        login_url = "https://www.naukri.com/recruit/login?msg=TO&URL=https%3A%2F%2Frecruit.naukri.com"
        print(f"Navigating to {login_url}")
        driver.get(login_url)
        
        wait = WebDriverWait(driver, 20)
        
        # Wait for and fill username
        user_field = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        user_field.send_keys(username)
        
        # Fill password
        pass_field = driver.find_element(By.ID, "passwordField")
        pass_field.send_keys(password)
        
        # Click login
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        print("Login clicked. Waiting for dashboard...")
        
        time.sleep(5) # Wait for redirect
        
        # 2. Navigate to Search (usually it redirects to dashboard)
        # We can go directly to the search page if we know the URL or find the menu
        search_url = "https://recruit.naukri.com/resdex/search"
        print(f"Navigating to {search_url}")
        driver.get(search_url)
        
        # 3. Perform Search
        # This part is complex because Resdex uses many frames/dynamic elements
        # For a first pass, we'll try to find the keywords field
        keywords_field = wait.until(EC.presence_of_element_located((By.NAME, "skill")))
        keywords_field.send_keys(query)
        
        # Click search
        search_btn = driver.find_element(By.ID, "search_btn") # Placeholder selector
        search_btn.click()
        
        print("Search executed. Waiting for results...")
        time.sleep(5)
        
        # 4. Extract (Placeholder logic - selectors vary by Resdex version)
        # We'll try to capture candidate names and links
        candidates = driver.find_elements(By.CSS_SELECTOR, ".tuple") # Sample selector
        for cand in candidates[:5]:
            try:
                name = cand.find_element(By.CSS_SELECTOR, ".name").text
                exp = cand.find_element(By.CSS_SELECTOR, ".exp").text
                results.append({"name": name, "exp": exp, "link": driver.current_url})
            except:
                continue
                
    except Exception as e:
        print(f"Error during automation: {e}")
        # Take a screenshot for debugging even in headless
        driver.save_screenshot("naukri_error.png")
    finally:
        driver.quit()
        
    return results

if __name__ == "__main__":
    # Test with provided credentials
    u = "Spoorthy.hg@supremology.com"
    p = "Spoorthy.hg@supremology.com April@2026"
    q = "(React AND Node.js) AND (\"Full Stack\" OR \"Backend\")"
    
    res = search_naukri_resdex(u, p, q)
    print(json.dumps(res, indent=2))
