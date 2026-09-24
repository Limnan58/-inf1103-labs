"""
logic_manager.py
=================
BiteFinder — Logic Manager

Responsibility (per system design):
- This is the domain brain. It acts on AI output, not raw data.
- Applies business rules to the AI-enriched record.
- Decides an outcome: flag, score, route, accept, or reject.
- Contains at least one multi-condition rule using AI output fields.
- This is where BiteFinder's actual domain idea lives — everything else
  (I/O, AI calls, storage) is plumbing around this decision logic.

Business rules implemented here (from the project's business-rules doc):
- Dietary needs, allergies, budget, and walking time are NON-NEGOTIABLE.
  A record failing any of these is rejected outright, regardless of how
  well it matches other preferences.
- If the AI itself failed (ai_status == "failed"), the record cannot be
  trusted either way — it is flagged for manual review, never silently
  accepted or rejected.
- Even when all hard constraints pass, low AI confidence results in a
  "flag" outcome (uncertain match) rather than an outright accept.
- Records that pass all hard constraints with high confidence are scored
  and accepted, ready to be ranked and shown to the user.
"""

CONFIDENCE_THRESHOLD = 0.7


class LogicManager:
    """Applies BiteFinder's business rules to AI-enriched restaurant records."""

    def evaluate(self, enriched_record: dict, user_requirements: dict) -> dict:
        """
        Apply business rules to a single AI-enriched record and return
        a decision dict: {"decision": ..., "score": ..., "reason": ...}
        decision is one of: "accept", "reject", "flag"
        """
        record = dict(enriched_record)

        # --- Rule 0: AI failure means we cannot trust the data either way ---
        if record.get("ai_status") != "ok":
            return self._make_decision(
                "flag",
                score=0.0,
                reason="AI evaluation failed or was unavailable — needs manual review.",
            )

        # --- Rule 1 (non-negotiable, checked first): hard constraints ---
        # Per the business rules doc: dietary, allergy, budget and walking
        # time are all non-negotiable and must be validated before any
        # ranking or preference-based logic runs.
        hard_constraints = {
            "matches_dietary": record.get("matches_dietary", False),
            "matches_allergy_safe": record.get("matches_allergy_safe", False),
            "matches_budget": record.get("matches_budget", False),
            "matches_walking_time": record.get("matches_walking_time", False),
        }
        failed_constraints = [name for name, passed in hard_constraints.items() if not passed]

        if failed_constraints:
            return self._make_decision(
                "reject",
                score=0.0,
                reason=f"Failed non-negotiable requirement(s): {', '.join(failed_constraints)}.",
            )

        # --- Rule 2 (multi-condition rule using AI output fields) ---
        # All four hard constraints passed AND the AI's confidence in that
        # assessment must also be high enough before we accept outright.
        confidence = record.get("confidence", 0.0)
        all_hard_constraints_pass = not failed_constraints

        if all_hard_constraints_pass and confidence >= CONFIDENCE_THRESHOLD:
            score = self._calculate_score(record, user_requirements)
            return self._make_decision(
                "accept",
                score=score,
                reason=f"Meets all requirements with high confidence ({confidence:.2f}). {record.get('explanation', '')}",
            )

        if all_hard_constraints_pass and confidence < CONFIDENCE_THRESHOLD:
            return self._make_decision(
                "flag",
                score=confidence,
                reason=f"Meets requirements but AI confidence is low ({confidence:.2f}) — recommend manual check. {record.get('explanation', '')}",
            )

        # Fallback safety net — should not normally be reached given the
        # branches above, but ensures we never fall through silently.
        return self._make_decision(
            "reject",
            score=0.0,
            reason="Did not meet acceptance criteria.",
        )

    def evaluate_batch(self, enriched_records: list, user_requirements: dict) -> list:
        """Apply evaluate() to a list of enriched records, in order."""
        return [self.evaluate(r, user_requirements) | {"record": r} for r in enriched_records]

    # ------------------------------------------------------------------
    # SCORING (used only for accepted records, to support ranking)
    # ------------------------------------------------------------------

    def _calculate_score(self, record: dict, user_requirements: dict) -> float:
        """
        Combine AI confidence with soft preference matches (cuisine
        preference, walking time headroom) into a single ranking score
        between 0 and 1. Only meaningful for accepted records.
        """
        score = record.get("confidence", 0.0) * 0.6  # base weight: AI confidence

        # Bonus: cuisine/food preference match (a soft preference, not a
        # hard constraint, per the business rules doc)
        preferred = (user_requirements.get("food_preference") or "").strip().lower()
        cuisine = (record.get("cuisine") or "").strip().lower()
        if preferred and preferred in cuisine:
            score += 0.2

        # Bonus: shorter walking time relative to the user's max is preferred
        max_walk = user_requirements.get("max_walking_time")
        actual_walk = record.get("walking_time")
        if isinstance(max_walk, (int, float)) and isinstance(actual_walk, (int, float)) and max_walk > 0:
            headroom = max(0.0, (max_walk - actual_walk) / max_walk)
            score += headroom * 0.2

        return round(min(1.0, score), 3)

    def _make_decision(self, decision: str, score: float, reason: str) -> dict:
        return {"decision": decision, "score": score, "reason": reason}
