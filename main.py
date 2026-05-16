import logging
import argparse
from scrapers.barberdts_scraper import run_barberdts_scraper
from scrapers.killerink_scraper import run_killerink_scraper
from scrapers.change_detector import get_price_comparison, get_recent_changes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_once():
    logger.info("Running one-time scrape...")
    logger.info("--- Barber DTS ---")
    bd = run_barberdts_scraper()
    logger.info(f"Barber DTS: {bd}")
    logger.info("One-time scrape complete!")


def run_dashboard():
    import uvicorn
    import threading
    from scheduler.job_scheduler import start_scheduler
    from config import SCRAPE_INTERVAL_HOURS

    # Scheduler alag thread mein start karo
    def start_bg_scheduler():
        start_scheduler(interval_hours=SCRAPE_INTERVAL_HOURS)

    scheduler_thread = threading.Thread(target=start_bg_scheduler, daemon=True)
    scheduler_thread.start()

    logger.info("Starting dashboard on http://localhost:8000")
    uvicorn.run("frontend.app:app", host="0.0.0.0", port=8000)


def show_comparison():
    comparison = get_price_comparison()
    if not comparison:
        print("No comparison data. Run scraper first.")
        return
    print(f"\n{'='*80}")
    print(f"{'PRODUCT':<40} {'KILLER INK':>10} {'BARBER DTS':>10} {'DIFF':>8}")
    print("=" * 80)
    for item in comparison:
        print(f"{item['product_name'][:39]:<40} £{item['killerink_price']:>9.2f} £{item['barberdts_price']:>9.2f} £{item['price_difference']:>7.2f}")


def show_changes():
    changes = get_recent_changes(limit=20)
    if not changes:
        print("No changes detected yet.")
        return
    print("\n" + "=" * 80)
    for c in changes:
        name = c.get("products", {}).get("name", "Unknown")
        site = c.get("products", {}).get("site", "Unknown")
        print(f"[{c['detected_at'][:19]}] {site.upper():<12} {c['change_type']:<15} {name[:30]:<30} {c['old_value']} -> {c['new_value']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Competitor Price Monitor")
    parser.add_argument(
        "--mode",
        choices=["once", "dashboard", "compare", "changes"],
        default="dashboard",
        help="once=single scrape | dashboard=UI+scheduler | compare=prices | changes=log"
    )
    args = parser.parse_args()

    if args.mode == "once":
        run_once()
    elif args.mode == "dashboard":
        run_dashboard()
    elif args.mode == "compare":
        show_comparison()
    elif args.mode == "changes":
        show_changes()