"""Smoke test: each Google API in dependency order. Billed-key edition."""
import config
import data_manager

print("Key loaded:", bool(config.GOOGLE_MAPS_API_KEY),
      "| length:", len(config.GOOGLE_MAPS_API_KEY))

# [1] Geocode — use a FRESH location so the cache can't fake a pass
origin = data_manager.geocode_location("Jurong East MRT")
if origin is None:
    print("[1] Geocode: FAIL — stop here, check table below")
else:
    print("[1] Geocode: PASS ->", origin)

    # [2] Places nearby
    places = data_manager.fetch_nearby_restaurants(origin, {"max_walk_minutes": 15})
    print(f"[2] Places: {'PASS' if places else 'FAIL'} — {len(places)} found")

    if places:
        # [3] Matrix — called DIRECTLY, no fallback, so None = matrix failed
        catalog = data_manager.load_restaurants()
        cands = [data_manager.enrich_place(p, catalog) for p in places[:5]]
        data_manager.walk_times_matrix(origin, cands)
        for c in cands:
            est = " <- ESTIMATE (matrix failed)" if c.get("walk_source") == "estimate" else ""
            print(f"[3] Matrix: {c['name'][:30]:32} -> {c.get('walk_minutes')} min{est}")

        # [4] On-demand route
        route = data_manager.get_walking_route(origin, (cands[0]["lat"], cands[0]["lng"]))
        if route:
            print(f"[4] Route: PASS -> {route['duration_min']} min, "
                  f"{route['distance_m']} m, {len(route['steps'])} steps")
        else:
            print("[4] Route: FAIL")
