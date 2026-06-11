"""
run_daily.py — main entry point
Run manually: python run_daily.py
Runs automatically via GitHub Actions every day at 08:00 UTC
"""

import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from scrapers import eia, fred, bls, zillow
from processing.calculator import (
    compute_cpi_estimate,
    add_official_benchmark,
    save_output,
    append_history,
)


def run():
    print("=" * 60)
    print(f"  CPI Tracker — Daily Run")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    all_scraped = []
    official_data = []

    # ── 1. EIA (energy prices) ─────────────────────────────────────
    print("\n[1/4] Fetching EIA energy prices...")
    try:
        eia_data = eia.fetch_all()
        all_scraped.extend(eia_data)
        print(f"      → {len(eia_data)} series fetched")
    except Exception as e:
        print(f"      ✗ EIA failed: {e}")

    # ── 2. FRED (rents, wages, vehicles, food PPIs) ────────────────
    print("\n[2/4] Fetching FRED economic data...")
    try:
        fred_data = fred.fetch_all()
        all_scraped.extend(fred_data)
        print(f"      → {len(fred_data)} series fetched")
    except Exception as e:
        print(f"      ✗ FRED failed: {e}")

    # ── 3. Zillow (market rents — OER leading indicator) ───────────
    print("\n[3/4] Fetching Zillow rent data...")
    try:
        zillow_data = zillow.fetch_all()
        all_scraped.extend(zillow_data)
        print(f"      → {len(zillow_data)} series fetched")
    except Exception as e:
        print(f"      ✗ Zillow failed: {e}")

    # ── 4. BLS official CPI (benchmark) ───────────────────────────
    print("\n[4/4] Fetching BLS official CPI benchmark...")
    try:
        official_data = bls.fetch_all()
        # Also add BLS series to scraped for component coverage
        all_scraped.extend(official_data)
        print(f"      → {len(official_data)} series fetched")
    except Exception as e:
        print(f"      ✗ BLS failed: {e}")

    # ── 5. Compute CPI estimate ────────────────────────────────────
    print("\n[Computing CPI estimate...]")
    estimate = compute_cpi_estimate(all_scraped)
    estimate = add_official_benchmark(estimate, official_data)

    # ── 6. Print summary ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    headline = estimate["estimate"].get("headline_cpi_pct")
    core = estimate["estimate"].get("core_cpi_pct")
    coverage = estimate["estimate"].get("basket_coverage_pct")

    print(f"  Our Headline CPI Estimate:  {headline:+.2f}% YoY" if headline else "  Headline: N/A")
    print(f"  Our Core CPI Estimate:      {core:+.2f}% YoY" if core else "  Core: N/A")
    print(f"  Basket coverage:            {coverage}%")

    official = estimate.get("official", {})
    if official.get("headline_cpi_pct"):
        print(f"\n  BLS Official (latest):      {official['headline_cpi_pct']:+.2f}% YoY ({official.get('date', '')})")
    if estimate.get("accuracy"):
        print(f"  Tracking error:             {estimate['accuracy']['error_pp']:+.2f}pp")

    print("\n  Category breakdown:")
    for cat_key, cat in estimate["category_breakdown"].items():
        yoy_str = f"{cat['avg_yoy_pct']:+.1f}%" if cat['avg_yoy_pct'] is not None else "N/A"
        contrib_str = f"{cat['contribution_bp']:+.0f}bp" if cat['contribution_bp'] else ""
        print(f"    {cat['label']:<25} {yoy_str:>8}  ({cat['weight']:.1f}% weight)  {contrib_str}")

    # ── 7. Save outputs ────────────────────────────────────────────
    print("\n[Saving outputs...]")
    save_output(estimate)
    append_history(estimate)

    # Also save raw scraped data for debugging
    os.makedirs("data", exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    with open(f"data/raw_{date_str}.json", "w") as f:
        json.dump(all_scraped, f, indent=2)
    print(f"✓ Raw data saved to data/raw_{date_str}.json")

    print("\n✅ Done.")
    return estimate


if __name__ == "__main__":
    run()
