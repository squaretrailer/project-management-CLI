"""
models/user.py
--------------
Defines the Person base class and User subclass.
Demonstrates inheritance, @property, class attributes, and __repr__.
"""

import re
from datetime import datetime


class Person:
    """
    Base class representing a generic person.
    Provides shared attributes (name, email) and validation logic.
    """

    def __init__(self, name: str, email: str):
        """Initialise a Person with a name and email."""
        self.name = name        # uses @property setter for validation
        self.email = email      # uses @property setter for validation

    @property
    def name(self) -> str:
        """Return the person's display name."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Validate and set name (non-empty string)."""
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def email(self) -> str:
        """Return the person's email address."""
        return self._email

    @email.setter
    def email(self, value: str):
        """Validate and set email (basic regex check)."""
        value = value.strip().lower()
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(pattern, value):
            raise ValueError(f"Invalid email address: '{value}'")
        self._email = value

    def __repr__(self) -> str:
        return f"Person(name={self._name!r}, email={self._email!r})"


class User(Person):
    """
    Represents a system user who owns one or more projects.

    Inherits from Person and adds:
      - A unique integer ID (class-level counter).
      - A list of project IDs (one-to-many relationship).
      - A creation timestamp.
    """

    # Class-level ID counter – incremented each time a User is created
    _next_id: int = 1

    def __init__(self, name: str, email: str, user_id: int | None = None):
        """
        Initialise a User.

        Args:
            name:    Display name.
            email:   Valid email address.
            user_id: Override auto-assigned ID (used when loading from disk).
        """
        super().__init__(name, email)

        if user_id is not None:
            self._id = user_id
            if user_id >= User._next_id:
                User._next_id = user_id + 1
        else:
            self._id = User._next_id
            User._next_id += 1

        self._project_ids: list[int] = []
        self.created_at: str = datetime.now().isoformat(timespec="seconds")

    @property
    def id(self) -> int:
        """Return the user's unique ID."""
        return self._id

    @property
    def project_ids(self) -> list[int]:
        """Return a copy of the user's project-ID list."""
        return list(self._project_ids)

    def add_project(self, project_id: int) -> None:
        """Associate a project ID with this user."""
        if project_id not in self._project_ids:
            self._project_ids.append(project_id)

    def remove_project(self, project_id: int) -> None:
        """Disassociate a project ID from this user."""
        self._project_ids = [p for p in self._project_ids if p != project_id]

    def to_dict(self) -> dict:
        """Serialise the user to a JSON-compatible dictionary."""
        return {
            "id": self._id,
            "name": self._name,
            "email": self._email,
            "project_ids": self._project_ids,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Deserialise a User from a dictionary (e.g. loaded from JSON)."""
        user = cls(
            name=data["name"],
            email=data["email"],
            user_id=data["id"],
        )
        user._project_ids = data.get("project_ids", [])
        user.created_at = data.get("created_at", datetime.now().isoformat(timespec="seconds"))
        return user

    def __repr__(self) -> str:
        return (
            f"User(id={self._id}, name={self._name!r}, "
            f"email={self._email!r}, projects={self._project_ids})"
        )

    def __str__(self) -> str:
        return f"[{self._id}] {self._name} <{self._email}>"