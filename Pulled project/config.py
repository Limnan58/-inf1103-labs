import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_ID = "gemini-3.5-flash-lite"

# --- Google Maps Platform (data layer) ---
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"
MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# Set USE_LIVE_GOOGLE=false in .env for offline catalog mode
USE_LIVE_GOOGLE = os.getenv("USE_LIVE_GOOGLE", "true").lower() == "true"

# --- Files ---
RESTAURANT_FILE = "data/restaurants.json"
HISTORY_FILE = "data/search_history.json"
GEOCODE_CACHE_FILE = "data/geocode_cache.json"
PROFILE_FILE = "data/user_profile.json"   # <-- moved into data/