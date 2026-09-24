"""
data_manager.py
================
BiteFinder — Data Manager

Responsibility (per system design):
- This is the system's memory across runs.
- Saves processed records to CSV or JSON.
- Loads all records on startup.
- Provides at least one filter/query function.
- Handles missing or corrupt files without crashing.
"""

import os
import json
import csv
import logging

logging.basicConfig(
    filename="bitefinder.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("DataManager")


class DataManager:
    """Handles saving and loading processed BiteFinder records."""

    def __init__(self, json_path: str = "bitefinder_records.json", csv_path: str = "bitefinder_records.csv"):
        self.json_path = json_path
        self.csv_path = csv_path

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------

    def save_json(self, records: list) -> bool:
        """Save records to a JSON file. Returns True on success, False on failure."""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            logger.error(f"Failed to save JSON to {self.json_path}: {e}")
            return False

    def save_csv(self, records: list) -> bool:
        """
        Save records to a CSV file. Handles records with differing keys
        by taking the union of all fields across all records.
        Returns True on success, False on failure.
        """
        if not records:
            logger.warning("No records to save to CSV.")
            return False

        try:
            fieldnames = sorted({key for record in records for key in record.keys()})
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in records:
                    writer.writerow(record)
            return True
        except OSError as e:
            logger.error(f"Failed to save CSV to {self.csv_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------

    def load_json(self) -> list:
        """
        Load all records from the JSON file. Returns an empty list if
        the file is missing, empty, or corrupt — never raises.
        """
        if not os.path.exists(self.json_path):
            logger.info(f"{self.json_path} not found. Starting with an empty record set.")
            return []

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                logger.error(f"{self.json_path} did not contain a JSON list. Ignoring file.")
                return []
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Corrupt or unreadable JSON file {self.json_path}: {e}")
            return []

    def load_csv(self) -> list:
        """
        Load all records from the CSV file. Returns an empty list if
        the file is missing or corrupt — never raises.
        """
        if not os.path.exists(self.csv_path):
            logger.info(f"{self.csv_path} not found. Starting with an empty record set.")
            return []

        try:
            with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except (csv.Error, OSError) as e:
            logger.error(f"Corrupt or unreadable CSV file {self.csv_path}: {e}")
            return []

    # ------------------------------------------------------------------
    # FILTER / QUERY
    # ------------------------------------------------------------------

    def filter_by_decision(self, records: list, decision: str) -> list:
        """Return only records matching the given decision (accept/reject/flag)."""
        return [r for r in records if r.get("decision") == decision]

    def filter_by_min_score(self, records: list, min_score: float) -> list:
        """Return only records with a score >= min_score."""
        result = []
        for r in records:
            try:
                score = float(r.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            if score >= min_score:
                result.append(r)
        return result

    def query_by_cuisine(self, records: list, cuisine: str) -> list:
        """Return only records whose cuisine field contains the given text (case-insensitive)."""
        cuisine_lower = cuisine.strip().lower()
        return [
            r for r in records
            if cuisine_lower in str(r.get("cuisine", "")).lower()
        ]
