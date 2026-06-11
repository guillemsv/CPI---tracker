# 📊 US CPI Tracker — Real-Time Inflation Nowcaster

A daily-updated CPI estimate built from live price data across the US economy.
Runs automatically on GitHub Actions — no server needed.

## What it does
- Scrapes **15+ data sources** daily (EIA, Zillow, FRED, Manheim, BLS, GasBuddy...)
- Covers **~70% of the CPI basket** via free APIs
- Computes a weighted CPI estimate using BLS weights
- Publishes a live dashboard at GitHub Pages
- Backtests accuracy against official BLS CPI releases

## CPI Coverage

| Component | Weight | Source | Method |
|-----------|--------|--------|--------|
| OER / Rent | 31.7% | Zillow, Apartment List | CSV download |
| Gasoline | 3.4% | EIA API | API |
| Electricity | 2.9% | EIA API | API |
| Natural gas | 0.9% | EIA API | API |
| Food at home | 8.7% | FRED PPI proxies + USDA | API |
| Used vehicles | 1.8% | Manheim / FRED | API |
| New vehicles | 3.0% | FRED | API |
| Medical services | 7.0% | FRED PPI | API |
| Wages proxy | — | FRED | API |
| Official BLS CPI | — | BLS API | Benchmark |

## Stack
- **Python 3.11** — scraping, processing
- **GitHub Actions** — free daily scheduler (cron)
- **GitHub Pages** — free dashboard hosting
- **Pandas + JSON** — data processing

## Setup (5 minutes)
See [SETUP.md](SETUP.md)

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env          # add your API keys
python run_daily.py
```

## Output
- `output/cpi_latest.json` — latest estimate
- `output/history.csv` — full price history
- `dashboard/index.html` — live web dashboard
