"""
CPI basket weights — BLS CPI-U 2023-2024
Single source of truth used by all modules.
"""

WEIGHTS = {
    # Housing (34.4%)
    "oer":                  {"weight": 24.0, "category": "housing",       "core": True,  "label": "Owners Equiv. Rent"},
    "rent":                 {"weight":  7.7, "category": "housing",       "core": True,  "label": "Rent of residence"},
    "utilities":            {"weight":  4.5, "category": "housing",       "core": True,  "label": "Utilities & fuel"},
    "furnishings":          {"weight":  4.0, "category": "housing",       "core": True,  "label": "Household furnishings"},

    # Food (13.5%)
    "food_home":            {"weight":  8.7, "category": "food",          "core": False, "label": "Food at home"},
    "food_away":            {"weight":  4.8, "category": "food",          "core": False, "label": "Food away from home"},

    # Energy (6.9%)
    "gasoline":             {"weight":  3.4, "category": "energy",        "core": False, "label": "Gasoline"},
    "electricity":          {"weight":  2.9, "category": "energy",        "core": False, "label": "Electricity"},
    "natural_gas":          {"weight":  0.9, "category": "energy",        "core": False, "label": "Natural gas"},
    "fuel_oil":             {"weight":  0.3, "category": "energy",        "core": False, "label": "Fuel oil"},

    # Transportation (8.1%)
    "new_vehicles":         {"weight":  3.0, "category": "transport",     "core": True,  "label": "New vehicles"},
    "used_vehicles":        {"weight":  1.8, "category": "transport",     "core": True,  "label": "Used vehicles"},
    "vehicle_insurance":    {"weight":  2.1, "category": "transport",     "core": True,  "label": "Vehicle insurance"},
    "public_transport":     {"weight":  0.7, "category": "transport",     "core": True,  "label": "Public transport"},
    "vehicle_repair":       {"weight":  0.5, "category": "transport",     "core": True,  "label": "Vehicle repair"},

    # Medical (8.8%)
    "medical_services":     {"weight":  7.0, "category": "medical",       "core": True,  "label": "Medical services"},
    "medical_goods":        {"weight":  1.8, "category": "medical",       "core": True,  "label": "Drugs & equipment"},

    # Education & Communication (6.5%)
    "tuition":              {"weight":  2.8, "category": "education",     "core": True,  "label": "Tuition & fees"},
    "communication":        {"weight":  3.7, "category": "education",     "core": True,  "label": "Communication"},

    # Recreation (5.7%)
    "recreation_tech":      {"weight":  1.8, "category": "recreation",    "core": True,  "label": "Video/audio/tech"},
    "recreation_admissions":{"weight":  1.9, "category": "recreation",    "core": True,  "label": "Admissions & sports"},
    "pets":                 {"weight":  2.0, "category": "recreation",    "core": True,  "label": "Pets & related"},

    # Apparel (2.4%)
    "apparel":              {"weight":  2.4, "category": "apparel",       "core": True,  "label": "Apparel"},

    # Other (4.1%)
    "tobacco":              {"weight":  0.9, "category": "other",         "core": True,  "label": "Tobacco"},
    "personal_care":        {"weight":  2.4, "category": "other",         "core": True,  "label": "Personal care"},
    "misc_services":        {"weight":  0.8, "category": "other",         "core": True,  "label": "Misc. services"},
}

# Category-level rollups
CATEGORIES = {
    "housing":     {"label": "Housing",              "color": "#1F4E79"},
    "food":        {"label": "Food",                 "color": "#2D8653"},
    "energy":      {"label": "Energy",               "color": "#C55A11"},
    "transport":   {"label": "Transportation",       "color": "#7B3F00"},
    "medical":     {"label": "Medical Care",         "color": "#843C0C"},
    "education":   {"label": "Education & Comm.",    "color": "#4472C4"},
    "recreation":  {"label": "Recreation",           "color": "#7030A0"},
    "apparel":     {"label": "Apparel",              "color": "#595959"},
    "other":       {"label": "Other",                "color": "#404040"},
}

def total_weight():
    return sum(v["weight"] for v in WEIGHTS.values())

def core_weights():
    return {k: v for k, v in WEIGHTS.items() if v["core"]}

def non_core_weights():
    return {k: v for k, v in WEIGHTS.items() if not v["core"]}
