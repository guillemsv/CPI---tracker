"""
CPI Calculator — applies BLS weights to scraped price data.
Produces headline CPI estimate + core CPI estimate.
"""

import json
import pandas as pd
from datetime import datetime
from processing.weights import WEIGHTS, CATEGORIES


# Map scraped component names → CPI weight keys
COMPONENT_MAP = {
    # Direct BLS series (best match)
    "headline_cpi":       None,   # is the target, not an input
    "core_cpi":           None,
    "rent":               "rent",
    "oer":                "oer",
    "food_home":          "food_home",
    "food_away":          "food_away",
    "used_vehicles":      "used_vehicles",
    "new_vehicles":       "new_vehicles",
    "medical_services":   "medical_services",

    # EIA series
    "gasoline":           "gasoline",
    "electricity":        "electricity",
    "natural_gas":        "natural_gas",

    # Zillow — proxy for OER
    "zori":               "oer",   # use as OER proxy if BLS OER missing

    # FRED macro (not direct CPI components — used as signals)
    "wages":              None,
    "employment_cost":    None,
    "ppi_final":          None,
    "import_prices":      None,
    "inflation_expectations": None,
    "pce":                None,
    "core_pce":           None,
    "corn_ppi":           None,
    "wheat_ppi":          None,
}


def compute_cpi_estimate(scraped_data: list) -> dict:
    """
    Given a list of scraped price records, compute a weighted CPI estimate.

    Logic:
    1. Map each scraped record to a CPI weight key
    2. For each weight key, use the YoY% from scraped data
    3. Weighted average of all covered components
    4. For uncovered components, use last known BLS value or fallback
    """
    # Build lookup: weight_key → yoy_pct
    yoy_by_component = {}
    for record in scraped_data:
        comp = record.get("component")
        weight_key = COMPONENT_MAP.get(comp)
        if weight_key and record.get("yoy_pct") is not None:
            # If multiple sources for same key, prefer BLS official
            if weight_key not in yoy_by_component or record.get("is_official"):
                yoy_by_component[weight_key] = {
                    "yoy_pct": record["yoy_pct"],
                    "date": record.get("date"),
                    "source": record.get("source"),
                    "label": record.get("label"),
                }

    # Fallback values for components we can't scrape (historical averages)
    FALLBACKS = {
        "utilities":         3.5,
        "furnishings":       0.5,
        "vehicle_insurance": 8.0,
        "public_transport":  4.5,
        "vehicle_repair":    5.5,
        "medical_goods":     2.5,
        "tuition":           3.2,
        "communication":     1.2,
        "recreation_tech":  -2.0,
        "recreation_admissions": 5.0,
        "pets":              3.5,
        "apparel":           0.5,
        "tobacco":           5.0,
        "personal_care":     4.0,
        "misc_services":     3.5,
        "fuel_oil":          2.0,
    }

    # Compute weighted CPI
    total_weight_covered = 0
    total_weight_all = sum(v["weight"] for v in WEIGHTS.values())
    weighted_sum = 0
    core_weighted_sum = 0
    core_weight_covered = 0

    component_details = []

    for key, info in WEIGHTS.items():
        w = info["weight"]
        is_core = info["core"]

        if key in yoy_by_component:
            yoy = yoy_by_component[key]["yoy_pct"]
            source = yoy_by_component[key]["source"]
            covered = True
        elif key in FALLBACKS:
            yoy = FALLBACKS[key]
            source = "Fallback (historical avg)"
            covered = True
        else:
            yoy = None
            source = "Not available"
            covered = False

        contribution_bp = round(w * yoy / 100 * 100, 2) if yoy is not None else None

        component_details.append({
            "key": key,
            "label": info["label"],
            "category": info["category"],
            "weight": w,
            "is_core": is_core,
            "yoy_pct": yoy,
            "contribution_bp": contribution_bp,
            "source": source,
            "covered": covered,
        })

        if yoy is not None:
            weighted_sum += w * yoy
            total_weight_covered += w
            if is_core:
                core_weighted_sum += w * yoy
                core_weight_covered += w

    # Scale to covered weight (normalize)
    headline_estimate = (weighted_sum / total_weight_covered) if total_weight_covered > 0 else None
    core_estimate = (core_weighted_sum / core_weight_covered) if core_weight_covered > 0 else None

    # Coverage ratio
    coverage_pct = round(total_weight_covered / total_weight_all * 100, 1)

    # Category breakdown
    category_summary = {}
    for cat_key, cat_info in CATEGORIES.items():
        cat_components = [c for c in component_details if c["category"] == cat_key]
        cat_weight = sum(c["weight"] for c in cat_components)
        cat_contrib = sum(c["contribution_bp"] for c in cat_components if c["contribution_bp"] is not None)
        covered_w = sum(c["weight"] for c in cat_components if c["covered"])
        avg_yoy = (sum(c["yoy_pct"] * c["weight"] for c in cat_components if c["yoy_pct"] is not None) /
                   covered_w) if covered_w > 0 else None
        category_summary[cat_key] = {
            "label": cat_info["label"],
            "color": cat_info["color"],
            "weight": cat_weight,
            "avg_yoy_pct": round(avg_yoy, 2) if avg_yoy is not None else None,
            "contribution_bp": round(cat_contrib, 1),
        }

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "estimate": {
            "headline_cpi_pct": round(headline_estimate, 2) if headline_estimate else None,
            "core_cpi_pct": round(core_estimate, 2) if core_estimate else None,
            "basket_coverage_pct": coverage_pct,
            "weight_covered": round(total_weight_covered, 1),
        },
        "category_breakdown": category_summary,
        "component_detail": sorted(component_details, key=lambda x: -x["weight"]),
    }


def add_official_benchmark(estimate: dict, official_data: list) -> dict:
    """Attach official BLS CPI values to the estimate for accuracy tracking."""
    for record in official_data:
        if record.get("component") == "headline_cpi":
            estimate["official"] = {
                "headline_cpi_pct": record.get("yoy_pct"),
                "date": record.get("date"),
                "source": "BLS Official",
            }
        elif record.get("component") == "core_cpi":
            if "official" not in estimate:
                estimate["official"] = {}
            estimate["official"]["core_cpi_pct"] = record.get("yoy_pct")

    # Compute accuracy if both available
    if "official" in estimate and estimate["estimate"].get("headline_cpi_pct"):
        diff = estimate["estimate"]["headline_cpi_pct"] - estimate["official"].get("headline_cpi_pct", 0)
        estimate["accuracy"] = {
            "error_pp": round(diff, 2),
            "note": f"Our estimate vs BLS: {diff:+.2f}pp"
        }

    return estimate


def save_output(estimate: dict, path: str = "output/cpi_latest.json"):
    """Save estimate to JSON."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(estimate, f, indent=2)
    print(f"\n✓ Saved estimate to {path}")


def append_history(estimate: dict, path: str = "output/history.csv"):
    """Append today's estimate to historical CSV."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = {
        "date": estimate["timestamp"][:10],
        "headline_estimate": estimate["estimate"].get("headline_cpi_pct"),
        "core_estimate": estimate["estimate"].get("core_cpi_pct"),
        "official_headline": estimate.get("official", {}).get("headline_cpi_pct"),
        "coverage_pct": estimate["estimate"].get("basket_coverage_pct"),
    }
    df_new = pd.DataFrame([row])
    if os.path.exists(path):
        df_existing = pd.read_csv(path)
        # Avoid duplicate dates
        df_existing = df_existing[df_existing["date"] != row["date"]]
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(path, index=False)
    print(f"✓ Updated history at {path}")
