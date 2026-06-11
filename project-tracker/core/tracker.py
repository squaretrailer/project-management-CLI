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
    All CLI commands delegate to Tracker methods, which handle
    business logic, relationship management, and persistence.
    """

    def __init__(self):
        """Load persisted data from disk on startup."""
        self._users: list[User] = []
        self._projects: list[Project] = []
        self._tasks: list[Task] = []
        self._load_all()

    # ------------------------------------------------------------------
    # Private: load / save
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Deserialise all entities from JSON files."""
        self._users = [User.from_dict(d) for d in load_users()]
        self._projects = [Project.from_dict(d) for d in load_projects()]
        self._tasks = [Task.from_dict(d) for d in load_tasks()]
        logger.debug(
            "Loaded %d users, %d projects, %d tasks",
            len(self._users), len(self._projects), len(self._tasks),
        )

    def _save_all(self) -> None:
        """Persist all in-memory entities to JSON files."""
        save_users(self._users)
        save_projects(self._projects)
        save_tasks(self._tasks)

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def users(self) -> list[User]:
        """Return a shallow copy of all users."""
        return list(self._users)

    @property
    def projects(self) -> list[Project]:
        """Return a shallow copy of all projects."""
        return list(self._projects)

    @property
    def tasks(self) -> list[Task]:
        """Return a shallow copy of all tasks."""
        return list(self._tasks)

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def add_user(self, name: str, email: str) -> User:
        """
        Create and persist a new User.

        Args:
            name:  Display name (non-empty).
            email: Valid email address (must be unique).

        Returns:
            The newly created User.

        Raises:
            ValueError: If email is already registered.
        """
        email_lower = email.strip().lower()
        if any(u.email == email_lower for u in self._users):
            raise ValueError(f"A user with email '{email_lower}' already exists.")

        user = User(name=name, email=email_lower)
        self._users.append(user)
        self._save_all()
        logger.info("Created user: %s", user)
        return user

    def list_users(self) -> list[User]:
        """Return all users."""
        return list(self._users)

    def get_user(self, identifier: str) -> User | None:
        """
        Look up a user by name or ID string.

        Args:
            identifier: A name string or integer ID string.

        Returns:
            The matching User or None.
        """
        if identifier.isdigit():
            return find_user_by_id(self._users, int(identifier))
        return find_user_by_name(self._users, identifier)

    def delete_user(self, identifier: str) -> User:
        """
        Remove a user and all their projects (cascading).

        Args:
            identifier: Name or ID string.

        Returns:
            The deleted User.

        Raises:
            ValueError: If no matching user is found.
        """
        user = self.get_user(identifier)
        if not user:
            raise ValueError(f"User '{identifier}' not found.")

        # Cascade-delete owned projects
        for pid in list(user.project_ids):
            try:
                self._delete_project_by_id(pid)
            except ValueError:
                pass

        self._users = [u for u in self._users if u.id != user.id]
        self._save_all()
        logger.info("Deleted user: %s", user)
        return user

    def update_user(self, identifier: str, name: str | None = None, email: str | None = None) -> User:
        """
        Update a user's name and/or email.

        Args:
            identifier: Name or ID string.
            name:       New display name (optional).
            email:      New email address (optional).

        Returns:
            The updated User.

        Raises:
            ValueError: If no matching user found or email already taken.
        """
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

    # ------------------------------------------------------------------
    # Project operations
    # ------------------------------------------------------------------

    def add_project(
        self,
        title: str,
        user_identifier: str,
        description: str = "",
        due_date: str = "",
    ) -> Project:
        """
        Create a new Project and link it to a User.

        Args:
            title:           Project name.
            user_identifier: Owner name or ID string.
            description:     Optional description.
            due_date:        Optional YYYY-MM-DD deadline.

        Returns:
            The newly created Project.

        Raises:
            ValueError: If user not found or title already taken by that user.
        """
        owner = self.get_user(user_identifier)
        if not owner:
            raise ValueError(f"User '{user_identifier}' not found.")

        # Prevent duplicate project titles per user
        user_projects = projects_for_user(self._projects, owner.id)
        if find_project_by_title(user_projects, title):
            raise ValueError(
                f"User '{owner.name}' already has a project titled '{title}'."
            )

        project = Project(
            title=title,
            owner_id=owner.id,
            description=description,
            due_date=due_date,
        )
        self._projects.append(project)
        owner.add_project(project.id)
        self._save_all()
        logger.info("Created project: %s for user %s", project, owner)
        return project

    def list_projects(self, user_identifier: str | None = None) -> list[Project]:
        """
        Return all projects, or those owned by a specific user.

        Args:
            user_identifier: Optional name or ID to filter by.
        """
        if user_identifier is None:
            return list(self._projects)

        owner = self.get_user(user_identifier)
        if not owner:
            raise ValueError(f"User '{user_identifier}' not found.")
        return projects_for_user(self._projects, owner.id)

    def get_project(self, identifier: str) -> Project | None:
        """
        Look up a project by title or ID string.

        Args:
            identifier: Title string or integer ID string.
        """
        if identifier.isdigit():
            return find_project_by_id(self._projects, int(identifier))
        return find_project_by_title(self._projects, identifier)

    def update_project(
        self,
        identifier: str,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
    ) -> Project:
        """
        Update project fields.

        Args:
            identifier:  Title or ID string.
            title:       New title (optional).
            description: New description (optional).
            due_date:    New due date string (optional).

        Returns:
            The updated Project.

        Raises:
            ValueError: If project not found.
        """
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
        """
        Remove a project (and its tasks) by title or ID.

        Args:
            identifier: Title or ID string.

        Returns:
            The deleted Project.

        Raises:
            ValueError: If project not found.
        """
        project = self.get_project(identifier)
        if not project:
            raise ValueError(f"Project '{identifier}' not found.")
        return self._delete_project_by_id(project.id)

    def _delete_project_by_id(self, project_id: int) -> Project:
        """Internal helper: delete project by ID and clean up relationships."""
        project = find_project_by_id(self._projects, project_id)
        if not project:
            raise ValueError(f"Project ID {project_id} not found.")

        # Remove tasks belonging to this project
        self._tasks = [t for t in self._tasks if t.project_id != project_id]

        # Unlink from owner
        owner = find_user_by_id(self._users, project.owner_id)
        if owner:
            owner.remove_project(project_id)

        self._projects = [p for p in self._projects if p.id != project_id]
        self._save_all()
        logger.info("Deleted project: %s", project)
        return project

    def search_projects(self, query: str) -> list[Project]:
        """
        Search projects by partial title or description match (case-insensitive).

        Args:
            query: Search string.
        """
        q = query.strip().lower()
        return [
            p for p in self._projects
            if q in p.title.lower() or q in p.description.lower()
        ]

    # ------------------------------------------------------------------
    # Task operations
    # ------------------------------------------------------------------

    def add_task(
        self,
        title: str,
        project_identifier: str,
        assigned_to: str = "",
        status: str = TaskStatus.TODO,
    ) -> Task:
        """
        Create a new Task and link it to a Project.

        Args:
            title:               Task title.
            project_identifier:  Project title or ID string.
            assigned_to:         Optional assignee name/email.
            status:              Initial status (default: todo).

        Returns:
            The newly created Task.

        Raises:
            ValueError: If project not found or duplicate task title.
        """
        project = self.get_project(project_identifier)
        if not project:
            raise ValueError(f"Project '{project_identifier}' not found.")

        # Guard: prevent duplicate task titles within the same project
        existing = tasks_for_project(self._tasks, project.id)
        if find_task_by_title(existing, title):
            raise ValueError(
                f"Project '{project.title}' already has a task titled '{title}'."
            )

        task = Task(
            title=title,
            project_id=project.id,
            assigned_to=assigned_to,
            status=status,
        )
        self._tasks.append(task)
        project.add_task(task.id)
        self._save_all()
        logger.info("Created task: %s in project %s", task, project)
        return task

    def list_tasks(self, project_identifier: str | None = None) -> list[Task]:
        """
        Return all tasks, or those belonging to a specific project.

        Args:
            project_identifier: Optional project title or ID string.
        """
        if project_identifier is None:
            return list(self._tasks)

        project = self.get_project(project_identifier)
        if not project:
            raise ValueError(f"Project '{project_identifier}' not found.")
        return tasks_for_project(self._tasks, project.id)

    def get_task(self, identifier: str, project_identifier: str | None = None) -> Task | None:
        """
        Look up a task by title or ID string.

        Args:
            identifier:         Task title or integer ID string.
            project_identifier: Optional scoping project.
        """
        project_id = None
        if project_identifier:
            project = self.get_project(project_identifier)
            if project:
                project_id = project.id

        if identifier.isdigit():
            return find_task_by_id(self._tasks, int(identifier))
        return find_task_by_title(self._tasks, identifier, project_id)

    def complete_task(self, identifier: str, project_identifier: str | None = None) -> Task:
        """
        Mark a task as done.

        Args:
            identifier:         Task title or ID string.
            project_identifier: Optional scoping project.

        Returns:
            The updated Task.

        Raises:
            ValueError: If task not found.
        """
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        task.complete()
        self._save_all()
        return task

    def start_task(self, identifier: str, project_identifier: str | None = None) -> Task:
        """
        Mark a task as in_progress.

        Args:
            identifier:         Task title or ID string.
            project_identifier: Optional scoping project.

        Returns:
            The updated Task.

        Raises:
            ValueError: If task not found.
        """
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")
        task.start()
        self._save_all()
        return task

    def update_task(
        self,
        identifier: str,
        title: str | None = None,
        assigned_to: str | None = None,
        status: str | None = None,
        project_identifier: str | None = None,
    ) -> Task:
        """
        Update task fields.

        Args:
            identifier:         Task title or ID string.
            title:              New title (optional).
            assigned_to:        New assignee (optional).
            status:             New status string (optional).
            project_identifier: Optional scoping project.

        Returns:
            The updated Task.

        Raises:
            ValueError: If task not found.
        """
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
        """
        Remove a task.

        Args:
            identifier:         Task title or ID string.
            project_identifier: Optional scoping project.

        Returns:
            The deleted Task.

        Raises:
            ValueError: If task not found.
        """
        task = self.get_task(identifier, project_identifier)
        if not task:
            raise ValueError(f"Task '{identifier}' not found.")

        # Unlink from project
        project = find_project_by_id(self._projects, task.project_id)
        if project:
            project.remove_task(task.id)

        self._tasks = [t for t in self._tasks if t.id != task.id]
        self._save_all()
        logger.info("Deleted task: %s", task)
        return task

    def get_project_with_owner(self, identifier: str):
        """
        Return (project, owner_user) tuple for a given project identifier.

        Args:
            identifier: Project title or ID string.

        Returns:
            Tuple of (Project, User) or (None, None).
        """
        project = self.get_project(identifier)
        if not project:
            return None, None
        owner = find_user_by_id(self._users, project.owner_id)
        return project, owner