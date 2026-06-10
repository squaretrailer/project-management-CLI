"""
utils/storage.py
----------------
Handles all JSON-based persistence: reading and writing users, projects, tasks.
Provides robust error handling for missing or malformed files.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
TASKS_FILE = DATA_DIR / "tasks.json"


def _ensure_data_dir() -> None:
    """Create the data directory if it does not already exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(filepath: Path) -> list[dict]:
    """
    Safely read a JSON array from filepath.
    Returns an empty list if the file is missing or contains invalid JSON.
    """
    if not filepath.exists():
        logger.debug("File not found, returning empty list: %s", filepath)
        return []
    try:
        with filepath.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, list):
                logger.warning("Expected JSON array in %s; got %s", filepath, type(data))
                return []
            return data
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON in %s: %s", filepath, exc)
        return []


def _write_json(filepath: Path, data: list[dict]) -> None:
    """
    Atomically write data as pretty-printed JSON to filepath.
    Uses a temp file + os.replace to prevent corruption on failure.
    """
    _ensure_data_dir()
    tmp_path = filepath.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
        logger.debug("Saved %d records to %s", len(data), filepath)
    except OSError as exc:
        logger.error("Failed to write %s: %s", filepath, exc)
        raise


def load_users() -> list[dict]:
    """Load all raw user dictionaries from disk."""
    return _read_json(USERS_FILE)


def save_users(users: list) -> None:
    """Persist a list of User objects to disk."""
    _write_json(USERS_FILE, [u.to_dict() if hasattr(u, "to_dict") else u for u in users])


def load_projects() -> list[dict]:
    """Load all raw project dictionaries from disk."""
    return _read_json(PROJECTS_FILE)


def save_projects(projects: list) -> None:
    """Persist a list of Project objects to disk."""
    _write_json(PROJECTS_FILE, [p.to_dict() if hasattr(p, "to_dict") else p for p in projects])


def load_tasks() -> list[dict]:
    """Load all raw task dictionaries from disk."""
    return _read_json(TASKS_FILE)


def save_tasks(tasks: list) -> None:
    """Persist a list of Task objects to disk."""
    _write_json(TASKS_FILE, [t.to_dict() if hasattr(t, "to_dict") else t for t in tasks])