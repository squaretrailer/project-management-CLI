"""
models/task.py
--------------
Defines the Task class with status management and serialisation.
"""

from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Valid states a task can be in."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task:
    """
    Represents a single unit of work within a project.

    Attributes:
        id          – Unique integer identifier (auto-assigned).
        title       – Short description of the work.
        status      – Current state: todo | in_progress | done.
        assigned_to – Name/email of the person responsible (optional).
        project_id  – The project this task belongs to.
        created_at  – ISO-8601 creation timestamp.
        updated_at  – ISO-8601 last-update timestamp.
    """

    _next_id: int = 1

    def __init__(
        self,
        title: str,
        project_id: int,
        assigned_to: str = "",
        status: str = TaskStatus.TODO,
        task_id: int | None = None,
    ):
        self.title = title
        self.project_id = project_id
        self.assigned_to = assigned_to
        self.status = status

        if task_id is not None:
            self._id = task_id
            if task_id >= Task._next_id:
                Task._next_id = task_id + 1
        else:
            self._id = Task._next_id
            Task._next_id += 1

        now = datetime.now().isoformat(timespec="seconds")
        self.created_at: str = now
        self.updated_at: str = now

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
            raise ValueError("Task title cannot be empty.")
        self._title = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        """Validate status against allowed TaskStatus values."""
        valid = {s.value for s in TaskStatus}
        if value not in valid:
            raise ValueError(
                f"Invalid status '{value}'. Must be one of: {', '.join(valid)}"
            )
        self._status = value
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    def complete(self) -> None:
        """Mark this task as done."""
        self.status = TaskStatus.DONE

    def start(self) -> None:
        """Mark this task as in-progress."""
        self.status = TaskStatus.IN_PROGRESS

    def reset(self) -> None:
        """Reset this task back to todo."""
        self.status = TaskStatus.TODO

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "title": self._title,
            "status": self._status,
            "assigned_to": self.assigned_to,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        task = cls(
            title=data["title"],
            project_id=data["project_id"],
            assigned_to=data.get("assigned_to", ""),
            status=data.get("status", TaskStatus.TODO),
            task_id=data["id"],
        )
        task.created_at = data.get("created_at", task.created_at)
        task.updated_at = data.get("updated_at", task.updated_at)
        return task

    def __repr__(self) -> str:
        return (
            f"Task(id={self._id}, title={self._title!r}, "
            f"status={self._status!r}, assigned_to={self.assigned_to!r})"
        )

    def __str__(self) -> str:
        assignee = f" → {self.assigned_to}" if self.assigned_to else ""
        return f"[{self._id}] {self._title} [{self._status.upper()}]{assignee}"