# ⚡ Competitor Price Monitor
### Killer Ink Tattoo vs Barber DTS — Ecommerce Intelligence Platform

> Automatically track every price, every stock change, and every product update across two major tattoo supply competitors.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Running the System](#running-the-system)
- [Dashboard](#dashboard)
- [Deployment](#deployment)
- [Known Limitations](#known-limitations)

---

## Overview

This is a production-ready Proof of Concept (POC) that automatically scrapes, compares, and monitors pricing and product data from:

| Site | URL | Platform |
|------|-----|----------|
| **Killer Ink Tattoo** | killerinktattoo.co.uk | Magento + Cloudflare |
| **Barber DTS** | barberdts.com/uk | Magento |

The system runs on a continuous automated loop — scraping both sites, detecting price changes, storing historical data in Supabase, and displaying everything on a live dashboard.

---

## Features

| Feature | Description |
|---------|-------------|
| ⚡ **Auto Scraping** | Barber DTS scraped automatically every 6 hours |
| 💰 **Price Comparison** | Side-by-side price diff between both sites |
| 📊 **Price History** | Every price recorded at every scrape run |
| 🔔 **Change Detection** | Detects price drops, stock changes, new products |
| 🗄️ **Supabase Storage** | Clean schema with products, price_history, change_log tables |
| 🖥️ **Live Dashboard** | FastAPI + HTML dashboard to view all data |
| 📅 **Auto Scheduler** | APScheduler background scheduler |
| 🔍 **Search & Filter** | Search products across both sites |

---

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| **Scraping (Barber DTS)** | Python + Playwright | Free |
| **Scraping (Killer Ink)** | Python + undetected-chromedriver | Free |
| **Scheduling** | APScheduler | Free |
| **Database** | Supabase (PostgreSQL) | Free tier |
| **Backend API** | FastAPI + Uvicorn | Free |
| **Frontend** | Vanilla HTML/CSS/JS | Free |
| **Infrastructure** | ~$0–5/month | Free tier |

---

## Project Structure

```
competitor-price-monitor/
│
├── scrapers/
│   ├── killerink_scraper.py      # Killer Ink scraper (undetected-chromedriver)
│   ├── barberdts_scraper.py      # Barber DTS scraper (Playwright)
│   ├── change_detector.py        # Price & stock change detection logic
│   ├── inspect_sites.py          # Dev tool: inspect site HTML structure
│   └── inspect_killerink.py      # Dev tool: inspect Killer Ink HTML
│
├── database/
│   ├── db.py                     # Supabase client + all DB functions
│   └── __init__.py
│
├── scheduler/
│   ├── job_scheduler.py          # APScheduler setup for auto scraping
│   └── __init__.py
│
├── frontend/
│   ├── app.py                    # FastAPI backend + API endpoints
│   ├── index.html                # Dashboard UI
│   └── dashboard.jsx             # (React version - not used)
│
├── logs/                         # Scrape logs + HTML snapshots
├── main.py                       # Entry point — all modes
├── config.py                     # Config + environment variables
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker deployment
├── docker-compose.yml            # Docker Compose
├── .env                          # Environment variables (not committed)
└── .gitignore
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Git
- Google Chrome (for Killer Ink scraper)

### Step 1: Clone the repo

```bash
git clone https://github.com/WasifSohail5/Competitor-Price-Monitor-POC.git
cd Competitor-Price-Monitor-POC
```

### Step 2: Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 4: Setup Supabase

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Go to **SQL Editor** and run the following:

```sql
-- Products Table
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    site VARCHAR(50) NOT NULL,
    sku VARCHAR(255),
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    category VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(site, sku)
);

-- Price History Table
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id),
    price DECIMAL(10,2),
    stock_status VARCHAR(50),
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Change Log Table
CREATE TABLE change_log (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id),
    change_type VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scrape Runs Table
CREATE TABLE scrape_runs (
    id BIGSERIAL PRIMARY KEY,
    site VARCHAR(50),
    status VARCHAR(50),
    products_scraped INT DEFAULT 0,
    changes_detected INT DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Step 5: Configure environment variables

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SCRAPE_INTERVAL_HOURS=6
LOG_LEVEL=INFO
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | Required |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Required |
| `SCRAPE_INTERVAL_HOURS` | How often to auto-scrape | `6` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Database Schema

```
products
├── id (PK)
├── site          → "killerink" or "barberdts"
├── sku           → unique product ID
├── name          → product name
├── url           → product page URL
├── category      → product category
├── created_at
└── updated_at

price_history
├── id (PK)
├── product_id    → FK to products
├── price         → price at time of scrape
├── stock_status  → "in_stock" or "out_of_stock"
└── scraped_at

change_log
├── id (PK)
├── product_id    → FK to products
├── change_type   → "price_change" or "stock_change"
├── old_value
├── new_value
└── detected_at

scrape_runs
├── id (PK)
├── site
├── status        → "running" / "success" / "failed"
├── products_scraped
├── changes_detected
├── started_at
└── completed_at
```

---

## Running the System

### Option 1: Dashboard + Auto Scheduler (Recommended)

```bash
python main.py --mode dashboard
```

This starts:
- ✅ FastAPI dashboard at `http://localhost:8000`
- ✅ Background scheduler — Barber DTS every 6 hours
- ✅ First scrape runs immediately on startup

### Option 2: One-time Scrape Only

```bash
python main.py --mode once
```

### Option 3: Run Individual Scrapers

```bash
# Barber DTS only
python scrapers/barberdts_scraper.py

# Killer Ink only
python scrapers/killerink_scraper.py
```

### Option 4: View Data in Terminal

```bash
# Price comparison
python main.py --mode compare

# Recent changes
python main.py --mode changes
```

---

## Dashboard

Access at: **http://localhost:8000**

| Tab | Description |
|-----|-------------|
| **Price Comparison** | Side-by-side prices for matched products |
| **Killer Ink** | All Killer Ink products with prices & stock |
| **Barber DTS** | All Barber DTS products with prices & stock |
| **Change Log** | Every price/stock change detected |
| **Scrape Runs** | Full audit trail of all scrape runs |

---

## Deployment

### Docker (Recommended)

```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### VPS Deployment (Ubuntu 22.04)

```bash
# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update && apt-get install -y google-chrome-stable

# Clone and setup
git clone https://github.com/WasifSohail5/Competitor-Price-Monitor-POC.git
cd Competitor-Price-Monitor-POC
pip install -r requirements.txt
playwright install chromium

# Run with environment variables
cp .env.example .env  # fill in your values
python main.py --mode dashboard
```

### Railway / Render

1. Connect GitHub repo
2. Add environment variables from `.env`
3. Set start command: `python main.py --mode dashboard`
4. Deploy

---

## Known Limitations

### Killer Ink — Cloudflare Protection

Killer Ink uses **Cloudflare Turnstile** enterprise-grade bot protection.

| Environment | Status |
|-------------|--------|
| Local machine (Windows) | ✅ Works — undetected Chrome bypasses Cloudflare |
| VPS / Server | ⚠️ May work but VPS IPs can get blocked by Cloudflare |
| Docker container | ⚠️ Same risk as VPS |

**For 100% reliable server deployment of Killer Ink scraper**, a dedicated scraping API is required:
- [ScraperAPI](https://scraperapi.com) — from $49/month
- [BrightData](https://brightdata.com) — from $99/month

Barber DTS has **no Cloudflare protection** and works 100% reliably on any server.

---

## System Workflow

```
SCHEDULER (every 6 hours)
        ↓
SCRAPER (Playwright / undetected-chromedriver)
        ↓
COMPARISON ENGINE (match products, calculate diff)
        ↓
CHANGE DETECTOR (price change / stock change / new product)
        ↓
SUPABASE (products → price_history → change_log → scrape_runs)
        ↓
DASHBOARD (http://localhost:8000)
```

---

## Post-POC Roadmap

- [ ] Email / Slack alerts for price changes
- [ ] More competitor websites (expandable architecture)
- [ ] Advanced dashboard with price history charts
- [ ] User authentication
- [ ] REST API endpoints for external integration
- [ ] Mobile app

---

*Prepared by Wasif Sohail | May 2026*
