from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
import logging

logger = logging.getLogger(__name__)

# Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def insert_product(site: str, sku: str, name: str, url: str, category: str = None):
    """Product insert karo ya update karo agar already exist kare"""
    try:
        result = supabase.table("products").upsert({
            "site": site,
            "sku": sku,
            "name": name,
            "url": url,
            "category": category,
            "updated_at": "now()"
        }, on_conflict="site,sku").execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"insert_product error: {e}")
        return None


def insert_price_history(product_id: int, price: float, stock_status: str):
    """Har scrape ka price record karo"""
    try:
        result = supabase.table("price_history").insert({
            "product_id": product_id,
            "price": price,
            "stock_status": stock_status,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"insert_price_history error: {e}")
        return None


def insert_change_log(product_id: int, change_type: str, old_value: str, new_value: str):
    """Koi bhi change detect ho to log karo"""
    try:
        result = supabase.table("change_log").insert({
            "product_id": product_id,
            "change_type": change_type,
            "old_value": old_value,
            "new_value": new_value,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"insert_change_log error: {e}")
        return None


def get_latest_price(product_id: int):
    """Product ki last recorded price lao"""
    try:
        result = supabase.table("price_history") \
            .select("*") \
            .eq("product_id", product_id) \
            .order("scraped_at", desc=True) \
            .limit(1) \
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_latest_price error: {e}")
        return None


def start_scrape_run(site: str):
    """Scrape run start hone ka record karo"""
    try:
        result = supabase.table("scrape_runs").insert({
            "site": site,
            "status": "running",
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"start_scrape_run error: {e}")
        return None


def complete_scrape_run(run_id: int, products_scraped: int, changes_detected: int, status: str = "success"):
    """Scrape run complete hone ka record karo"""
    try:
        result = supabase.table("scrape_runs").update({
            "status": status,
            "products_scraped": products_scraped,
            "changes_detected": changes_detected,
            "completed_at": "now()"
        }).eq("id", run_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"complete_scrape_run error: {e}")
        return None