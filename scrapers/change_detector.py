import logging
from database.db import supabase, insert_change_log

logger = logging.getLogger(__name__)


def detect_price_change(product_id: int, new_price: float) -> bool:
    """Price change detect karo"""
    try:
        result = supabase.table("price_history") \
            .select("price") \
            .eq("product_id", product_id) \
            .order("scraped_at", desc=True) \
            .limit(1) \
            .execute()

        if result.data:
            old_price = float(result.data[0]["price"])
            if old_price != new_price:
                insert_change_log(
                    product_id=product_id,
                    change_type="price_change",
                    old_value=str(old_price),
                    new_value=str(new_price)
                )
                logger.info(f"Price change detected: {old_price} -> {new_price}")
                return True
    except Exception as e:
        logger.error(f"detect_price_change error: {e}")
    return False


def detect_stock_change(product_id: int, new_stock: str) -> bool:
    """Stock change detect karo"""
    try:
        result = supabase.table("price_history") \
            .select("stock_status") \
            .eq("product_id", product_id) \
            .order("scraped_at", desc=True) \
            .limit(1) \
            .execute()

        if result.data:
            old_stock = result.data[0]["stock_status"]
            if old_stock != new_stock:
                insert_change_log(
                    product_id=product_id,
                    change_type="stock_change",
                    old_value=old_stock,
                    new_value=new_stock
                )
                logger.info(f"Stock change detected: {old_stock} -> {new_stock}")
                return True
    except Exception as e:
        logger.error(f"detect_stock_change error: {e}")
    return False


def detect_new_product(site: str, sku: str) -> bool:
    """Naya product detect karo"""
    try:
        result = supabase.table("products") \
            .select("id") \
            .eq("site", site) \
            .eq("sku", sku) \
            .execute()

        if not result.data:
            logger.info(f"New product detected: {sku} on {site}")
            return True
    except Exception as e:
        logger.error(f"detect_new_product error: {e}")
    return False


def get_price_comparison():
    """Dono sites ke products ka price comparison karo"""
    try:
        # Killer Ink products
        killerink = supabase.table("products") \
            .select("id, name, sku, url") \
            .eq("site", "killerink") \
            .execute()

        # Barber DTS products
        barberdts = supabase.table("products") \
            .select("id, name, sku, url") \
            .eq("site", "barberdts") \
            .execute()

        comparison = []

        for ki_product in killerink.data:
            # Latest price for killer ink
            ki_price_data = supabase.table("price_history") \
                .select("price, stock_status") \
                .eq("product_id", ki_product["id"]) \
                .order("scraped_at", desc=True) \
                .limit(1) \
                .execute()

            ki_price = float(ki_price_data.data[0]["price"]) if ki_price_data.data else 0.0
            ki_stock = ki_price_data.data[0]["stock_status"] if ki_price_data.data else "unknown"

            # Match karo barber dts se naam se
            matched = next(
                (p for p in barberdts.data if
                 p["name"].lower()[:20] == ki_product["name"].lower()[:20]),
                None
            )

            bd_price = 0.0
            bd_stock = "unknown"

            if matched:
                bd_price_data = supabase.table("price_history") \
                    .select("price, stock_status") \
                    .eq("product_id", matched["id"]) \
                    .order("scraped_at", desc=True) \
                    .limit(1) \
                    .execute()

                bd_price = float(bd_price_data.data[0]["price"]) if bd_price_data.data else 0.0
                bd_stock = bd_price_data.data[0]["stock_status"] if bd_price_data.data else "unknown"

            price_diff = round(ki_price - bd_price, 2)

            comparison.append({
                "product_name": ki_product["name"],
                "killerink_price": ki_price,
                "killerink_stock": ki_stock,
                "killerink_url": ki_product["url"],
                "barberdts_price": bd_price,
                "barberdts_stock": bd_stock,
                "barberdts_url": matched["url"] if matched else "",
                "price_difference": price_diff,
                "cheaper_site": "killerink" if ki_price < bd_price else "barberdts" if bd_price < ki_price else "same"
            })

        return comparison

    except Exception as e:
        logger.error(f"get_price_comparison error: {e}")
        return []


def get_recent_changes(limit: int = 50):
    """Recent changes lao"""
    try:
        result = supabase.table("change_log") \
            .select("*, products(name, site, url)") \
            .order("detected_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data
    except Exception as e:
        logger.error(f"get_recent_changes error: {e}")
        return []