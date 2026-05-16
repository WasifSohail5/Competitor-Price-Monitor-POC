from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def inspect_killerink():
    print("Inspecting Killer Ink...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/London",
        )
        page = context.new_page()

        # Automation detection hatao
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-GB', 'en']});
            window.chrome = {runtime: {}};
        """)

        print("Going to Killer Ink...")
        page.goto("https://www.killerinktattoo.co.uk/tattoo-ink", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        title = page.title()
        print(f"Page title: {title}")

        html = page.content()
        with open("logs/killerink.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved: logs/killerink.html")

        if "security" in title.lower() or "cloudflare" in html.lower()[:500]:
            print("❌ Still blocked by Cloudflare!")
            print("Manually click 'Verify you are human' in browser window")
            input("After passing Cloudflare, press Enter here...")
            html = page.content()
            with open("logs/killerink.html", "w", encoding="utf-8") as f:
                f.write(html)

        print("✅ Checking classes now...")
        soup = BeautifulSoup(html, "html.parser")
        seen = set()
        for tag in soup.find_all(class_=True):
            for cls in tag.get("class", []):
                key = f"{tag.name}.{cls}"
                if key not in seen and any(x in cls.lower() for x in ["product", "card", "item", "price", "name", "title"]):
                    seen.add(key)
                    print(f"  {key}")

        input("Press Enter to close browser...")
        browser.close()

def inspect_barberdts():
    print("\nInspecting Barber DTS...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto("https://www.barberdts.com/uk/tattoo-machines.html", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        title = page.title()
        print(f"Page title: {title}")

        html = page.content()
        with open("logs/barberdts.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved: logs/barberdts.html")

        soup = BeautifulSoup(html, "html.parser")
        print("\n--- Product related classes ---")
        seen = set()
        for tag in soup.find_all(class_=True):
            for cls in tag.get("class", []):
                key = f"{tag.name}.{cls}"
                if key not in seen and any(x in cls.lower() for x in ["product", "card", "item", "price", "name", "title"]):
                    seen.add(key)
                    print(f"  {key}")

        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    inspect_killerink()
    inspect_barberdts()