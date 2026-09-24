"""Logic layer — business rules applied to the AI-enriched record."""
from datetime import datetime
from io_manager import BAND_SYMBOLS

ALLOWED_DIETARY = {
    "none": {"none", "vegetarian", "vegan", "halal"},
    "halal": {"halal"},
    "vegetarian": {"vegetarian", "vegan"},
    "vegan": {"vegan"},
}

BAND_ORDER = ["inexpensive", "moderate", "expensive", "very_expensive"]


# --- HELPER FUNCTIONS TO HANDLE MESSY AI OUTPUT ---

def _ensure_list(val):
    """Forces a value to be a list of lowercase strings.
    Handles None, strings, and lists."""
    if val is None:
        return []
    if isinstance(val, str):
        return [val.lower().strip()]
    if isinstance(val, list):
        return [str(v).lower().strip() for v in val if v is not None]
    return [str(val).lower().strip()]


def _ensure_str(val, default=""):
    """Forces a value to be a single lowercase string.
    If it's a list, it joins it into one string."""
    if val is None:
        return default.lower()
    if isinstance(val, list):
        return " ".join(str(v) for v in val).lower()
    return str(val).lower()


def _safe_float(val):
    """Safely converts a value to a float, returns None if it fails."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Safely converts a value to an int, returns None if it fails."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _band_index(band):
    return BAND_ORDER.index(band) if band in BAND_ORDER else -1


def _minutes(hhmm):
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return None


# --- MAIN LOGIC FUNCTIONS ---

def open_status(restaurant, eat_time):
    hours = restaurant.get("open_hours")
    if not hours or "-" not in hours:
        return "unknown"

    parts = hours.split("-")
    if len(parts) != 2:
        return "unknown"  # Handles complex hours like "10:00-14:00, 17:00-22:00"

    start = _minutes(parts[0].strip())
    end = _minutes(parts[1].strip())
    if start is None or end is None:
        return "unknown"

    if eat_time == "now":
        now = datetime.now()
        t = now.hour * 60 + now.minute
    else:
        t = _minutes(eat_time)
        if t is None:
            return "unknown"

    return "open" if start <= t <= end else "closed"


def decide_outcome(restaurant, req):
    """MULTI-CONDITION RULE using AI output fields.
    Hard rules (dietary, allergies) -> reject. Relaxable (budget, walk, rating)
    -> alternative. Unverifiable unknowns -> alternative. Otherwise scored match.

    Dietary data:
      - Verified (from catalog)  -> treated as a hard rule.
      - Inferred (from Google)   -> still allowed as a match, but WARNED."""
    reasons = []

    # --- HARD RULE 1: dietary ---
    wanted_diets = _ensure_list(req.get("dietary"))
    if not wanted_diets:
        wanted_diets = ["none"]

    r_dietary = _ensure_str(restaurant.get("dietary", "none"))
    dietary_source = _ensure_str(restaurant.get("dietary_source", "catalog (verified)"))
    is_inferred = "inferred" in dietary_source

    for wanted in wanted_diets:
        if r_dietary == "unknown":
            if wanted != "none":
                return "alternative", 0, [
                    "dietary certification unknown — please confirm with the restaurant"
                ]
        elif r_dietary not in ALLOWED_DIETARY.get(wanted, set()):
            return "reject", 0, [f"dietary requirement not met ({wanted})"]
        elif is_inferred and wanted != "none":
            # Dietary matches, but it was INFERRED (not verified) -> warn the user.
            reasons.append(
                f"⚠️ dietary '{r_dietary}' inferred from Google — "
                "please confirm with the restaurant"
            )

    # --- HARD RULE 2: allergies ---
    wanted_allergies = set(_ensure_list(req.get("allergies")))
    if wanted_allergies:
        allergens = restaurant.get("allergens")
        if allergens is None:
            return "alternative", 0, [
                "ingredient information unavailable — cannot verify your allergies"
            ]

        restaurant_allergens = set(_ensure_list(allergens))
        overlap = wanted_allergies & restaurant_allergens
        if overlap:
            return "reject", 0, [
                f"contains allergen(s): {', '.join(sorted(overlap))} "
                "(confirm with restaurant — never assumed allergy-safe)"
            ]

    # --- RELAXABLE: budget band, walking time, rating ---
    wanted_band = _ensure_str(req.get("budget_band"))
    r_band = _ensure_str(restaurant.get("price_band"))

    r_walk = _safe_int(restaurant.get("walk_minutes"))
    walk = _safe_int(req.get("max_walk_minutes"))

    rating = _safe_float(restaurant.get("rating"))
    min_rating = _safe_float(req.get("min_rating"))

    if wanted_band and r_band and wanted_band in BAND_ORDER and r_band in BAND_ORDER:
        if _band_index(r_band) > _band_index(wanted_band):
            sym_w = BAND_SYMBOLS.get(wanted_band, wanted_band)
            sym_r = BAND_SYMBOLS.get(r_band, r_band)
            return "alternative", 0, [f"price band {sym_r} exceeds your {sym_w} budget"]

    if walk is not None and r_walk is not None and r_walk > walk:
        return "alternative", 0, [f"would need to walk {r_walk - walk} more minutes"]

    if min_rating is not None and rating is not None and rating < min_rating:
        return "alternative", 0, [f"rating {rating} is below your {min_rating} minimum"]

    # --- UNVERIFIABLE DATA (relevant unknowns -> alternative) ---
    unknowns = []
    if wanted_band and not r_band:
        unknowns.append("price band unavailable — cannot verify budget")
    if walk is not None and r_walk is None:
        unknowns.append("walking time unavailable — cannot verify distance")
    if min_rating is not None and rating is None:
        unknowns.append("rating unavailable — cannot verify quality")
    if unknowns:
        return "alternative", 0, unknowns

    # --- PREFERENCES (only scored after all rules pass) ---
    score = 0

    cuisine = _ensure_str(req.get("cuisine"), "any")
    r_cuisine = _ensure_str(restaurant.get("cuisine"), "")

    if cuisine not in ("any", "") and cuisine in r_cuisine:
        score += 3
        reasons.append("matches your cuisine preference")

    if wanted_band and r_band and wanted_band in BAND_ORDER and r_band in BAND_ORDER:
        if _band_index(r_band) < _band_index(wanted_band):
            score += 1
            reasons.append(f"cheaper than your {BAND_SYMBOLS.get(wanted_band, wanted_band)} budget")

    if rating is not None and rating >= 4.5:
        score += 1
        reasons.append("highly rated (4.5+)")

    status = open_status(restaurant, req.get("eat_time", "now"))
    if status == "open":
        score += 1
        reasons.append("open at your requested time")
    elif status == "unknown":
        reasons.append("opening hours unknown — please confirm with the restaurant")
    else:
        score -= 1
        reasons.append("likely closed at your requested time")

    # Fixed: "free_text" (matches io_manager output)
    free_text = _ensure_str(req.get("free_text"))
    if "spicy" in free_text and restaurant.get("spicy_options"):
        score += 1
        reasons.append("has spicy options")

    if not reasons:
        reasons.append("meets all your hard requirements")

    return "match", score, reasons


def rank_restaurants(restaurants, req):
    matches, alternatives = [], []
    for r in restaurants:
        status, score, reasons = decide_outcome(r, req)
        if status == "match":
            matches.append({"restaurant": r, "score": score, "reasons": reasons})
        elif status == "alternative":
            alternatives.append({"restaurant": r, "score": 0, "reasons": reasons})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches[:3], "alternatives": alternatives[:3]}