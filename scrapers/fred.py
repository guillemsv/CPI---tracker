"""
FRED API scraper — covers rents, wages, food PPIs, vehicles, medical
Free API: https://fredaccount.stlouisfed.org
Covers: ~50% of CPI basket via proxy series
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

FRED_KEY = os.getenv("FRED_API_KEY", "")


def _fred_series(series_id: str, periods: int = 24) -> pd.DataFrame:
    """Fetch a FRED series using fredapi or raw requests as fallback."""
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_KEY)
        s = fred.get_series(series_id)
        df = s.reset_index()
        df.columns = ["period", "value"]
        df["period"] = pd.to_datetime(df["period"])
        df = df.dropna().sort_values("period").tail(periods)
        return df
    except Exception:
        import requests
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": periods,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        df = pd.DataFrame(obs)[["date", "value"]]
        df.columns = ["period", "value"]
        df["period"] = pd.to_datetime(df["period"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().sort_values("period")


def _yoy(series_id: str, component: str, label: str, unit: str, note: str = "") -> dict:
    """Generic YoY calculator for any FRED series."""
    df = _fred_series(series_id, periods=36)
    if df.empty or len(df) < 2:
        return {}
    latest = df.iloc[-1]
    year_ago = df[df["period"] <= latest["period"] - timedelta(days=335)]
    if year_ago.empty:
        return {}
    year_ago_val = year_ago.iloc[-1]["value"]
    yoy = ((latest["value"] - year_ago_val) / year_ago_val) * 100
    result = {
        "component": component,
        "label": label,
        "date": latest["period"].strftime("%Y-%m-%d"),
        "price": round(float(latest["value"]), 3),
        "price_year_ago": round(float(year_ago_val), 3),
        "yoy_pct": round(float(yoy), 2),
        "unit": unit,
        "source": "FRED",
        "series": series_id,
    }
    if note:
        result["note"] = note
    return result


# ── HOUSING ────────────────────────────────────────────────────────────────

def fetch_rent_index() -> dict:
    """
    Zillow Observed Rent Index (ZORI) via FRED — CUSR0000SEHA
    This is the BLS actual rent series, monthly.
    """
    return _yoy("CUSR0000SEHA", "rent",
                "BLS Rent of primary residence (index)",
                "Index (1982=100)",
                "Direct BLS series; 7.7% CPI weight")


def fetch_oer() -> dict:
    """
    BLS Owners Equivalent Rent via FRED — CUSR0000SEHC
    Largest single CPI component (24%).
    """
    return _yoy("CUSR0000SEHC", "oer",
                "Owners Equivalent Rent (OER) index",
                "Index (1982=100)",
                "Lags market rents by 12-15 months; 24% CPI weight")


# ── FOOD ───────────────────────────────────────────────────────────────────

def fetch_food_home() -> dict:
    """BLS Food at home CPI — CUSR0000SAF11"""
    return _yoy("CUSR0000SAF11", "food_home",
                "Food at home (BLS CPI series)",
                "Index (1982=100)",
                "8.7% CPI weight; driven by commodities + energy")


def fetch_food_away() -> dict:
    """BLS Food away from home CPI — CUSR0000SEFV"""
    return _yoy("CUSR0000SEFV", "food_away",
                "Food away from home (BLS CPI series)",
                "Index (1982=100)",
                "4.8% CPI weight; driven by labor costs (~40% of restaurant cost)")


def fetch_corn_ppi() -> dict:
    """USDA corn price received by farmers — WPU012201"""
    return _yoy("WPU012201", "corn_ppi",
                "Corn PPI (producer price)",
                "Index",
                "Leading indicator for food_home; 2-6 month lag")


def fetch_wheat_ppi() -> dict:
    """Wheat PPI — WPU012101"""
    return _yoy("WPU012101", "wheat_ppi",
                "Wheat PPI (producer price)",
                "Index",
                "Leading indicator for cereals & bakery; 1-4 month lag")


# ── VEHICLES ───────────────────────────────────────────────────────────────

def fetch_used_vehicles() -> dict:
    """
    Manheim Used Vehicle Value Index via FRED — MVPHGVS
    Leads BLS used vehicle CPI by ~3 months.
    """
    return _yoy("CUSR0000SETA02", "used_vehicles",
                "Used vehicles CPI (BLS series)",
                "Index (1982=100)",
                "1.8% CPI weight; highly volatile")


def fetch_new_vehicles() -> dict:
    """New vehicles CPI — CUSR0000SETA01"""
    return _yoy("CUSR0000SETA01", "new_vehicles",
                "New vehicles CPI (BLS series)",
                "Index (1982=100)",
                "3.0% CPI weight")


# ── MEDICAL ────────────────────────────────────────────────────────────────

def fetch_medical() -> dict:
    """Medical care services CPI — CUSR0000SAM2"""
    return _yoy("CUSR0000SAM2", "medical_services",
                "Medical care services CPI",
                "Index (1982=100)",
                "7.0% CPI weight; sticky, upward bias")


# ── WAGES / LABOR ──────────────────────────────────────────────────────────

def fetch_wages() -> dict:
    """
    Average hourly earnings, all private employees — CES0500000003
    Wages are the dominant driver of services CPI (sticky).
    """
    return _yoy("CES0500000003", "wages",
                "Avg hourly earnings, all private ($/hr)",
                "$/hour",
                "CRITICAL leading indicator — services CPI follows wages 3-9m lag")


def fetch_employment_cost() -> dict:
    """Employment Cost Index — ECIALLCIV (quarterly)"""
    return _yoy("ECIALLCIV", "employment_cost",
                "Employment Cost Index",
                "Index",
                "Fed's preferred labor cost measure; quarterly")


# ── BROADER MACRO ──────────────────────────────────────────────────────────

def fetch_pce() -> dict:
    """PCE Price Index — PCEPI (Fed's preferred inflation measure)"""
    return _yoy("PCEPI", "pce",
                "PCE Price Index (Fed target)",
                "Index",
                "Fed 2% target; lower OER weight than CPI")


def fetch_core_pce() -> dict:
    """Core PCE (ex food & energy) — PCEPILFE"""
    return _yoy("PCEPILFE", "core_pce",
                "Core PCE (ex food & energy)",
                "Index",
                "Fed's primary policy target")


def fetch_ppi_final() -> dict:
    """PPI Final Demand — PPIFID (leads CPI by ~2-3 months)"""
    return _yoy("PPIFID", "ppi_final",
                "PPI Final Demand",
                "Index",
                "Leading CPI indicator; 2-3 month pass-through")


def fetch_import_prices() -> dict:
    """Import Price Index — IR (USD strength → deflation)"""
    return _yoy("IR", "import_prices",
                "Import Price Index",
                "Index",
                "USD +10% → import prices -3% → CPI goods -0.3%")


def fetch_inflation_expectations() -> dict:
    """
    University of Michigan 1-year inflation expectations — MICH
    Self-fulfilling: expectations shape wage demands and pricing.
    """
    return _yoy("MICH", "inflation_expectations",
                "UMich 1yr inflation expectations (%)",
                "%",
                "Self-fulfilling; key for services stickiness")


def fetch_all() -> list:
    fetchers = [
        fetch_rent_index, fetch_oer,
        fetch_food_home, fetch_food_away, fetch_corn_ppi, fetch_wheat_ppi,
        fetch_used_vehicles, fetch_new_vehicles,
        fetch_medical,
        fetch_wages, fetch_employment_cost,
        fetch_pce, fetch_core_pce, fetch_ppi_final,
        fetch_import_prices, fetch_inflation_expectations,
    ]
    results = []
    for fn in fetchers:
        try:
            r = fn()
            if r:
                results.append(r)
                print(f"  ✓ FRED: {r['label']} → {r['yoy_pct']:+.1f}% YoY")
        except Exception as e:
            print(f"  ✗ FRED {fn.__name__}: {e}")
    return results


if __name__ == "__main__":
    print("Testing FRED scraper...")
    data = fetch_all()
    print(f"\nFetched {len(data)} series")
