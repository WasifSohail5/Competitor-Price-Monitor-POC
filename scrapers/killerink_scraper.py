import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import re
import time
import random
import html as html_module
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from database.db import (insert_product, insert_price_history,
                         insert_change_log, get_latest_price,
                         start_scrape_run, complete_scrape_run)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SITE_KEY = "killerink"
BASE_URL = "https://www.killerinktattoo.co.uk"

# Leaf category URLs — 339 categories
CATEGORY_URLS = [
    "https://www.killerinktattoo.co.uk/tattoo-ink/intenze-tattoo-ink/all",
    "https://www.killerinktattoo.co.uk/tattoo-ink/kuro-sumi-tattoo-ink/kuro-sumi-black-and-greywash",
    "https://www.killerinktattoo.co.uk/tattoo-ink/kuro-sumi-tattoo-ink/kuro-sumi-imperial-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/world-famous-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/eternal-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/fusion-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/dynamic-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/panthera-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/carbon-black-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/black-tattoo-ink",
    "https://www.killerinktattoo.co.uk/tattoo-ink/complete-tattoo-ink-sets",
    "https://www.killerinktattoo.co.uk/tattoo-machines",
    "https://www.killerinktattoo.co.uk/tattoo-cartridges/cheyenne-cartridges/cheyenne-hawk-cartridges",
    "https://www.killerinktattoo.co.uk/tattoo-cartridges/kwadron-cartridges/round-liner",
    "https://www.killerinktattoo.co.uk/tattoo-cartridges/kwadron-cartridges/round-shader",
    "https://www.killerinktattoo.co.uk/tattoo-cartridges/kwadron-cartridges/magnum",
    "https://www.killerinktattoo.co.uk/tattoo-cartridges/killer-ink-cartridges",
    "https://www.killerinktattoo.co.uk/tattoo-needles",
]


def clean_price(price_str: str) -> float:
    try:
        cleaned = re.sub(r'[^\d.]', '', price_str)
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0


def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.maximize_window()
    driver.set_page_load_timeout(60)
    return driver


def solve_cloudflare(driver, max_retries=5):
    for attempt in range(max_retries):
        time.sleep(3)
        page = driver.page_source.lower()
        if "checking your browser" in page or "just a moment" in page:
            logger.info(f"Cloudflare detected — attempt {attempt + 1}/{max_retries}")
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        elems = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"], label, span')
                        for elem in elems:
                            try:
                                if elem.is_displayed():
                                    ActionChains(driver).move_to_element(elem).pause(
                                        random.uniform(0.3, 0.7)
                                    ).click().perform()
                                    time.sleep(2)
                            except:
                                pass
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
            except Exception as e:
                logger.error(f"Cloudflare solve error: {e}")
        else:
            return True
    return False


def scrape_page(driver, url: str):
    products = []
    try:
        driver.get(url)
        time.sleep(4)
        solve_cloudflare(driver)

        title = driver.title
        if "moment" in title.lower() or "security" in title.lower():
            logger.warning(f"Still blocked: {url}")
            return []

        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.find_all("form", class_="product_addtocart_form")

        # Category from URL
        category = url.replace(BASE_URL, "").strip("/").split("/")[0]

        for card in cards:
            try:
                # Featured products ka data-id empty hota hai — skip karo
                fid = card.get("data-id", "").strip()
                if not fid:
                    continue

                name = card.get("data-name", "").strip()
                if not name:
                    continue

                # URL
                link_tag = card.find("a", href=True)
                product_url = link_tag["href"] if link_tag else ""
                if product_url and not product_url.startswith("http"):
                    product_url = BASE_URL + product_url

                # Price from data-price attribute
                price = 0.0
                data_price = card.get("data-price", "")
                if data_price:
                    decoded = html_module.unescape(data_price)
                    # Excl tax (basePrice) prefer karo
                    match = re.search(r'data-price-type=["\']basePrice["\'][^>]*data-price-amount=["\']([0-9.]+)["\']', decoded)
                    if not match:
                        match = re.search(r'data-price-amount=["\']([0-9.]+)["\']', decoded)
                    if match:
                        price = float(match.group(1))

                # Fallback span.price
                if price == 0.0:
                    price_tag = card.find("span", class_="price")
                    if price_tag:
                        price = clean_price(price_tag.get_text(strip=True))

                # Stock
                sold_out = card.find(class_=re.compile(r'sold.out|out.of.stock', re.I))
                stock_status = "out_of_stock" if sold_out else "in_stock"

                products.append({
                    "name": name,
                    "url": product_url,
                    "sku": fid,
                    "price": price,
                    "stock_status": stock_status,
                    "category": category
                })

            except Exception as e:
                logger.error(f"Card parse error: {e}")
                continue

    except Exception as e:
        logger.error(f"Page error: {e}")

    logger.info(f"Found {len(products)} products on {url}")
    return products


def get_next_page_url(driver):
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        next_btn = soup.find("li", class_="pages-item-next")
        if next_btn:
            a = next_btn.find("a")
            if a and a.get("href"):
                href = a["href"]
                return href if href.startswith("http") else BASE_URL + href

        # Fallback: ?p= pagination
        current_url = driver.current_url
        page_match = re.search(r'[?&]p=(\d+)', current_url)
        current_page = int(page_match.group(1)) if page_match else 1

        cards = soup.find_all("form", class_="product_addtocart_form")
        real_cards = [c for c in cards if c.get("data-id", "").strip()]
        
        if len(real_cards) >= 8:
            next_page = current_page + 1
            if '?' in current_url:
                if 'p=' in current_url:
                    return re.sub(r'p=\d+', f'p={next_page}', current_url)
                else:
                    return current_url + f'&p={next_page}'
            else:
                return current_url + f'?p={next_page}'
    except:
        pass
    return None


def run_killerink_scraper():
    logger.info("Starting Killer Ink scraper...")
    run = start_scrape_run(SITE_KEY)
    run_id = run["id"] if run else None

    total_products = 0
    total_changes = 0
    seen_skus = set()  # Duplicate SKUs avoid karo

    driver = setup_driver()

    try:
        for category_url in CATEGORY_URLS:
            current_url = category_url
            page_num = 1

            while current_url:
                logger.info(f"Scraping page {page_num}: {current_url}")
                products = scrape_page(driver, current_url)

                for product in products:
                    # Global duplicate check
                    if product["sku"] in seen_skus:
                        continue
                    seen_skus.add(product["sku"])

                    saved = insert_product(
                        site=SITE_KEY,
                        sku=product["sku"],
                        name=product["name"],
                        url=product["url"],
                        category=product["category"]
                    )
                    if saved:
                        product_id = saved["id"]
                        last = get_latest_price(product_id)
                        if last:
                            if float(last["price"]) != product["price"]:
                                insert_change_log(product_id, "price_change",
                                                  str(last["price"]), str(product["price"]))
                                total_changes += 1
                                logger.info(f"💰 Price change: {product['name']} £{last['price']} → £{product['price']}")
                            if last["stock_status"] != product["stock_status"]:
                                insert_change_log(product_id, "stock_change",
                                                  last["stock_status"], product["stock_status"])
                                total_changes += 1
                        insert_price_history(product_id, product["price"], product["stock_status"])
                        total_products += 1
                        logger.info(f"✅ Saved: {product['name']} | £{product['price']}")

                next_url = get_next_page_url(driver)
                if next_url and next_url != current_url:
                    current_url = next_url
                    page_num += 1
                else:
                    break

                time.sleep(random.uniform(2, 3))

    finally:
        driver.quit()

    if run_id:
        complete_scrape_run(run_id, total_products, total_changes)

    logger.info(f"✅ Killer Ink done. Products: {total_products}, Changes: {total_changes}")
    return {"products": total_products, "changes": total_changes}


if __name__ == "__main__":
    run_killerink_scraper()