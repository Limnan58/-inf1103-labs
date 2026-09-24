# test_band.py
import config
import data_manager

catalog = data_manager.load_restaurants()
origin = data_manager.geocode_location("199029")
places = data_manager.fetch_nearby_restaurants(origin, {"max_walk_minutes": 15})
for p in places[:5]:
    c = data_manager.enrich_place(p, catalog)
    print(f"{c['name'][:28]:30} avg_price={c['avg_price']}  band={c['price_band']}  src={c['source']}")
