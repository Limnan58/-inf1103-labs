"""
io_manager.py
=============
BiteFinder — I/O Manager

Responsibility (per system design):
- This module is the ONLY boundary between the system and the user.
- It collects structured input from the user via the terminal.
- It validates all user input, rejecting and re-prompting on bad data.
- It formats individual records and lists of records for display.
- Every print() call in the entire system lives here — no other module
  should print anything directly to the terminal.

No business logic (matching, ranking, AI calls, etc.) lives here.
Other modules should call into IOManager to get input and to display
results, but should never call print()/input() themselves.
"""

import json
import os
from datetime import datetime
from typing import Optional


# ----------------------------------------------------------------------
# Allowed value sets used for validation
# ----------------------------------------------------------------------
DIETARY_OPTIONS = ["none", "halal", "vegetarian", "vegan"]
COMMON_ALLERGENS = ["peanut", "shellfish", "dairy", "egg", "gluten", "soy", "tree nut"]

# Where collected user input is saved
USER_INPUT_JSON_PATH = "user_requests.json"


class IOManager:
    """Handles all terminal input/output for BiteFinder."""

    # ------------------------------------------------------------------
    # INPUT COLLECTION
    # ------------------------------------------------------------------

    def collect_user_input(self) -> dict:
        """
        Prompt the user for BiteFinder's inputs. Most fields are optional
        (press Enter to skip); location is required and re-prompted until
        given. Returns a structured dict ready for the AI / matching layer.
        """
        print("\n--- Your request (press Enter to skip optional fields) ---")

        walking_time = self._prompt_optional_number("Max walking time (minutes): ")
        budget = self._prompt_optional_number("Max budget ($): ")
        dietary = self._prompt_optional_dietary("Dietary (none/halal/vegetarian/vegan): ")
        allergies = self._prompt_optional_list("Allergies to avoid (comma separated): ")
        food_preference = self._prompt_optional_text("Food/cuisine preference: ")
        eat_time = self._prompt_optional_time("Eat time ('now' or HH:MM): ")
        natural_language = self._prompt_optional_text(
            "Anything else? (e.g. 'something spicy but cheap'): "
        )
        location = self._prompt_required_location()

        user_input = {
            "max_walking_time": walking_time,
            "budget": budget,
            "dietary_requirement": dietary,
            "allergies": allergies,
            "food_preference": food_preference,
            "time_requirement": eat_time,
            "natural_language_request": natural_language,
            "location": location,
        }

        self.display_summary(user_input)
        self.save_input_to_json(user_input)
        return user_input

    # ------------------------------------------------------------------
    # JSON PERSISTENCE OF COLLECTED INPUT
    # ------------------------------------------------------------------

    def save_input_to_json(self, user_input: dict, json_path: str = USER_INPUT_JSON_PATH) -> bool:
        """
        Append this collected user_input (with a timestamp) to a JSON
        file, preserving all previous entries. Handles a missing or
        corrupt file without crashing — starts a fresh list instead.
        Returns True on success, False on failure.
        """
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            **user_input,
        }

        history = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    history = loaded
                else:
                    self.show_error(f"{json_path} did not contain a JSON list. Starting fresh.")
            except (json.JSONDecodeError, OSError) as e:
                self.show_error(f"Could not read existing {json_path} ({e}). Starting fresh.")

        history.append(entry)

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            self.show_message(f"Saved your request to {json_path}.\n")
            return True
        except OSError as e:
            self.show_error(f"Could not save to {json_path}: {e}")
            return False

    def load_input_history(self, json_path: str = USER_INPUT_JSON_PATH) -> list:
        """
        Load all previously saved user requests from the JSON file.
        Returns an empty list if the file is missing or corrupt.
        """
        if not os.path.exists(json_path):
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return loaded if isinstance(loaded, list) else []
        except (json.JSONDecodeError, OSError) as e:
            self.show_error(f"Could not read {json_path}: {e}")
            return []

    def collect_prompt(self) -> dict:
        """
        Ask the user for a single free-text prompt describing what they
        want (e.g. 'cheap halal food near Bishan, no peanuts'), instead
        of going through every structured field individually. Saves the
        result to JSON just like collect_user_input().
        """
        while True:
            prompt_text = input(
                "\nWhat are you looking for? "
                "(e.g. 'cheap halal food near Bishan, no peanuts'): "
            ).strip()
            if prompt_text:
                break
            print("  ! Please enter something so BiteFinder knows what to look for.")

        user_input = {"prompt": prompt_text}
        self.save_input_to_json(user_input)
        return user_input

    # ------------------------------------------------------------------
    # FIELD-LEVEL PROMPTS (each one validates + re-prompts on bad input)
    # ------------------------------------------------------------------

    def _prompt_optional_number(self, prompt_text: str) -> Optional[float]:
        """Ask for a number; Enter skips it (returns None); invalid input re-prompts."""
        while True:
            raw = input(prompt_text).strip()
            if raw == "":
                return None
            try:
                value = float(raw)
            except ValueError:
                print("  ! Please enter a valid number, or press Enter to skip.")
                continue
            if value < 0:
                print("  ! Value cannot be negative. Please try again.")
                continue
            return value

    def _prompt_optional_dietary(self, prompt_text: str) -> str:
        """Ask for a dietary requirement; Enter defaults to 'none'."""
        options_str = "/".join(DIETARY_OPTIONS)
        while True:
            value = input(prompt_text).strip().lower()
            if value == "":
                return "none"
            if value not in DIETARY_OPTIONS:
                print(f"  ! Please choose one of: {options_str}, or press Enter for 'none'.")
                continue
            return value

    def _prompt_optional_list(self, prompt_text: str) -> list:
        """Ask for a comma-separated list; Enter returns an empty list."""
        raw = input(prompt_text).strip()
        if raw == "":
            return []
        return [item.strip().lower() for item in raw.split(",") if item.strip()]

    def _prompt_optional_time(self, prompt_text: str) -> str:
        """Ask for 'now' or HH:MM; Enter defaults to 'now'; invalid input re-prompts."""
        while True:
            value = input(prompt_text).strip().lower()
            if value == "" or value == "now":
                return "now"
            if self._is_valid_time_format(value):
                return value
            print("  ! Please enter 'now', a time in HH:MM format (e.g. 19:30), or press Enter.")

    def _prompt_required_location(self) -> str:
        """Location is mandatory — keep re-prompting until a non-empty value is given."""
        while True:
            value = input("  Location is REQUIRED. Enter location: ").strip()
            if value:
                return value
            print("  ! Location cannot be empty. Please enter a location.")

    def _prompt_optional_text(self, prompt_text: str) -> Optional[str]:
        value = input(prompt_text).strip()
        return value if value else None

    @staticmethod
    def _is_valid_time_format(value: str) -> bool:
        parts = value.split(":")
        if len(parts) != 2:
            return False
        hours, minutes = parts
        if not (hours.isdigit() and minutes.isdigit()):
            return False
        hours, minutes = int(hours), int(minutes)
        return 0 <= hours <= 23 and 0 <= minutes <= 59

    # ------------------------------------------------------------------
    # SUMMARY VIEW
    # ------------------------------------------------------------------

    def display_summary(self, user_input: dict) -> None:
        """Print a clear summary of everything the user entered."""
        print("\n--- Your Request Summary ---")
        walking = user_input["max_walking_time"]
        print(f"  Max walking time:    {walking if walking is not None else 'No limit'} min")
        budget = user_input["budget"]
        print(f"  Max budget:          {'$' + format(budget, '.2f') if budget is not None else 'No limit'}")
        print(f"  Dietary requirement: {user_input['dietary_requirement']}")
        allergies = user_input["allergies"]
        print(f"  Allergies:           {', '.join(allergies) if allergies else 'None'}")
        print(f"  Food preference:     {user_input['food_preference'] or 'None specified'}")
        print(f"  Eat time:            {user_input['time_requirement']}")
        if user_input["natural_language_request"]:
            print(f"  Additional request:  {user_input['natural_language_request']}")
        print(f"  Location:            {user_input['location']}")
        print("-----------------------------\n")

    # ------------------------------------------------------------------
    # OUTPUT FORMATTING — single record and list of records
    # ------------------------------------------------------------------

    def format_record(self, record: dict) -> str:
        """
        Format a single restaurant recommendation record as a readable
        block of text. Expected keys (missing ones shown as 'Unavailable'):
        name, food_type, price, walking_time, opening_status,
        dietary_certification, match_reason
        """
        name = record.get("name", "Unavailable")
        food_type = record.get("food_type", "Unavailable")
        price = record.get("price")
        price_str = f"SGD {price:.2f}" if isinstance(price, (int, float)) else "Unavailable"
        walking_time = record.get("walking_time")
        walking_str = f"{walking_time} min" if walking_time is not None else "Unavailable"
        opening_status = record.get("opening_status", "Unavailable")
        certification = record.get("dietary_certification", "Unavailable")
        match_reason = record.get("match_reason", "No explanation provided.")

        lines = [
            f"{name} ({food_type})",
            f"  Price:          {price_str}",
            f"  Walking time:   {walking_str}",
            f"  Open now:       {opening_status}",
            f"  Certification:  {certification}",
            f"  Why this match: {match_reason}",
        ]
        return "\n".join(lines)

    def display_record(self, record: dict) -> None:
        """Print a single formatted record."""
        print(self.format_record(record))
        print()

    def display_recommendations(self, records: list) -> None:
        """
        Print a numbered list of recommendation records. If no records
        are given, informs the user clearly instead of showing nothing.
        """
        if not records:
            print("No matching restaurants were found for your request.\n")
            return

        print(f"=== {len(records)} Recommendation(s) Found ===\n")
        for i, record in enumerate(records, start=1):
            print(f"{i}. {self.format_record(record)}")
            print()

    def display_alternatives(self, records: list, note: str) -> None:
        """
        Print alternative suggestions when no exact match was found,
        along with a note explaining what would need to change.
        """
        print("No exact match was found. Here are the closest alternatives:\n")
        print(f"Note: {note}\n")
        self.display_recommendations(records)

    # ------------------------------------------------------------------
    # GENERIC MESSAGES (still routed through here so all print() stays
    # in this one module)
    # ------------------------------------------------------------------

    def show_message(self, message: str) -> None:
        print(message)

    def show_error(self, message: str) -> None:
        print(f"Error: {message}")


# ----------------------------------------------------------------------
# Simple manual test / demonstration when run directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    io = IOManager()

    print("Choose input mode:")
    print("  1. Full structured questions")
    print("  2. Single free-text prompt")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        user_data = io.collect_prompt()
    else:
        user_data = io.collect_user_input()

    print(f"\n(All saved requests so far: {len(io.load_input_history())})\n")

    # Example records (in the real system, these would come from the
    # matching/AI layer, never hardcoded here)
    sample_records = [
        {
            "name": "Warung Nasi Padang",
            "food_type": "Indonesian, Halal",
            "price": 6.50,
            "walking_time": 8,
            "opening_status": "Open now",
            "dietary_certification": "Halal (MUIS certified)",
            "match_reason": "Within budget, Halal certified, 8 min walk (under your limit).",
        },
        {
            "name": "Green Bowl Vegan Cafe",
            "food_type": "Vegan",
            "price": 9.00,
            "walking_time": 12,
            "opening_status": "Open now",
            "dietary_certification": "Restaurant-reported vegan menu",
            "match_reason": "Matches vegan preference, slightly over preferred walking time.",
        },
    ]

    io.display_recommendations(sample_records)
