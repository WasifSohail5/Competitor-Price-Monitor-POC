import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
import random
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scrapers.barberdts_scraper import run_barberdts_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_barberdts():
    logger.info("=" * 40)
    logger.info("Scheduled Barber DTS scrape starting...")
    try:
        result = run_barberdts_scraper()
        logger.info(f"Barber DTS done: {result}")
    except Exception as e:
        logger.error(f"Barber DTS failed: {e}")
    logger.info("=" * 40)


def run_killerink():
    logger.info("=" * 40)
    logger.info("Scheduled Killer Ink scrape starting...")
    try:
        from scrapers.killerink_scraper import run_killerink_scraper
        result = run_killerink_scraper()
        logger.info(f"Killer Ink done: {result}")
    except Exception as e:
        logger.error(f"Killer Ink failed: {e}")
    logger.info("=" * 40)


def start_scheduler(interval_hours: int = 6):
    scheduler = BackgroundScheduler()

    # Barber DTS — har 6 ghante
    scheduler.add_job(
        run_barberdts,
        trigger=IntervalTrigger(hours=interval_hours),
        id="barberdts_job",
        name="Barber DTS Scraper",
        replace_existing=True,
    )

    # Killer Ink — har 6 ghante, 30 min baad start (overlap avoid)
    scheduler.add_job(
        run_killerink,
        trigger=IntervalTrigger(hours=interval_hours),
        id="killerink_job",
        name="Killer Ink Scraper",
        replace_existing=True,
        minutes=30,
    )

    scheduler.start()
    logger.info(f"Scheduler started — both scrapers every {interval_hours} hours")

    # First run — Barber DTS pehle
    logger.info("Running Barber DTS first scrape...")
    run_barberdts()

    # Killer Ink 2 min baad
    logger.info("Waiting 2 min before Killer Ink...")
    time.sleep(120)
    logger.info("Running Killer Ink first scrape...")
    run_killerink()

    return scheduler