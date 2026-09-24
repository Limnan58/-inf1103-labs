"""
data_fetcher.py
================
BiteFinder — Restaurant Data Fetcher

Fetches real, nearby restaurant candidates for the pipeline to evaluate,
using free OpenStreetMap services (no API key required):

1. Nominatim  -> converts a location name (e.g. "Ang Mo Kio") into
                 latitude/longitude coordinates.
2. Overpass   -> finds restaurants within a radius of that point.

Walking time is ESTIMATED from straight-line distance at an average
walking speed — it is not a real routed walking time (that would need
a routing service like OSRM or Google Directions). This is flagged
clearly in the returned data so downstream logic doesn't treat it as
more accurate than it is.

This module has ZERO domain logic — it only fetches and lightly shapes
raw data. AIManager and LogicManager decide what to do with it.
"""

import math
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "BiteFinder/1.0 (student project)"}

AVERAGE_WALKING_SPEED_M_PER_MIN = 80  # roughly 4.8 km/h
DEFAULT_RADIUS_METERS = 1000  # used when no max walking time is given


def geocode_location(location: str):
    """
    Convert a place name into (latitude, longitude) using Nominatim.
    Returns None if the location can't be found or the request fails.
    """
    params = {
        "q": f"{location}, Singapore",
        "format": "json",
        "limit": 1,
    }
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None

    return float(results[0]["lat"]), float(results[0]["lon"])


def haversine_distance_m(lat1, lon1, lat2, lon2) -> float:
    """Straight-line distance between two coordinates, in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def fetch_nearby_restaurants(lat: float, lon: float, radius_m: int, max_results: int = 20):
    """
    Query Overpass for restaurants within radius_m meters of (lat, lon).
    Returns the raw list of OSM elements, or an empty list on failure.
    """
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="restaurant"](around:{radius_m},{lat},{lon});
      way["amenity"="restaurant"](around:{radius_m},{lat},{lon});
    );
    out center tags {max_results};
    """
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json().get("elements", [])
    except (requests.RequestException, ValueError):
        return []


def _extract_dietary_certification(tags: dict) -> str:
    """Read whatever diet-related tags OSM has, without inventing anything."""
    if tags.get("diet:halal") == "yes":
        return "Halal (OSM-tagged)"
    if tags.get("diet:vegan") == "yes":
        return "Vegan (OSM-tagged)"
    if tags.get("diet:vegetarian") == "yes":
        return "Vegetarian (OSM-tagged)"
    return "Unavailable"


def build_candidates(elements: list, user_lat: float, user_lon: float) -> list:
    """
    Convert raw OSM elements into the candidate record shape expected by
    AIManager (name, cuisine, price, walking_time, dietary_certification,
    allergens). Fields OSM doesn't provide are marked "Unavailable" rather
    than guessed, per BiteFinder's business rules.
    """
    candidates = []
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip unnamed entries, not useful for recommendations

        if "center" in element:
            r_lat, r_lon = element["center"]["lat"], element["center"]["lon"]
        else:
            r_lat, r_lon = element.get("lat"), element.get("lon")

        distance_m = haversine_distance_m(user_lat, user_lon, r_lat, r_lon)
        estimated_walking_time = round(distance_m / AVERAGE_WALKING_SPEED_M_PER_MIN, 1)

        candidates.append({
            "name": name,
            "cuisine": tags.get("cuisine", "Unavailable"),
            "price": None,  # OSM does not track price; left honest as unavailable
            "walking_time": estimated_walking_time,
            "walking_time_is_estimated": True,  # straight-line estimate, not routed
            "dietary_certification": _extract_dietary_certification(tags),
            "allergens": "Unavailable",
            "address": " ".join(filter(None, [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:postcode"),
            ])),
        })

    return candidates


def fetch_candidates_for_request(location: str, max_walking_time=None, max_results: int = 20) -> list:
    """
    Main entry point: given a location string and an optional max walking
    time (in minutes), return a list of real nearby restaurant candidates
    ready to be passed into AIManager. Returns an empty list (never raises)
    if geocoding or fetching fails.
    """
    coords = geocode_location(location)
    if coords is None:
        return []
    lat, lon = coords

    if max_walking_time:
        radius_m = int(max_walking_time * AVERAGE_WALKING_SPEED_M_PER_MIN)
    else:
        radius_m = DEFAULT_RADIUS_METERS

    time.sleep(1)  # be polite to the free Nominatim/Overpass services
    elements = fetch_nearby_restaurants(lat, lon, radius_m, max_results)
    return build_candidates(elements, lat, lon)
