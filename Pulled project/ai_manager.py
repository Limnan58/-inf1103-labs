"""AI layer — parses a natural-language user request into a structured query
using Gemini (OpenAI-compatible endpoint)."""
import json
import config
from openai import OpenAI

# Gemini exposes an OpenAI-compatible API. The OpenAI SDK wants the *base* URL
# (without /chat/completions), so we strip it if present.
_BASE_URL = config.API_URL.replace("/chat/completions", "").rstrip("/")

client = OpenAI(
    api_key=config.GEMINI_API_KEY,
    base_url=_BASE_URL,
)

# The prompt reflects EXACTLY the fields logic_manager needs.
# The AI's job: normalize messy user input + map food_preference -> cuisine.
SYSTEM_PROMPT = """You are a restaurant-search parser for BiteFinder (Singapore).
You will receive a JSON object containing the user's restaurant preferences.
Your job is to NORMALIZE and ENRICH this data into a clean structured query.

Return ONLY a JSON object with these EXACT keys:
  - "cuisine": string (from the "food_preference" field; use "any" if empty)
  - "dietary": string (one of: "none", "halal", "vegetarian", "vegan"; default "none")
  - "allergies": list of strings (e.g. ["peanuts", "shellfish"]; [] if none)
  - "budget_band": string or null (one of: "inexpensive", "moderate", "expensive", "very_expensive")
  - "max_walk_minutes": integer or null
  - "min_rating": float or null
  - "eat_time": string ("now" or "HH:MM" 24-hour format)
  - "free_text": string (a short summary of the free_text notes, e.g. "spicy food")

RULES:
- If "food_preference" is empty or missing, set "cuisine" to "any".
- Preserve all existing non-empty values from the input. Only fill in what's missing.
- If "free_text" mentions spice ("spicy", "hot"), set "free_text" to include "spicy".
- Do not invent values that aren't in the input.
- No explanation. No markdown. JSON only."""


def call_ai(record):
    """
    record: the raw user-input dict from io_manager.get_user_requirements()
    returns: (ok: bool, result: dict | str)
             ok=True  -> result is the parsed requirement dict
             ok=False -> result is an error message string
    """
    # Defensive: strip the 'name' field before sending to the AI.
    # (main.py already does this, but keeping the guard for safety.)
    if isinstance(record, dict):
        ai_input = {k: v for k, v in record.items() if k != "name"}
    else:
        ai_input = record

    user_text = ai_input if isinstance(ai_input, str) else json.dumps(ai_input)

    try:
        resp = client.chat.completions.create(
            model=config.MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0,
        )
    except Exception as e:
        return False, f"AI request failed: {type(e).__name__}: {e}"

    raw = resp.choices[0].message.content.strip()

    # Models sometimes wrap JSON in ```json fences — strip them.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"AI returned non-JSON ({e}): {raw[:200]}"

    # --- SAFETY NET: ensure 'cuisine' exists even if the AI forgot it ---
    # If the AI didn't return cuisine but the original record had food_preference,
    # use it as a fallback.
    if isinstance(record, dict):
        if not parsed.get("cuisine"):
            parsed["cuisine"] = record.get("food_preference") or "any"
        if not parsed.get("eat_time"):
            parsed["eat_time"] = record.get("eat_time") or "now"
        if parsed.get("max_walk_minutes") is None:
            parsed["max_walk_minutes"] = record.get("max_walk_minutes")

    return True, parsed