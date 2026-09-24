"""
ai_manager.py
=============
BiteFinder — AI Manager

Responsibility (per system design):
- This is the core engine. EVERY record passes through here, no exceptions.
- Builds a prompt from an input record.
- Calls the AI API and parses the response.
- Validates the response schema — rejects or retries on malformed output.
- Handles API failure gracefully — logs and continues, never crashes.
- ZERO domain logic lives here. This module does not decide whether a
  restaurant is "good enough" — that is LogicManager's job. AIManager
  only talks to the API and hands back a validated, structured result.
"""

import os
import json
import logging
import requests
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    filename="bitefinder.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("AIManager")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "z-ai/glm-5.2:free"
MAX_RETRIES = 2

# The exact schema every AI response must follow. AIManager rejects
# and retries any response that doesn't match this shape.
REQUIRED_FIELDS = {
    "matches_dietary": bool,
    "matches_allergy_safe": bool,
    "matches_budget": bool,
    "matches_walking_time": bool,
    "confidence": (int, float),
    "explanation": str,
}

SYSTEM_PROMPT = """You are an evaluation engine for a food-recommendation system called BiteFinder.
You will be given a restaurant candidate and a user's requirements.
Evaluate ONLY whether the candidate satisfies the requirements — do not invent
facts not given to you. If information is missing, be conservative (assume it
does NOT satisfy that requirement) and say so in the explanation.

Respond ONLY with a single JSON object with EXACTLY these fields, no others:
{
  "matches_dietary": true or false,
  "matches_allergy_safe": true or false,
  "matches_budget": true or false,
  "matches_walking_time": true or false,
  "confidence": a number between 0 and 1,
  "explanation": "a short one or two sentence explanation"
}
Do not include markdown code fences. Do not include any text outside the JSON object."""


class AIManager:
    """Handles all API interaction for evaluating a restaurant record."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------

    def process_record(self, restaurant: dict, user_requirements: dict) -> dict:
        """
        Run a single restaurant record through the AI pipeline:
        build prompt -> call API -> validate/retry -> return enriched record.

        Never raises. On failure, returns the original record with
        ai_status="failed" so the pipeline can continue without crashing.
        """
        enriched = dict(restaurant)  # never mutate the caller's original

        if not self.api_key:
            logger.error("No API key configured. Skipping AI evaluation.")
            enriched["ai_status"] = "failed"
            enriched["ai_error"] = "No API key configured."
            return enriched

        prompt = self.build_prompt(restaurant, user_requirements)

        for attempt in range(1, MAX_RETRIES + 2):  # initial try + retries
            raw_response = self.call_api(prompt)

            if raw_response is None:
                # API-level failure (network, timeout, non-200 status).
                # Already logged inside call_api. Try again if attempts remain.
                continue

            parsed = self.parse_response(raw_response)
            if parsed is not None:
                enriched.update(parsed)
                enriched["ai_status"] = "ok"
                return enriched

            logger.warning(
                f"Malformed AI response on attempt {attempt} for '{restaurant.get('name', 'unknown')}'. Retrying."
            )

        # Every attempt failed — log and return a safe fallback, never crash.
        logger.error(
            f"AI evaluation failed after {MAX_RETRIES + 1} attempts for '{restaurant.get('name', 'unknown')}'."
        )
        enriched["ai_status"] = "failed"
        enriched["ai_error"] = "AI did not return a valid response after retries."
        return enriched

    # ------------------------------------------------------------------
    # PROMPT BUILDING
    # ------------------------------------------------------------------

    def build_prompt(self, restaurant: dict, user_requirements: dict) -> str:
        """Build a plain-text prompt describing the candidate and requirements."""
        return (
            "RESTAURANT CANDIDATE:\n"
            f"- Name: {restaurant.get('name', 'Unknown')}\n"
            f"- Cuisine: {restaurant.get('cuisine', 'Unknown')}\n"
            f"- Price: {restaurant.get('price', 'Unknown')}\n"
            f"- Walking time: {restaurant.get('walking_time', 'Unknown')} minutes\n"
            f"- Dietary certification: {restaurant.get('dietary_certification', 'Unknown')}\n"
            f"- Known allergens present: {restaurant.get('allergens', 'Unknown')}\n\n"
            "USER REQUIREMENTS:\n"
            f"- Dietary requirement: {user_requirements.get('dietary_requirement', 'none')}\n"
            f"- Allergies to avoid: {user_requirements.get('allergies', [])}\n"
            f"- Budget (max SGD): {user_requirements.get('budget', 'Unknown')}\n"
            f"- Max walking time (min): {user_requirements.get('max_walking_time', 'Unknown')}\n"
        )

    # ------------------------------------------------------------------
    # API CALL
    # ------------------------------------------------------------------

    def call_api(self, prompt: str) -> Optional[str]:
        """
        Call the AI API and return the raw text content, or None on any
        failure. Never raises — all exceptions are caught and logged.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            logger.error(f"Network error calling AI API: {e}")
            return None

        if response.status_code != 200:
            logger.error(f"AI API returned status {response.status_code}: {response.text}")
            return None

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Unexpected AI API response shape: {e}")
            return None

    # ------------------------------------------------------------------
    # RESPONSE VALIDATION
    # ------------------------------------------------------------------

    def parse_response(self, raw_response: str) -> Optional[dict]:
        """
        Parse and validate the AI's raw text response against the required
        schema. Returns the parsed dict if valid, or None if malformed
        (missing fields, wrong types, or invalid JSON).
        """
        content = raw_response.strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in parsed:
                return None
            if not isinstance(parsed[field], expected_type):
                return None

        # Clamp confidence into a valid 0-1 range defensively
        parsed["confidence"] = max(0.0, min(1.0, float(parsed["confidence"])))

        return parsed