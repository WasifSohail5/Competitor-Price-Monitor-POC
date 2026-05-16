import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Scraping Config
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", 6))

# Target Sites
SITES = {
    "killerink": {
        "name": "Killer Ink Tattoo",
        "base_url": "https://www.killerinktattoo.co.uk",
        "products_url": "https://www.killerinktattoo.co.uk/collections/all",
    },
    "barberdts": {
        "name": "Barber DTS",
        "base_url": "https://www.barberdts.com",
        "products_url": "https://www.barberdts.com/collections/all",
    }
}

# Logging Config
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/scraper.log"