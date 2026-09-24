"""Data layer — system memory + all external data sources (Google APIs + Gemini).
Handles all external API calls. Fails gracefully — never crashes the app."""
import json
import os
import re
import time
import random
import requests
import config

# --- AI-powered dietary extraction (Gemini) ---
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List


# ---------- generic JSON helpers ----------

BAND_THRESHOLDS = (8.0, 15.0, 30.0)  # SG casual dining: <=8 $, <=15 $$, <=30 $$$, else $$$$

# Dietary extraction: rate-limit + cache
_GEMINI_DELAY_RANGE = (4.0, 5.0)   # seconds, keeps us under 15 RPM
_GEMINI_MAX_RETRIES = 3
_DIETARY_CACHE_FILE = "data/dietary_cache.json"


def price_to_band(avg_price):
    """Catalog dollars -> Google-style band, so both data sources compare equally."""
    for band, upper in zip(("inexpensive", "moderate", "expensive"), BAND_THRESHOLDS):
        if avg_price <= upper:
            return band
    return "very_expensive"


def _load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def _log_api_error(context, err):
    """Handle API failure gracefully - log and continue, never crash."""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/api_errors.log", "a", encoding="utf-8") as f:
            f.write(f"{context}: {type(err).__name__}: {err}\n")
    except OSError:
        pass


# ---------- catalog (flat file) ----------

def load_restaurants(path=config.RESTAURANT_FILE):
    """Load all records on startup. Missing or corrupt file -> empty list."""
    data = _load_json(path)
    return data if isinstance(data, list) else []


def filter_by_dietary(restaurants, dietary):
    return [r for r in restaurants if r.get("dietary") == dietary]


def find_by_name(restaurants, name):
    return [r for r in restaurants if name.lower() in r.get("name", "").lower()]


# ---------- Google Geocoding API (with permanent cache) ----------

def geocode_location(address_text):
    """'199029' / 'Bugis Junction' -> (lat, lng) or None. Cached forever."""
    key = (address_text or "").strip().lower()
    if not key:
        return None
    cache = _load_json(config.GEOCODE_CACHE_FILE)
    if not isinstance(cache, dict):
        cache = {}
    if key in cache:
        return tuple(cache[key])
    try:
        resp = requests.get(
            config.GEOCODE_URL,
            params={"address": address_text, "key": config.GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        loc = results[0]["geometry"]["location"]
        cache[key] = [loc["lat"], loc["lng"]]
        _save_json(config.GEOCODE_CACHE_FILE, cache)
        return loc["lat"], loc["lng"]
    except (requests.RequestException, KeyError, ValueError):
        return None


# ---------- Google Places API (New): nearby search ----------

_CUISINE_MAP = {
    "cafe": "cafe", "fast_food_restaurant": "fast food", "bakery": "bakery",
    "american_restaurant": "western", "pizza_restaurant": "western",
    "hamburger_restaurant": "western", "indian_restaurant": "indian",
    "malaysian_restaurant": "malaysian", "indonesian_restaurant": "indonesian",
}


def _cuisine_from_types(types):
    for t in types or []:
        if t in _CUISINE_MAP:
            return _CUISINE_MAP[t]
        if t.endswith("_restaurant"):
            return t[: -len("_restaurant")]
    return "unknown"


def _search_radius_m(req):
    """~80 m/min walking + buffer, clamped to Places limits (500-20000)."""
    walk = req.get("max_walk_minutes")
    return max(500, min((walk if walk else 15) * 100, 20000))


def _infer_dietary_from_google(place_json):
    """Scans Google's generative summary + servesVegetarianFood flag for dietary hints.
    Returns one of: 'halal', 'vegan', 'vegetarian', or 'unknown'.
    NOTE: This is INFERRED data, not verified certification."""
    summary_obj = place_json.get("generativeSummary") or {}
    overview = (summary_obj.get("overview") or {}).get("text", "")
    description = (summary_obj.get("description") or {}).get("text", "")
    full_text = (overview + " " + description).lower()

    if "halal" in full_text or "清真" in full_text:
        return "halal"
    if "vegan" in full_text:
        return "vegan"
    if "vegetarian" in full_text or "veggie" in full_text:
        return "vegetarian"
    if place_json.get("servesVegetarianFood") is True:
        return "vegetarian"
    return "unknown"


def fetch_nearby_restaurants(origin, req):
    """ONE Places request per search (up to 20 places in the response). [] on failure."""
    lat, lng = origin
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.priceLevel,"
            "places.types,places.servesVegetarianFood,"
            "places.generativeSummary,places.reviews"
        ),
    }
    body = {
        "includedTypes": ["restaurant", "cafe", "fast_food_restaurant"],
        "maxResultCount": 20,
        "rankPreference": "DISTANCE",
        "locationRestriction": {"circle": {
            "center": {"latitude": lat, "longitude": lng},
            "radius": _search_radius_m(req),
        }},
    }
    try:
        resp = requests.post(config.PLACES_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        places = []
        for p in resp.json().get("places", []):
            name = p.get("displayName", {}).get("text")
            if not name:
                continue

            # Collect review texts (Google returns up to 5)
            review_texts = []
            for review in p.get("reviews", []):
                text = review.get("text", {}).get("text", "")
                if text:
                    review_texts.append(text)

            places.append({
                "name": name,
                "address": p.get("formattedAddress", "unavailable"),
                "lat": p["location"]["latitude"],
                "lng": p["location"]["longitude"],
                "rating": p.get("rating"),
                "price_level": (p.get("priceLevel") or "").replace("PRICE_LEVEL_", "").lower() or None,
                "types": p.get("types", []),
                "dietary_hint": _infer_dietary_from_google(p),
                "reviews": review_texts,
            })
        return places
    except (requests.RequestException, KeyError, ValueError):
        return []


# ---------- AI-powered dietary extraction (Gemini) + cache ----------

class DietaryExtraction(BaseModel):
    """Schema for structured dietary extraction from reviews."""
    dietary: List[str] = Field(
        description="Confirmed dietary options mentioned: halal, vegetarian, vegan, gluten-free, etc. Empty list if none."
    )
    confidence: str = Field(
        description="One of: high, medium, low. High = explicitly stated as certified. Medium = mentioned clearly. Low = ambiguous or implied."
    )
    evidence: List[str] = Field(
        description="Exact quotes from reviews that support the dietary claims. Empty if none."
    )


# Singleton Gemini client (lazy-initialised)
_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _gemini_client


# ---------- dietary cache ----------

_dietary_cache = None   # in-memory cache (loaded once)


def _load_dietary_cache():
    """Lazy-loads the persistent dietary cache from disk."""
    global _dietary_cache
    if _dietary_cache is None:
        data = _load_json(_DIETARY_CACHE_FILE)
        _dietary_cache = data if isinstance(data, dict) else {}
    return _dietary_cache


def _save_dietary_cache():
    """Flushes the in-memory cache back to disk."""
    if _dietary_cache is not None:
        os.makedirs("data", exist_ok=True)
        _save_json(_DIETARY_CACHE_FILE, _dietary_cache)


# ---------- the actual Gemini call + retry ----------

def _call_gemini_for_dietary(reviews):
    """Makes the actual Gemini API call. Returns the parsed dict, or empty on failure."""
    empty = {"dietary": [], "confidence": "low", "evidence": []}
    if not reviews:
        return empty

    joined = "\n---\n".join(reviews)[:4000]

    prompt = (
        "You are a dietary-information extractor for a restaurant search app in Singapore.\n"
        "Read the following customer reviews and extract any confirmed dietary options.\n"
        "Pay special attention to: halal, vegetarian, vegan, gluten-free, kosher.\n"
        "Only report a dietary option if the reviews explicitly mention it.\n"
        "Do NOT guess. If nothing is mentioned, return an empty list.\n\n"
        f"REVIEWS:\n{joined}"
    )

    for attempt in range(_GEMINI_MAX_RETRIES):
        try:
            client = _get_gemini_client()
            response = client.models.generate_content(
                model=config.MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DietaryExtraction,
                    temperature=0,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            parsed = response.parsed
            if parsed is None:
                return empty
            return {
                "dietary": [d.lower() for d in parsed.dietary],
                "confidence": parsed.confidence.lower(),
                "evidence": parsed.evidence,
            }
        except Exception as err:
            err_str = str(err)
            is_rate_limit = ("429" in err_str) or ("RESOURCE_EXHAUSTED" in err_str)

            if is_rate_limit and attempt < _GEMINI_MAX_RETRIES - 1:
                wait = 5 * (2 ** attempt)   # 5s, 10s, 20s
                print(f"    [rate-limit] Gemini 429 — retrying in {wait}s "
                      f"(attempt {attempt + 1}/{_GEMINI_MAX_RETRIES})")
                time.sleep(wait)
                continue

            _log_api_error("gemini_dietary_extraction", err)
            return empty

    return empty


def extract_dietary_from_reviews(restaurant_name, reviews):
    """Cached + rate-limited wrapper around the Gemini call.
    Cache key: normalised restaurant name.
    Returns: {"dietary": [...], "confidence": "...", "evidence": [...]}."""
    empty = {"dietary": [], "confidence": "low", "evidence": []}
    if not reviews:
        return empty

    cache = _load_dietary_cache()
    key = _norm(restaurant_name)

    # 1. Cache hit -> return immediately, no API call
    if key in cache:
        return cache[key]

    # 2. Cache miss -> rate-limit, then call
    delay = random.uniform(*_GEMINI_DELAY_RANGE)
    print(f"    [dietary] analysing '{restaurant_name}' "
          f"(waiting {delay:.1f}s to respect rate limit)...")
    time.sleep(delay)

    result = _call_gemini_for_dietary(reviews)

    # 3. Save result to cache (even empty results — saves future API calls)
    cache[key] = result
    _save_dietary_cache()
    return result


# ---------- enrichment: Places results x catalog ----------

def _norm(name):
    return re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).strip()


def _match_catalog(place, catalog):
    p = _norm(place["name"])
    for entry in catalog:
        e = _norm(entry.get("name", ""))
        if e and (e == p or e in p or p in e):
            return entry
    return None


def enrich_place(place, catalog):
    """Merge catalog fields into a Places result.
    Dietary priority: catalog (verified) > Gemini reviews (inferred) > Google summary (inferred) > unknown.
    Missing data stays None/'unknown' — never invented (business rule)."""
    entry = _match_catalog(place, catalog)
    google_hint = place.get("dietary_hint", "unknown")

    # Only call Gemini if the catalog doesn't already have verified dietary data.
    catalog_has_dietary = bool(
        entry and entry.get("dietary") and entry.get("dietary") != "unknown"
    )

    ai_result = {"dietary": [], "confidence": "low", "evidence": []}
    if not catalog_has_dietary:
        ai_result = extract_dietary_from_reviews(
            place["name"], place.get("reviews", [])
        )

    # --- Decide the final dietary value and its source ---
    if catalog_has_dietary:
        dietary_value = entry["dietary"]
        dietary_source = "catalog (verified)"
    elif ai_result["dietary"]:
        dietary_value = ai_result["dietary"][0]
        dietary_source = f"gemini reviews (inferred, {ai_result['confidence']} confidence)"
    elif google_hint != "unknown":
        dietary_value = google_hint
        dietary_source = "google places (inferred)"
    else:
        dietary_value = "unknown"
        dietary_source = "unknown"

    if entry:
        return {
            "name": entry.get("name", place["name"]),
            "address": place["address"],
            "lat": place["lat"], "lng": place["lng"],
            "cuisine": entry.get("cuisine") or _cuisine_from_types(place["types"]),
            "dietary": dietary_value,
            "dietary_source": dietary_source,
            "dietary_evidence": ai_result["evidence"],
            "allergens": entry.get("allergens"),
            "avg_price": entry.get("avg_price"),
            "price_band": (price_to_band(entry["avg_price"])
                           if entry.get("avg_price") is not None else None),
            "price_level": place["price_level"],
            "open_hours": entry.get("open_hours"),
            "spicy_options": entry.get("spicy_options"),
            "certification": entry.get("certification", "unknown"),
            "walk_minutes": None,
            "source": "catalog + google places",
        }

    return {
        "name": place["name"],
        "address": place["address"],
        "lat": place["lat"], "lng": place["lng"],
        "cuisine": _cuisine_from_types(place["types"]),
        "dietary": dietary_value,
        "dietary_source": dietary_source,
        "dietary_evidence": ai_result["evidence"],
        "allergens": None,
        "avg_price": None,
        "price_band": place["price_level"],
        "price_level": place["price_level"],
        "open_hours": None,
        "spicy_options": None,
        "certification": "unknown",
        "walk_minutes": None,
        "source": "google places (partial data)",
    }


# ---------- Google Routes API: matrix (walk times) + on-demand route ----------

def walk_times_matrix(origin, restaurants):
    """ONE request for ALL restaurants. Sets r['walk_minutes'] (minutes or None)."""
    if not restaurants:
        return
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": ("originIndex,destinationIndex,duration,"
                             "distanceMeters,status,condition"),
    }
    body = {
        "origins": [{"waypoint": {"location": {"latLng": {
            "latitude": origin[0], "longitude": origin[1]}}}}],
        "destinations": [{"waypoint": {"location": {"latLng": {
            "latitude": r["lat"], "longitude": r["lng"]}}}} for r in restaurants],
        "travelMode": "WALK",
    }
    try:
        resp = requests.post(config.MATRIX_URL, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        elements = data if isinstance(data, list) else data.get("elements", [])
        for el in elements:
            try:
                idx = el["destinationIndex"]
                if el.get("condition") == "ROUTE_NOT_FOUND":
                    continue
                status_code = (el.get("status") or {}).get("code", 0)
                if status_code not in (0, None):
                    continue
                minutes = round(int(el["duration"].rstrip("s")) / 60)
                restaurants[idx]["walk_minutes"] = minutes
                restaurants[idx]["walk_source"] = "routes-api"
            except (KeyError, ValueError, TypeError):
                continue
    except (requests.RequestException, AttributeError, KeyError, ValueError) as err:
        _log_api_error("routes_matrix", err)


def get_walking_route(origin, destination):
    """ONE on-demand call for the user's chosen restaurant. None on failure."""
    body = {
        "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
        "destination": {"location": {"latLng": {"latitude": destination[0], "longitude": destination[1]}}},
        "travelMode": "WALK",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": ("routes.duration,routes.distanceMeters,"
                             "routes.legs.steps.navigationInstruction"),
    }
    try:
        resp = requests.post(config.ROUTES_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        routes = resp.json().get("routes", [])
        if not routes:
            return None
        route = routes[0]
        steps = []
        for leg in route.get("legs", []):
            for s in leg.get("steps", []):
                text = s.get("navigationInstruction", {}).get("instructions")
                if text:
                    steps.append(text)
        return {"duration_min": round(int(route["duration"].rstrip("s")) / 60),
                "distance_m": route["distanceMeters"],
                "steps": steps}
    except (requests.RequestException, KeyError, ValueError):
        return None


def build_maps_link(origin, destination):
    """Free, no API call — opens the walking route in Google Maps."""
    return (f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin[0]},{origin[1]}"
            f"&destination={destination[0]},{destination[1]}&travelmode=walking")


# ---------- candidate builder (the only function main.py needs) ----------

def build_candidates(origin, req, catalog):
    """Live mode: Places -> catalog enrichment -> Routes walk times.
    Offline mode: catalog only (deterministic; demo backup)."""
    if not config.USE_LIVE_GOOGLE:
        return [dict(r) for r in catalog]
    places = fetch_nearby_restaurants(origin, req)
    if not places:
        return []
    candidates, seen = [], set()
    for p in places:
        c = enrich_place(p, catalog)
        key = _norm(c["name"])
        if key not in seen:
            seen.add(key)
            candidates.append(c)
    walk_times_matrix(origin, candidates)
    return candidates


# ---------- search history ----------

def load_history(path=config.HISTORY_FILE):
    data = _load_json(path)
    return data if isinstance(data, list) else []


def save_history(entry, path=config.HISTORY_FILE):
    history = load_history(path)
    history.append(entry)
    return _save_json(path, history)


# ---------- user profile (persistent preferences) ----------

def load_user_profile():
    """Loads the user profile from a JSON file. Returns {} if missing or corrupt."""
    data = _load_json(config.PROFILE_FILE)
    return data if isinstance(data, dict) else {}


def save_user_profile(profile):
    """Saves the user profile to a JSON file. Returns True on success."""
    return _save_json(config.PROFILE_FILE, profile)