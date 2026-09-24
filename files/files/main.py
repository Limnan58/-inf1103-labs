

from io_manager import IOManager
from ai_manager import AIManager
from logic_manager import LogicManager
from data_manager import DataManager
from data_fetcher import fetch_candidates_for_request


def main():
    io = IOManager()
    ai = AIManager()
    logic = LogicManager()
    data = DataManager()

    # --- Load history on startup (Data Manager) ---
    history = data.load_json()
    io.show_message(f"Loaded {len(history)} record(s) from previous runs.\n")

    # --- Collect and validate user requirements (I/O Manager) ---
    user_requirements = io.collect_user_input()

    # --- Fetch real nearby restaurant candidates (Data Fetcher) ---
    io.show_message(f"Searching for restaurants near '{user_requirements['location']}'...")
    candidates = fetch_candidates_for_request(
        location=user_requirements["location"],
        max_walking_time=user_requirements.get("max_walking_time"),
    )

    if not candidates:
        io.show_error(
            "Could not find any restaurants for that location. "
            "Try a more specific or well-known place name."
        )
        return

    io.show_message(f"Found {len(candidates)} nearby restaurant(s) to evaluate.\n")

    # --- Run every candidate through the AI Manager, no exceptions ---
    results = []
    for candidate in candidates:
        enriched = ai.process_record(candidate, user_requirements)
        decision = logic.evaluate(enriched, user_requirements)

        combined_record = {**enriched, **decision}
        results.append(combined_record)

    # --- Persist this run's results (Data Manager) ---
    all_records = history + results
    data.save_json(all_records)
    data.save_csv(all_records)

    # --- Display outcomes (I/O Manager) ---
    accepted = data.filter_by_decision(results, "accept")
    flagged = data.filter_by_decision(results, "flag")
    rejected = data.filter_by_decision(results, "reject")

    io.show_message(f"\nResults: {len(accepted)} accepted, {len(flagged)} flagged, {len(rejected)} rejected.\n")

    if accepted:
        accepted_sorted = sorted(accepted, key=lambda r: r.get("score", 0), reverse=True)
        display_records = [
            {
                "name": r.get("name"),
                "food_type": r.get("cuisine"),
                "price": r.get("price"),
                "walking_time": r.get("walking_time"),
                "opening_status": "Unavailable",  # not modeled in this sample data
                "dietary_certification": r.get("dietary_certification"),
                "match_reason": r.get("reason"),
            }
            for r in accepted_sorted
        ]
        io.display_recommendations(display_records)
    else:
        io.show_message("No restaurants were accepted outright. Here is what was flagged instead:\n")
        for r in flagged:
            io.show_message(f"  - {r.get('name')}: {r.get('reason')}")


if __name__ == "__main__":
    main()
