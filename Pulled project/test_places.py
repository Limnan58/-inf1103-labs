# test_places_app.py
import requests
import config
import data_manager

location = input("Type the same location you used in the app: ")
origin = data_manager.geocode_location(location)
print("Origin:", origin)

body = {
    "includedTypes": ["restaurant", "cafe", "fast_food_restaurant"],
    "maxResultCount": 20,
    "rankPreference": "DISTANCE",
    "locationRestriction": {"circle": {
        "center": {"latitude": origin[0], "longitude": origin[1]},
        "radius": 1000,   # app uses 100m per walk-minute: 10 min -> 1000 m
    }},
}
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": config.GOOGLE_MAPS_API_KEY,
    "X-Goog-FieldMask": ("places.displayName,places.formattedAddress,"
                         "places.location,places.rating,places.priceLevel,places.types"),
}
resp = requests.post(config.PLACES_URL, headers=headers, json=body, timeout=15)
print("HTTP status:", resp.status_code)
print(resp.json())
