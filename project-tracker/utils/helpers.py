"""
utils/helpers.py
----------------
Shared helper functions used across the CLI and tracker.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Return True if email loosely matches a valid email format."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip().lower()))


def validate_date(date_str: str) -> bool:
    """Return True if date_str is a valid YYYY-MM-DD string (or empty)."""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def find_user_by_name(users: list, name: str):
    """Case-insensitive user lookup by name. Returns User or None."""
    name_lower = name.strip().lower()
    for user in users:
        if user.name.lower() == name_lower:
            return user
    return None


def find_user_by_id(users: list, user_id: int):
    """Find a user by integer ID. Returns User or None."""
    for user in users:
        if user.id == user_id:
            return user
    return None


def find_project_by_title(projects: list, title: str):
    """Case-insensitive project lookup by title. Returns Project or None."""
    title_lower = title.strip().lower()
    for project in projects:
        if project.title.lower() == title_lower:
            return project
    return None


def find_project_by_id(projects: list, project_id: int):
    """Find a project by integer ID. Returns Project or None."""
    for project in projects:
        if project.id == project_id:
            return project
    return None


def find_task_by_title(tasks: list, title: str, project_id: int | None = None):
    """Case-insensitive task lookup by title, optionally scoped to a project."""
    title_lower = title.strip().lower()
    for task in tasks:
        if task.title.lower() == title_lower:
            if project_id is None or task.project_id == project_id:
                return task
    return None


def find_task_by_id(tasks: list, task_id: int):
    """Find a task by integer ID. Returns Task or None."""
    for task in tasks:
        if task.id == task_id:
            return task
    return None


def tasks_for_project(tasks: list, project_id: int) -> list:
    """Return all tasks belonging to a specific project."""
    return [t for t in tasks if t.project_id == project_id]


def projects_for_user(projects: list, user_id: int) -> list:
    """Return all projects owned by a specific user."""
    return [p for p in projects if p.owner_id == user_id]