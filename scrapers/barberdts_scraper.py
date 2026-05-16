import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from database.db import (insert_product, insert_price_history,
                         insert_change_log, get_latest_price,
                         start_scrape_run, complete_scrape_run)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SITE_KEY = "barberdts"
BASE_URL = "https://www.barberdts.com"

CATEGORY_URLS = [
    "https://www.barberdts.com/uk/tattoo-machines.html",
    "https://www.barberdts.com/uk/tattoo-ink.html",
    "https://www.barberdts.com/uk/tattoo-cartridges.html",
    "https://www.barberdts.com/uk/tattoo-needles.html",
    "https://www.barberdts.com/uk/tattoo-power-supplies.html",
    "https://www.barberdts.com/uk/tattoo-grips-and-tubes.html",
]


def clean_price(price_str: str) -> float:
    try:
        cleaned = re.sub(r'[^\d.]', '', price_str)
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0


def scrape_page(page, url: str):
    products = []
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        soup = BeautifulSoup(page.content(), "html.parser")

        # Barber DTS product cards
        cards = soup.find_all("form", class_="prod-card")
        if not cards:
            cards = soup.find_all("form", class_="product-item")
        if not cards:
            cards = soup.find_all("form", class_=re.compile(r'product', re.I))

        logger.info(f"Found {len(cards)} products on {url}")

        for card in cards:
            try:
                # Name
                name_tag = card.find("a", class_="product-item-link")
                if not name_tag:
                    name_tag = card.find(class_=re.compile(r'prod-title|product-name', re.I))
                name = name_tag.get_text(strip=True) if name_tag else None
                if not name:
                    continue

                # URL
                product_url = name_tag.get("href", "") if name_tag else ""
                if product_url and not product_url.startswith("http"):
                    product_url = BASE_URL + product_url

                # SKU from URL
                sku = product_url.rstrip("/").split("/")[-1].replace(".html", "") if product_url else name.lower().replace(" ", "-")[:50]

                # Price — special price first, then regular
                special = card.find("span", class_="special-price")
                if special:
                    price_tag = special.find("span", class_="price")
                else:
                    price_tag = card.find("span", class_="price")
                price = clean_price(price_tag.get_text(strip=True)) if price_tag else 0.0

                # Stock
                sold_out = card.find(class_=re.compile(r'sold.out|out.of.stock|unavailable', re.I))
                stock_status = "out_of_stock" if sold_out else "in_stock"

                # Category from URL
                category = url.split("/")[-1].replace(".html", "")

                products.append({
                    "name": name,
                    "url": product_url,
                    "sku": sku,
                    "price": price,
                    "stock_status": stock_status,
                    "category": category
                })

            except Exception as e:
                logger.error(f"Card parse error: {e}")
                continue

    except Exception as e:
        logger.error(f"Page error: {e}")

    return products


def get_next_page_url(page, base_url: str):
    try:
        soup = BeautifulSoup(page.content(), "html.parser")
        next_btn = soup.find("a", class_=re.compile(r'next', re.I))
        if not next_btn:
            next_btn = soup.find("li", class_="pages-item-next")
            if next_btn:
                next_btn = next_btn.find("a")
        if next_btn and next_btn.get("href"):
            href = next_btn["href"]
            if href.startswith("http"):
                return href
            return BASE_URL + href
    except:
        pass
    return None


def run_barberdts_scraper():
    logger.info("Starting Barber DTS scraper...")
    run = start_scrape_run(SITE_KEY)
    run_id = run["id"] if run else None

    total_products = 0
    total_changes = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        for category_url in CATEGORY_URLS:
            current_url = category_url
            page_num = 1

            while current_url:
                logger.info(f"Scraping page {page_num}: {current_url}")
                products = scrape_page(page, current_url)

                for product in products:
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

                next_url = get_next_page_url(page, current_url)
                if next_url and next_url != current_url:
                    current_url = next_url
                    page_num += 1
                else:
                    break

        browser.close()

    if run_id:
        complete_scrape_run(run_id, total_products, total_changes)

    logger.info(f"✅ Barber DTS done. Products: {total_products}, Changes: {total_changes}")
    return {"products": total_products, "changes": total_changes}


if __name__ == "__main__":
    run_barberdts_scraper()