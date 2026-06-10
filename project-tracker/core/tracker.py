"""
core/tracker.py
---------------
The Tracker class is the single source of truth for the application state.
It loads/saves data and exposes high-level CRUD operations used by the CLI.
"""

import logging
from models import User, Project, Task, TaskStatus
from utils.storage import (
    load_users, save_users,
    load_projects, save_projects,
    load_tasks, save_tasks,
)
from utils.helpers import (
    find_user_by_name, find_user_by_id,
    find_project_by_title, find_project_by_id,
    find_task_by_title, find_task_by_id,
    tasks_for_project, projects_for_user,
)

logger = logging.getLogger(__name__)


class Tracker:
    """
    Central application state manager.
    Owns the in-memory lists of Users, Projects, and Tasks.
    All CLI commands delegate here for business logic and persistence.
    """

    def __init__(self):
        """Load persisted data from disk on startup."""
        self._users: list[User] = []
        self._projects: list[Project] = []
        self._tasks: list[Task] = []
        self._load_all()

    def _load_all(self) -> None:
        """Deserialise all entities from JSON files."""
        self._users = [User.from_dict(d) for d in load_users()]
        self._projects = [Project.from_dict(d) for d in load_projects()]
        self._tasks = [Task.from_dict(d) for d in load_tasks()]

    def _save_all(self) -> None:
        """Persist all in-memory entities to JSON files."""
        save_users(self._users)
        save_projects(self._projects)
        save_tasks(self._tasks)

    # --- Read-only accessors ---

    @property
    def users(self) -> list[User]:
        return list(self._users)

    @property
    def projects(self) -> list[Project]:
        return list(self._projects)

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks)

    # --- User operations ---

    def add_user(self, name: str, email: str) -> User:
        """Create and persist a new User. Raises ValueError on duplicate email."""
        email_lower = email.strip().lower()
        if any(u.email == email_lower for u in self._users):
            raise ValueError(f"A user with email '{email_lower}' already exists.")
        user = User(name=name, email=email_lower)
        self._users.append(user)
        self._save_all()
        return user

    def list_users(self) -> list[User]:
        return list(self._users)

    def get_user(self, identifier: str) -> User | None:
        """Look up by name or numeric ID string."""
        if identifier.isdigit():
            return find_user_by_id(self._users, int(identifier))
        return find_user_by_name(self._users, identifier)

    def delete_user(self, identifier: str) -> User:
        """Delete user and cascade-delete all their projects/tasks."""
        user = self.get_user(identifier)
        if not user:
            raise ValueError(f"User '{identifier}' not found.")
        for pid in list(user.project_ids):
            try:
                self._delete_project_by_id(pid)
            except ValueError:
                pass
        self._users = [u for u in self._users if u.id != user.id]
        self._save_all()
        return user

    def update_user(self, identifier: str, name: str | None = None, email: str | None = None) -> User:
        """Update a user's name and/or email."""
        user = self.get_user(identifier)
        if not user:
            raise ValueError(f"User '{identifier}' not found.")
        if name:
            user.name = name
        if email:
            email_lower = email.strip().lower()
            if any(u.email == email_lower and u.id != user.id for u in self._users):
                raise ValueError(f"Email '{email_lower}' is already in use.")
            user.email = email_lower
        self._save_all()
        return user

    # --- Project operations ---

    def add_project(self, title: str, user_identifier: str,
                    description: str = "", due_date: str = "") -> Project:
        """Create a Project and link it to a User."""
        owner = self.get_user(user_identifier)
        if not owner:
            raise ValueError(f"User '{user_identifier}' not found.")
        user_projects = projects_for_user(self._projects, owner.id)
        if find_project_by_title(user_projects, title):
            raise ValueError(f"User '{owner.name}' already has a project titled '{title}'.")
        project = Project(title=title, owner_id=owner.id,
                          description=description, due_date=due_date)
        self._projects.append(project)
        owner.add_project(project.id)
        self._save_all()
        return project

    def list_projects(self, user_identifier: str | None = None) -> list[Project]:
        """Return all projects, or those owned by a specific user."""
        if user_identifier is None:
            return list(self._projects)
        owner = self.get_user(user_identifier)
        if not owner:
            raise ValueError(f"User '{user_identifier}' not found.")
        return projects_for_user(self._projects, owner.id)

    def get_project(self, identifier: str) -> Project | None:
        """Look up by title or numeric ID string."""
        if identifier.isdigit():
            return find_project_by_id(self._projects, int(identifier))
        return find_project_by_title(self._projects, identifier)

    def update_project(self, identifier: str, title: str | None = None,
                       description: str | None = None, due_date: str | None = None) -> Project:
        """Update project fields."""
        project = self.get_project(identifier)
        if not project:
            raise ValueError(f"Project '{identifier}' not found.")
        if title:
            project.title = title
        if description is not None:
            project.description = description
        if due_date is not None:
            project.due_date = due_date
        self._save_all()
        return project

    def delete_project(self, identifier: str) -> Project:
        """Delete a project and its tasks."""
        project = self.get_project(identifier)
        if not project:
            raise ValueError(f"Project '{identifier}' not found.")
        return self._delete_project_by_id(project.id)

    def _delete_project_by_id(self, project_id: int) -> Project:
        """Internal: delete by ID, cascade tasks, unlink from owner."""
        project = find_project_by_id(self._projects, project_id)
        if not project:
            raise ValueError(f"Project ID {project_id} not found.")
        self._tasks = [t for t in self._tasks if t.project_id != project_id]
        owner = find_user_by_id(self._users, project.owner_id)
        if owner:
            owner.remove_project(project_id)
        self._projects = [p for p in self._projects if p.id != project_id]
        self._save_all()
        return project

    def search_projects(self, query: str) -> list[Project]:
        """Case-insensitive search over title and description."""
        q = query.strip().lower()
        return [p for p in self._projects
                if q in p.title.lower() or q in p.description.lower()]

    # --- Task operations ---

    def add_task(self, title: str, project_identifier: str,
                 assigned_to: str = "", status: str = TaskStatus.TODO) -> Task:
        """Create a Task and link it to a Project."""
        project = self.get_project(project_identifier)
        if not project:
            raise ValueError(f"Project '{project_identifier}' not found.")
        task = Task(title=title, project_id=project.id,
                    assigned_to=assigned_to, status=status)
        self._tasks.append(task)
        project.add_task(task.id)
        self._save_all()
        return task

    def list_tasks(self, project_identifier: str | None = None) -> list[Task]:
        """Return all tasks, or those belonging to a specific project."""
        if project_identifier is None:
            return list(self._tasks)
        project = self.get_project(project_identifier)
        if not project:
            raise ValueError(f"Project '{project_identifier}' not found.")
        return tasks_for_project(self._tasks, project.id)

    def get_task(self, identifier: str, project_identifier: str | None = None) -> Task | None:
        """Look up by title or numeric ID string, optionally scoped to a project."""
        project_id = None
        if project_identifier:
            project = self.get_project(project_identifier)
            if project:
                project_id = project.id
        if identifier.isdigit():
            return find_task_by_id(self._tasks, int(identifier))
        return find_task_by_title(self._tasks, identifier, project_id)

    def complete_task(self, identifier: str, project_identifier: str | None = None) -> Task:
        """Mark a task as done."""
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        task.complete()
        self._save_all()
        return task

    def start_task(self, identifier: str, project_identifier: str | None = None) -> Task:
        """Mark a task as in_progress."""
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        task.start()
        self._save_all()
        return task

    def update_task(self, identifier: str, title: str | None = None,
                    assigned_to: str | None = None, status: str | None = None,
                    project_identifier: str | None = None) -> Task:
        """Update task fields."""
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        if title:
            task.title = title
        if assigned_to is not None:
            task.assigned_to = assigned_to
        if status:
            task.status = status
        self._save_all()
        return task

    def delete_task(self, identifier: str, project_identifier: str | None = None) -> Task:
        """Delete a task and unlink it from its project."""
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        project = find_project_by_id(self._projects, task.project_id)
        if project:
            project.remove_task(task.id)
        self._tasks = [t for t in self._tasks if t.id != task.id]
        self._save_all()
        return task

    def get_project_with_owner(self, identifier: str):
        """Return (Project, User) tuple, or (None, None) if not found."""
        project = self.get_project(identifier)
        if not project:
            return None, None
        owner = find_user_by_id(self._users, project.owner_id)
        return project, owner