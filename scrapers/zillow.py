"""
Zillow scraper — Zillow Observed Rent Index (ZORI)
Zillow publishes free CSV downloads monthly.
This is the best leading indicator for OER (12-15 month lag).
Covers: OER (24%) + Rent (7.7%) = 31.7% of CPI
"""

import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta


# Zillow publishes these as public CSVs — no API key needed
ZILLOW_URLS = {
    "zori_all": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
    "zori_sfr": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfr_sm_month.csv",
    "zhvi":     "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
}

NATIONAL_REGION = "United States"


def fetch_zillow_csv(url: str) -> pd.DataFrame:
    """Download a Zillow research CSV and return as DataFrame."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CPI-Tracker/1.0)"
    }
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    return df


def get_national_rent() -> dict:
    """
    Fetch national ZORI (Zillow Observed Rent Index).
    Returns latest value + YoY % change.
    """
    df = fetch_zillow_csv(ZILLOW_URLS["zori_all"])

    # Filter to national row
    national = df[df["RegionName"] == NATIONAL_REGION]
    if national.empty:
        # Try alternative region name
        national = df[df["RegionName"].str.contains("United States", na=False)]
    if national.empty:
        raise ValueError(f"Cannot find '{NATIONAL_REGION}' in Zillow data")

    row = national.iloc[0]

    # Get date columns (format: YYYY-MM-DD)
    date_cols = [c for c in df.columns if c[:4].isdigit()]
    date_cols = sorted(date_cols)

    # Latest value
    latest_col = date_cols[-1]
    latest_val = float(row[latest_col])
    latest_date = pd.to_datetime(latest_col)

    # Year-ago value (find closest column ~12 months back)
    target_ago = latest_date - timedelta(days=365)
    year_ago_col = min(date_cols, key=lambda c: abs((pd.to_datetime(c) - target_ago).days))
    year_ago_val = float(row[year_ago_col])

    yoy = ((latest_val - year_ago_val) / year_ago_val) * 100

    # 3-month trend (momentum)
    if len(date_cols) >= 3:
        three_m_col = date_cols[-4]
        three_m_val = float(row[three_m_col])
        mom_3 = ((latest_val - three_m_val) / three_m_val) * 100 * 4  # annualized
    else:
        mom_3 = None

    return {
        "component": "zori",
        "label": "Zillow Rent Index ZORI (national)",
        "date": latest_date.strftime("%Y-%m-%d"),
        "price": round(latest_val, 2),
        "price_year_ago": round(year_ago_val, 2),
        "yoy_pct": round(yoy, 2),
        "mom_annualized_3m": round(mom_3, 2) if mom_3 else None,
        "unit": "$/month",
        "source": "Zillow Research",
        "note": "LEADING INDICATOR — OER lags ZORI by 12-15 months. Current ZORI predicts OER 1yr forward.",
    }


def get_top_metros(n: int = 10) -> list:
    """Fetch rent data for top N metros by population."""
    top_metros = [
        "New York, NY", "Los Angeles, CA", "Chicago, IL", "Dallas, TX",
        "Houston, TX", "Washington, DC", "Miami, FL", "Atlanta, GA",
        "Philadelphia, PA", "Phoenix, AZ",
    ]
    df = fetch_zillow_csv(ZILLOW_URLS["zori_all"])
    date_cols = sorted([c for c in df.columns if c[:4].isdigit()])
    latest_col = date_cols[-1]
    year_ago_col = sorted(date_cols, key=lambda c: abs((pd.to_datetime(c) - (pd.to_datetime(latest_col) - timedelta(days=365))).days))[0]

    results = []
    for metro in top_metros:
        row = df[df["RegionName"].str.contains(metro.split(",")[0], na=False)]
        if row.empty:
            continue
        row = row.iloc[0]
        try:
            curr = float(row[latest_col])
            prev = float(row[year_ago_col])
            yoy = ((curr - prev) / prev) * 100
            results.append({
                "metro": row["RegionName"],
                "rent": round(curr, 0),
                "yoy_pct": round(yoy, 2),
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["yoy_pct"], reverse=True)


def fetch_all() -> list:
    results = []
    try:
        r = get_national_rent()
        results.append(r)
        print(f"  ✓ Zillow: {r['label']} → ${r['price']}/mo ({r['yoy_pct']:+.1f}% YoY)")
        print(f"    → OER forecast 12m forward: {r['yoy_pct'] * 0.85:.1f}% (applying 0.85 pass-through)")
    except Exception as e:
        print(f"  ✗ Zillow: {e}")
    return results


if __name__ == "__main__":
    print("Testing Zillow scraper...")
    data = fetch_all()
    print("\nTop metros by rent growth:")
    try:
        metros = get_top_metros()
        for m in metros:
            print(f"  {m['metro']}: ${m['rent']}/mo ({m['yoy_pct']:+.1f}% YoY)")
    except Exception as e:
        print(f"  Error: {e}")
