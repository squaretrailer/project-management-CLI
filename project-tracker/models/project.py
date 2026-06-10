"""
models/project.py
-----------------
Defines the Project class with date validation and one-to-many task relationship.
"""

from datetime import datetime


class Project:
    """
    Represents a project owned by a User and containing one or more Tasks.

    Attributes:
        id          – Unique integer identifier (auto-assigned).
        title       – Project name.
        description – Optional longer description.
        due_date    – Optional deadline (YYYY-MM-DD string).
        owner_id    – ID of the User who owns this project.
        task_ids    – List of Task IDs belonging to this project.
        created_at  – ISO-8601 creation timestamp.
    """

    _next_id: int = 1

    def __init__(
        self,
        title: str,
        owner_id: int,
        description: str = "",
        due_date: str = "",
        project_id: int | None = None,
    ):
        self.title = title
        self.owner_id = owner_id
        self.description = description
        self.due_date = due_date

        if project_id is not None:
            self._id = project_id
            if project_id >= Project._next_id:
                Project._next_id = project_id + 1
        else:
            self._id = Project._next_id
            Project._next_id += 1

        self._task_ids: list[int] = []
        self.created_at: str = datetime.now().isoformat(timespec="seconds")

    @property
    def id(self) -> int:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Project title cannot be empty.")
        self._title = value

    @property
    def due_date(self) -> str:
        return self._due_date

    @due_date.setter
    def due_date(self, value: str):
        """Accepts empty string (no deadline) or YYYY-MM-DD."""
        value = value.strip()
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid due_date '{value}'. Expected format: YYYY-MM-DD")
        self._due_date = value

    @property
    def task_ids(self) -> list[int]:
        return list(self._task_ids)

    @property
    def is_overdue(self) -> bool:
        if not self._due_date:
            return False
        deadline = datetime.strptime(self._due_date, "%Y-%m-%d")
        return deadline < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def add_task(self, task_id: int) -> None:
        """Associate a task ID with this project."""
        if task_id not in self._task_ids:
            self._task_ids.append(task_id)

    def remove_task(self, task_id: int) -> None:
        """Disassociate a task ID from this project."""
        self._task_ids = [t for t in self._task_ids if t != task_id]

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "title": self._title,
            "description": self.description,
            "due_date": self._due_date,
            "owner_id": self.owner_id,
            "task_ids": self._task_ids,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        project = cls(
            title=data["title"],
            owner_id=data["owner_id"],
            description=data.get("description", ""),
            due_date=data.get("due_date", ""),
            project_id=data["id"],
        )
        project._task_ids = data.get("task_ids", [])
        project.created_at = data.get("created_at", project.created_at)
        return project

    def __repr__(self) -> str:
        return (
            f"Project(id={self._id}, title={self._title!r}, "
            f"owner_id={self.owner_id}, tasks={self._task_ids})"
        )

    def __str__(self) -> str:
        deadline = f" | Due: {self._due_date}" if self._due_date else ""
        overdue = " ⚠ OVERDUE" if self.is_overdue else ""
        return f"[{self._id}] {self._title}{deadline}{overdue}"