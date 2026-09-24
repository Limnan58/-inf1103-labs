import requests
import config

# Security check: never print the key itself — just whether it loaded
print("Key loaded:", bool(config.GOOGLE_MAPS_API_KEY),
      "| length:", len(config.GOOGLE_MAPS_API_KEY))

resp = requests.get(
    config.GEOCODE_URL,
    params={"address": "199029", "key": config.GOOGLE_MAPS_API_KEY},
    timeout=10,
)
print("HTTP status:", resp.status_code)
print(resp.json())
