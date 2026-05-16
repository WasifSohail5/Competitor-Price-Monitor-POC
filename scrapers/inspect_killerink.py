import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import random

def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.maximize_window()
    return driver

def solve_cloudflare(driver, max_retries=5):
    for attempt in range(max_retries):
        time.sleep(3)
        page = driver.page_source.lower()
        if "checking your browser" in page or "just a moment" in page:
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        elems = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"], label, span')
                        for elem in elems:
                            if elem.is_displayed():
                                ActionChains(driver).move_to_element(elem).pause(random.uniform(0.3, 0.7)).click().perform()
                                time.sleep(2)
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
            except:
                pass
        else:
            print("✅ Cloudflare passed!")
            return True
    return False

driver = setup_driver()
driver.get("https://www.killerinktattoo.co.uk/tattoo-ink")
time.sleep(3)
solve_cloudflare(driver)
time.sleep(3)

# HTML save karo
html = driver.page_source
with open("logs/killerink.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ HTML saved!")

# Classes inspect karo
soup = BeautifulSoup(html, "html.parser")
print("\n--- Product related classes ---")
seen = set()
for tag in soup.find_all(class_=True):
    for cls in tag.get("class", []):
        key = f"{tag.name}.{cls}"
        if key not in seen and any(x in cls.lower() for x in ["product", "card", "item", "price", "name", "title", "grid"]):
            seen.add(key)
            print(f"  {key}")

input("\nPress Enter to close...")
driver.quit()