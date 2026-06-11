"""
BLS API scraper — official CPI releases for benchmarking.
Free API: https://data.bls.gov/registrationEngine/
No key needed for basic access (limited); key gives more history.
"""

import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BLS_KEY = os.getenv("BLS_API_KEY", "")
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Key BLS series IDs
SERIES = {
    "headline_cpi":    "CUSR0000SA0",    # CPI-U All items
    "core_cpi":        "CUSR0000SA0L1E", # CPI-U ex food & energy
    "food_cpi":        "CUSR0000SAF1",   # Food
    "energy_cpi":      "CUSR0000SA0E",   # Energy
    "shelter_cpi":     "CUSR0000SAH1",   # Shelter
    "medical_cpi":     "CUSR0000SAM",    # Medical care
    "transport_cpi":   "CUSR0000SAT",    # Transportation
    "apparel_cpi":     "CUSR0000SAA",    # Apparel
    "education_cpi":   "CUSR0000SAE",    # Education & communication
    "recreation_cpi":  "CUSR0000SAR",    # Recreation
}


def fetch_bls_series(series_ids: list, years_back: int = 3) -> dict:
    """Fetch multiple BLS series in one API call (max 50 series per call)."""
    current_year = datetime.now().year
    start_year = str(current_year - years_back)
    end_year = str(current_year)

    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
        "calculations": True,    # includes YoY changes
        "annualaverage": False,
    }
    if BLS_KEY:
        payload["registrationkey"] = BLS_KEY

    resp = requests.post(BLS_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_bls_response(data: dict) -> list:
    """Parse BLS API response into clean records."""
    results = []
    for series in data.get("Results", {}).get("series", []):
        series_id = series["seriesID"]
        label = next((k for k, v in SERIES.items() if v == series_id), series_id)
        obs = series.get("data", [])
        if not obs:
            continue

        # BLS returns newest first
        latest = obs[0]
        # Find year-ago value
        year_ago = None
        for o in obs:
            if o["year"] == str(int(latest["year"]) - 1) and o["period"] == latest["period"]:
                year_ago = o
                break

        yoy = None
        if year_ago:
            try:
                curr_val = float(latest["value"])
                prev_val = float(year_ago["value"])
                yoy = round(((curr_val - prev_val) / prev_val) * 100, 2)
            except (ValueError, ZeroDivisionError):
                pass

        # Also check BLS built-in calculations
        if yoy is None:
            calcs = latest.get("calculations", {})
            pct_changes = calcs.get("pct_changes", {})
            if "12" in pct_changes:
                try:
                    yoy = round(float(pct_changes["12"]), 2)
                except ValueError:
                    pass

        period_str = f"{latest['year']}-{latest['period'].replace('M', '')}-01"
        try:
            period_date = pd.to_datetime(period_str).strftime("%Y-%m-%d")
        except Exception:
            period_date = f"{latest['year']}-{latest['period']}"

        result = {
            "component": label,
            "label": f"BLS Official: {label.replace('_', ' ').title()}",
            "date": period_date,
            "price": float(latest["value"]),
            "yoy_pct": yoy,
            "unit": "Index (1982-84=100)",
            "source": "BLS Official",
            "series": series_id,
            "is_official": True,
        }
        results.append(result)
        print(f"  ✓ BLS: {result['label']} → {yoy:+.1f}% YoY" if yoy else f"  ✓ BLS: {result['label']}")

    return results


def fetch_all() -> list:
    """Fetch all tracked BLS series."""
    try:
        series_ids = list(SERIES.values())
        raw = fetch_bls_series(series_ids, years_back=3)
        if raw.get("status") != "REQUEST_SUCCEEDED":
            print(f"  ✗ BLS API error: {raw.get('message', 'unknown')}")
            return []
        return parse_bls_response(raw)
    except Exception as e:
        print(f"  ✗ BLS fetch failed: {e}")
        return []


def get_latest_headline() -> dict:
    """Quick fetch of just headline CPI for dashboard summary."""
    try:
        raw = fetch_bls_series(["CUSR0000SA0", "CUSR0000SA0L1E"], years_back=2)
        parsed = parse_bls_response(raw)
        result = {}
        for r in parsed:
            if r["component"] == "headline_cpi":
                result["headline"] = r
            elif r["component"] == "core_cpi":
                result["core"] = r
        return result
    except Exception as e:
        print(f"  ✗ BLS headline fetch: {e}")
        return {}


if __name__ == "__main__":
    print("Testing BLS scraper...")
    data = fetch_all()
    print(f"\nFetched {len(data)} official series")
    for d in data:
        yoy_str = f"{d['yoy_pct']:+.1f}%" if d.get("yoy_pct") else "N/A"
        print(f"  {d['label']}: {yoy_str}")
