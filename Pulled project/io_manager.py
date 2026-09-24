"""Input layer — all user boundaries. Every input() and print() lives here.
Generic filters mirror Google Maps search filters (price band, rating,
open-now, distance); dietary/allergy/certification are BiteFinder's own."""

BAND_SYMBOLS = {
    "inexpensive": "$",
    "moderate": "$$",
    "expensive": "$$$",
    "very_expensive": "$$$$",
}


def print_welcome():
    print("=" * 55)
    print("  BiteFinder — food that fits your rules")
    print("=" * 55)


def ask_int(prompt, default=None):
    """Reject and re-prompt on bad data. Supports a default value."""
    prompt_display = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "
    while True:
        raw = input(prompt_display).strip()
        if raw == "":
            return default
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("  Please enter a positive whole number (e.g. 15).")


def ask_price_band(prompt, default=None):
    """Google Maps-style price filter: any / $ / $$ / $$$ / $$$$. Supports a default."""
    menu = {"any": None, "$": "inexpensive", "$$": "moderate",
            "$$$": "expensive", "$$$$": "very_expensive"}
    
    default_sym = "any"
    if default:
        for sym, band in menu.items():
            if band == default:
                default_sym = sym
                break
                
    prompt_display = f"{prompt} (any / $ / $$ / $$$ / $$$$) [{default_sym}]: "
    
    while True:
        raw = input(prompt_display).strip()
        if raw == "":
            return default
        if raw in menu:
            return menu[raw]
        print("  Please type any, $, $$, $$$ or $$$$.")


def ask_rating(prompt, default=None):
    """Google Maps-style rating filter: any / 4.0 / 4.5. Supports a default."""
    prompt_display = f"{prompt} (any / 4.0 / 4.5) [{default if default else 'any'}]: "
    
    while True:
        raw = input(prompt_display).strip().lower()
        if raw == "":
            return default
        if raw in ("any",):
            return None
        try:
            value = float(raw)
            if 1.0 <= value <= 5.0:
                return value
        except ValueError:
            pass
        print("  Enter 'any' or a rating between 1.0 and 5.0.")


def ask_choice(prompt, options, default=None):
    """Asks for a choice from a list. Supports a default."""
    prompt_display = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "
    while True:
        raw = input(prompt_display).strip().lower()
        if raw == "" and default is not None:
            return default
        if raw in options:
            return raw
        print(f"  Please type one of: {', '.join(options)}")


def get_user_requirements(profile=None):
    """Gathers user input. If a profile is provided, uses those as defaults."""
    profile = profile or {}
    
    print("\n--- Your request (Enter = use saved profile or skip optional) ---")
    
    name = input(f"Name [{profile.get('name', 'Guest')}]: ").strip() or profile.get('name', 'Guest')
    
    location = ""
    while not location:
        location = input("Location (SG postal code / address / landmark): ").strip()
        
    saved_allergies = profile.get("allergies", [])
    if isinstance(saved_allergies, str):
        saved_allergies = [saved_allergies]
    saved_allergies_str = ", ".join(saved_allergies) if saved_allergies else "none"
    
    allergies_raw = input(f"Allergies to avoid (comma separated) [{saved_allergies_str}]: ").strip()
    if allergies_raw == "":
        allergies = saved_allergies
    else:
        allergies = [a.strip() for a in allergies_raw.split(",") if a.strip()]

    return {
        "name": name,
        "location": location,
        "max_walk_minutes": ask_int("Max walking time (minutes)", profile.get("max_walk_minutes")),
        "budget_band": ask_price_band("Max budget", profile.get("budget_band")),
        "dietary": ask_choice("Dietary (none/halal/vegetarian/vegan): ",
                              ["none", "halal", "vegetarian", "vegan"],
                              profile.get("dietary", "none")),
        "allergies": allergies,
        "food_preference": input(f"Food/cuisine preference [{profile.get('food_preference', '')}]: ").strip() or profile.get('food_preference', ''),
        "min_rating": ask_rating("Min rating", profile.get("min_rating")),
        "eat_time": input("Open now or at a time (Enter = now / HH:MM): ").strip() or "now",
        "free_text": input("Anything else? (e.g. 'something spicy'): ").strip(),
    }


def _fmt_val(val):
    """Helper to cleanly format lists or strings for display."""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val) if val else "none"
    return val if val is not None and str(val).strip() != "" else "none"


def print_parsed(req):
    """Prints the AI-parsed request nicely, handling lists and strings."""
    band = BAND_SYMBOLS.get(req.get("budget_band"), "any")
    rating = req.get("min_rating")
    rating_txt = f"{rating}+" if rating else "any"
    
    cuisine = _fmt_val(req.get("cuisine"))
    dietary = _fmt_val(req.get("dietary"))
    allergies = _fmt_val(req.get("allergies"))
    
    print("\n[BiteFinder understood your request as]")
    print(f"  For: {req.get('name', 'Guest')} | cuisine: {cuisine} | dietary: {dietary} | "
          f"budget: {band} | rating: {rating_txt} | walk: {req.get('max_walk_minutes')} min | "
          f"allergies: {allergies} | time: {req.get('eat_time')}")


def _fmt_price(r):
    sym = BAND_SYMBOLS.get(r.get("price_band"), "")
    price = r.get("avg_price")
    if price is not None:
        return f"${price:.2f} ({sym})" if sym else f"${price:.2f}"
    return sym if sym else "price unavailable"


def _fmt_walk(r):
    w = r.get("walk_minutes")
    src = " (est.)" if r.get("walk_source") == "estimate" else ""
    return f"{w} min walk{src}" if w is not None else "walk time unavailable"


def _fmt_dietary(r):
    """Shows dietary with a badge indicating verification status."""
    dietary = r.get("dietary", "unknown")
    source = (r.get("dietary_source") or "").lower()
    if dietary == "unknown":
        return "unknown"
    if "inferred" in source:
        return f"{dietary} (inferred ⚠️)"
    if "verified" in source:
        return f"{dietary} (verified ✓)"
    return dietary


def print_results(results):
    matches, alternatives = results["matches"], results["alternatives"]
    if not matches and not alternatives:
        print("\nNo options found. Try relaxing budget, walking time, or another location.")
        return
    if matches:
        print(f"\n=== {len(matches)} match(es) for you ===")
        for item in matches:
            r = item["restaurant"]
            rating = r.get("rating")
            rating_txt = f"rating: {rating}" if rating is not None else "rating: unavailable"
            print(f"\n{r['name']}  (score {item['score']})")
            print(f"  {r.get('cuisine', 'unknown')} | {_fmt_price(r)} | {_fmt_walk(r)} "
                  f"| {rating_txt} | dietary: {_fmt_dietary(r)} "
                  f"| certification: {r.get('certification', 'unknown')}")
            for reason in item["reasons"]:
                print(f"  + {reason}")
    else:
        print("\nNo exact match, but here are the closest alternatives")
        print("(your dietary and allergy rules were NOT relaxed):")
    if alternatives:
        if matches:
            print("\n=== Alternatives (what would need to change) ===")
        for item in alternatives:
            r = item["restaurant"]
            print(f"\n{r['name']}  [data: {r.get('source', 'catalog')}]")
            for reason in item["reasons"]:
                print(f"  ! {reason}")


def choose_restaurant(results):
    options = results["matches"] + results["alternatives"]
    if not options:
        return None
    print("\nShow walking route: enter a number above (or Enter to skip):")
    while True:
        raw = input("> ").strip()
        if raw == "":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]["restaurant"]
        print(f"  Please enter a number 1-{len(options)} (or Enter to skip).")


def print_route(name, route, link):
    print(f"\n--- Walking route to {name} ---")
    if route is None:
        print("  Detailed route unavailable right now — open this map link instead:")
    else:
        print(f"  {route['duration_min']} min | {route['distance_m']} m")
        for i, step in enumerate(route["steps"], start=1):
            print(f"  {i}. {step}")
        print("  Visual map:")
    print(f"  {link}")


def print_error(message):
    print(f"\n[ERROR] {message}")