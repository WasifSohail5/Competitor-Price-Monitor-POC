import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from database.db import supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


@app.get("/api/stats")
def get_stats():
    ki = supabase.table("products").select("id", count="exact").eq("site", "killerink").execute()
    bd = supabase.table("products").select("id", count="exact").eq("site", "barberdts").execute()
    changes = supabase.table("change_log").select("id", count="exact").execute()
    last_run = supabase.table("scrape_runs").select("*").order("started_at", desc=True).limit(1).execute()
    return {
        "killerink_products": ki.count,
        "barberdts_products": bd.count,
        "total_changes": changes.count,
        "last_run": last_run.data[0] if last_run.data else None,
    }


def get_products_with_prices(site=None, search=None):
    q = supabase.table("products").select("*").order("name")
    if site:
        q = q.eq("site", site)
    if search:
        q = q.ilike("name", f"%{search}%")
    products = q.execute().data

    latest = supabase.table("price_history").select("*").order("scraped_at", desc=True).limit(5000).execute().data
    price_map = {}
    for p in latest:
        if p["product_id"] not in price_map:
            price_map[p["product_id"]] = p

    for p in products:
        ph = price_map.get(p["id"], {})
        p["price"] = float(ph.get("price", 0))
        p["stock_status"] = ph.get("stock_status", "unknown")

    return products


@app.get("/api/products")
def get_products(site: str = None, search: str = None):
    return get_products_with_prices(site=site, search=search)


@app.get("/api/comparison")
def get_comparison():
    ki = get_products_with_prices(site="killerink")
    bd = get_products_with_prices(site="barberdts")

    # Multiple matching strategies
    bd_map_full = {normalize(p["name"]): p for p in bd}
    bd_map_30 = {normalize(p["name"])[:30]: p for p in bd}
    bd_map_20 = {normalize(p["name"])[:20]: p for p in bd}

    result = []
    for k in ki:
        k_norm = normalize(k["name"])

        # Strategy 1: Full name match
        match = bd_map_full.get(k_norm)

        # Strategy 2: First 30 chars
        if not match:
            match = bd_map_30.get(k_norm[:30])

        # Strategy 3: First 20 chars
        if not match:
            match = bd_map_20.get(k_norm[:20])

        # Strategy 4: Partial contains
        if not match and len(k_norm) > 15:
            for bd_norm, bd_val in bd_map_full.items():
                if k_norm[:20] in bd_norm or bd_norm[:20] in k_norm:
                    match = bd_val
                    break

        if match:
            diff = round(k["price"] - match["price"], 2)
            result.append({
                "name": k["name"],
                "ki_price": k["price"],
                "ki_stock": k["stock_status"],
                "ki_url": k["url"],
                "bd_price": match["price"],
                "bd_stock": match["stock_status"],
                "bd_url": match["url"],
                "diff": diff,
                "cheaper": "killerink" if diff < 0 else "barberdts" if diff > 0 else "same",
            })

    return result


@app.get("/api/changes")
def get_changes(limit: int = 100):
    result = supabase.table("change_log") \
        .select("*, products(name, site, url)") \
        .order("detected_at", desc=True) \
        .limit(limit) \
        .execute()
    return result.data


@app.get("/api/scrape-runs")
def get_scrape_runs():
    result = supabase.table("scrape_runs") \
        .select("*") \
        .order("started_at", desc=True) \
        .limit(20) \
        .execute()
    return result.data


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)