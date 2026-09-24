"""Wires the four managers together. User -> io -> ai -> logic -> data."""
import config
import io_manager
import ai_manager
import logic_manager
import data_manager


def run_bitefinder():
    io_manager.print_welcome()
    catalog = data_manager.load_restaurants()        # load all records on startup
    if not catalog:
        io_manager.print_error(f"No catalog data found at {config.RESTAURANT_FILE}")
        return

    # 1. Load the user profile on startup
    profile = data_manager.load_user_profile()
    if profile:
        print(f"Welcome back, {profile.get('name', 'Guest')}!")

    while True:
        choice = input("\n1 = new search, q = quit :> ").strip().lower()
        if choice == "q":
            print("Goodbye!")
            break
        if choice != "1":
            continue

        # 2. Pass the profile to the IO layer
        record = io_manager.get_user_requirements(profile)

        # 3. Ask if they want to save this as their profile
        save_choice = input("Save these details to your profile? (y/n): ").strip().lower()
        if save_choice == 'y':
            profile = {
                "name": record.get("name"),
                "dietary": record.get("dietary"),
                "food_preference": record.get("food_preference"),
                "max_walk_minutes": record.get("max_walk_minutes"),
                "budget_band": record.get("budget_band"),
                "allergies": record.get("allergies"),
                "min_rating": record.get("min_rating"),
            }
            data_manager.save_user_profile(profile)
            print("Profile saved successfully!")

        # Remove 'name' before sending to AI so it doesn't get confused
        ai_record = record.copy()
        ai_record.pop("name", None)

        ok, req = ai_manager.call_ai(ai_record)                 # 2. AI LAYER (parses request)
        if not ok:
            io_manager.print_error(req)
            continue
        io_manager.print_parsed(req)

        origin = data_manager.geocode_location(record["location"])   # 4a. DATA: geocode
        if origin is None:
            io_manager.print_error("Could not find that location — try a Singapore "
                                   "postal code or a landmark name.")
            continue

        candidates = data_manager.build_candidates(origin, req, catalog)  # 4b. DATA: places + routes
        if not candidates:
            io_manager.print_error("No restaurants found near that location. Try another.")
            continue

        results = logic_manager.rank_restaurants(candidates, req)    # 3. LOGIC LAYER
        io_manager.print_results(results)

        chosen = io_manager.choose_restaurant(results)               # on-demand route
        route_link = None
        if chosen is not None:
            if chosen.get("lat") is None:
                io_manager.print_error("No coordinates stored for that restaurant "
                                       "— add lat/lng in the catalog.")
            else:
                dest = (chosen["lat"], chosen["lng"])
                route = data_manager.get_walking_route(origin, dest)
                route_link = data_manager.build_maps_link(origin, dest)
                io_manager.print_route(chosen["name"], route, route_link)

        # Clean the input record for history (drop the personal name)
        history_input = record.copy()
        history_input.pop("name", None)

        data_manager.save_history({                          # 4c. DATA: persist
            "input": history_input,
            "parsed": req,
            "mode": "live-google" if config.USE_LIVE_GOOGLE else "offline-catalog",
            "origin": list(origin),
            "top_matches": [m["restaurant"]["name"] for m in results["matches"]],
            "route_link": route_link,
        })


if __name__ == "__main__":
    run_bitefinder()