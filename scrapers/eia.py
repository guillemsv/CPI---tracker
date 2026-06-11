"""
EIA API scraper — gasoline, electricity, natural gas
Free API: https://www.eia.gov/opendata/register.php
Covers: gasoline (3.4%), electricity (2.9%), natural gas (0.9%) = 7.2% of CPI
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

EIA_KEY = os.getenv("EIA_API_KEY", "")
BASE = "https://api.eia.gov/v2"


def _get(series_id: str, frequency: str = "weekly") -> pd.DataFrame:
    """Fetch a single EIA series, return DataFrame with date + value columns."""
    url = f"{BASE}/seriesid/{series_id}"
    params = {
        "api_key": EIA_KEY,
        "frequency": frequency,
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 60,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("response", {}).get("data", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)[["period", "value"]].copy()
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("period")


def fetch_gasoline() -> dict:
    """
    Weekly US regular gasoline retail price ($/gallon).
    Series: EMM_EPMR_PTE_NUS_DPG
    """
    df = _get("EMM_EPMR_PTE_NUS_DPG", "weekly")
    if df.empty:
        return {}
    latest = df.iloc[-1]
    year_ago = df[df["period"] <= latest["period"] - timedelta(days=350)]
    if year_ago.empty:
        return {}
    year_ago_val = year_ago.iloc[-1]["value"]
    yoy = ((latest["value"] - year_ago_val) / year_ago_val) * 100

    return {
        "component": "gasoline",
        "label": "Gasoline (regular, $/gal)",
        "date": latest["period"].strftime("%Y-%m-%d"),
        "price": round(float(latest["value"]), 3),
        "price_year_ago": round(float(year_ago_val), 3),
        "yoy_pct": round(float(yoy), 2),
        "unit": "$/gallon",
        "source": "EIA",
        "series": "EMM_EPMR_PTE_NUS_DPG",
    }


def fetch_electricity() -> dict:
    """
    Monthly US average electricity retail price (cents/kWh).
    Series: ELEC.PRICE.US-ALL.M
    """
    df = _get("ELEC.PRICE.US-ALL.M", "monthly")
    if df.empty:
        return {}
    latest = df.iloc[-1]
    year_ago = df[df["period"] <= latest["period"] - timedelta(days=350)]
    if year_ago.empty:
        return {}
    year_ago_val = year_ago.iloc[-1]["value"]
    yoy = ((latest["value"] - year_ago_val) / year_ago_val) * 100

    return {
        "component": "electricity",
        "label": "Electricity (US avg, cents/kWh)",
        "date": latest["period"].strftime("%Y-%m-%d"),
        "price": round(float(latest["value"]), 3),
        "price_year_ago": round(float(year_ago_val), 3),
        "yoy_pct": round(float(yoy), 2),
        "unit": "cents/kWh",
        "source": "EIA",
        "series": "ELEC.PRICE.US-ALL.M",
    }


def fetch_natural_gas() -> dict:
    """
    Monthly US natural gas citygate price ($/MCF).
    Series: NG.N3010US3.M
    """
    df = _get("NG.N3010US3.M", "monthly")
    if df.empty:
        return {}
    latest = df.iloc[-1]
    year_ago = df[df["period"] <= latest["period"] - timedelta(days=350)]
    if year_ago.empty:
        return {}
    year_ago_val = year_ago.iloc[-1]["value"]
    yoy = ((latest["value"] - year_ago_val) / year_ago_val) * 100

    return {
        "component": "natural_gas",
        "label": "Natural gas (citygate, $/MCF)",
        "date": latest["period"].strftime("%Y-%m-%d"),
        "price": round(float(latest["value"]), 3),
        "price_year_ago": round(float(year_ago_val), 3),
        "yoy_pct": round(float(yoy), 2),
        "unit": "$/MCF",
        "source": "EIA",
        "series": "NG.N3010US3.M",
    }


def fetch_crude_oil() -> dict:
    """
    Weekly WTI crude oil spot price ($/barrel) — leading indicator.
    Series: PET.RWTC.W
    """
    df = _get("PET.RWTC.W", "weekly")
    if df.empty:
        return {}
    latest = df.iloc[-1]
    year_ago = df[df["period"] <= latest["period"] - timedelta(days=350)]
    if year_ago.empty:
        return {}
    year_ago_val = year_ago.iloc[-1]["value"]
    yoy = ((latest["value"] - year_ago_val) / year_ago_val) * 100

    return {
        "component": "crude_oil",
        "label": "WTI crude oil ($/barrel)",
        "date": latest["period"].strftime("%Y-%m-%d"),
        "price": round(float(latest["value"]), 3),
        "price_year_ago": round(float(year_ago_val), 3),
        "yoy_pct": round(float(yoy), 2),
        "unit": "$/barrel",
        "source": "EIA",
        "series": "PET.RWTC.W",
        "note": "Leading indicator — feeds gasoline with ~2 week lag",
    }


def fetch_all() -> list:
    results = []
    for fn in [fetch_gasoline, fetch_electricity, fetch_natural_gas, fetch_crude_oil]:
        try:
            r = fn()
            if r:
                results.append(r)
                print(f"  ✓ EIA: {r['label']} → {r['yoy_pct']:+.1f}% YoY")
        except Exception as e:
            print(f"  ✗ EIA {fn.__name__}: {e}")
    return results


if __name__ == "__main__":
    print("Testing EIA scraper...")
    data = fetch_all()
    for d in data:
        print(f"  {d['label']}: ${d['price']} ({d['yoy_pct']:+.1f}% YoY)")
