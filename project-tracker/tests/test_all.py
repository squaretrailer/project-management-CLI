"""
tests/test_all.py
-----------------
Unit tests covering models, helpers, storage layer, and CLI commands.
Run with:  python -m pytest tests/ -v
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.user import Person, User
from models.project import Project
from models.task import Task, TaskStatus
from utils.helpers import (
    validate_email, validate_date,
    find_user_by_name, find_user_by_id,
    find_project_by_title, find_project_by_id,
    find_task_by_title, find_task_by_id,
    tasks_for_project, projects_for_user,
)


# ==================================================================
# Model: Person
# ==================================================================

class TestPerson(unittest.TestCase):
    """Tests for the Person base class."""

    def test_valid_creation(self):
        p = Person("Alice", "alice@example.com")
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.email, "alice@example.com")

    def test_name_whitespace_stripped(self):
        p = Person("  Bob  ", "bob@test.com")
        self.assertEqual(p.name, "Bob")

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            Person("", "a@b.com")

    def test_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            Person("Alice", "not-an-email")

    def test_email_stored_lowercase(self):
        p = Person("Carol", "CAROL@EXAMPLE.COM")
        self.assertEqual(p.email, "carol@example.com")

    def test_repr(self):
        p = Person("Dave", "dave@x.com")
        self.assertIn("Person", repr(p))


# ==================================================================
# Model: User
# ==================================================================

class TestUser(unittest.TestCase):
    """Tests for the User class."""

    def setUp(self):
        """Reset the class-level ID counter before each test."""
        User._next_id = 1

    def test_auto_id_assigned(self):
        u1 = User("Alice", "alice@example.com")
        u2 = User("Bob", "bob@example.com")
        self.assertNotEqual(u1.id, u2.id)

    def test_explicit_id(self):
        u = User("Alice", "alice@example.com", user_id=99)
        self.assertEqual(u.id, 99)

    def test_add_project(self):
        u = User("Alice", "alice@example.com")
        u.add_project(5)
        self.assertIn(5, u.project_ids)

    def test_remove_project(self):
        u = User("Alice", "alice@example.com")
        u.add_project(5)
        u.remove_project(5)
        self.assertNotIn(5, u.project_ids)

    def test_add_project_no_duplicates(self):
        u = User("Alice", "alice@example.com")
        u.add_project(5)
        u.add_project(5)
        self.assertEqual(len(u.project_ids), 1)

    def test_to_dict_roundtrip(self):
        u = User("Alice", "alice@example.com")
        u.add_project(3)
        d = u.to_dict()
        u2 = User.from_dict(d)
        self.assertEqual(u.name, u2.name)
        self.assertEqual(u.email, u2.email)
        self.assertEqual(u.project_ids, u2.project_ids)

    def test_str(self):
        u = User("Alice", "alice@example.com")
        self.assertIn("Alice", str(u))


# ==================================================================
# Model: Project
# ==================================================================

class TestProject(unittest.TestCase):
    """Tests for the Project class."""

    def setUp(self):
        Project._next_id = 1

    def test_valid_creation(self):
        p = Project("My Project", owner_id=1)
        self.assertEqual(p.title, "My Project")

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            Project("", owner_id=1)

    def test_valid_due_date(self):
        p = Project("Proj", owner_id=1, due_date="2030-01-01")
        self.assertEqual(p.due_date, "2030-01-01")

    def test_invalid_due_date_raises(self):
        with self.assertRaises(ValueError):
            Project("Proj", owner_id=1, due_date="31-12-2025")

    def test_empty_due_date_allowed(self):
        p = Project("Proj", owner_id=1, due_date="")
        self.assertEqual(p.due_date, "")

    def test_is_overdue_past_date(self):
        p = Project("Proj", owner_id=1, due_date="2000-01-01")
        self.assertTrue(p.is_overdue)

    def test_is_overdue_future_date(self):
        p = Project("Proj", owner_id=1, due_date="2099-12-31")
        self.assertFalse(p.is_overdue)

    def test_add_remove_task(self):
        p = Project("Proj", owner_id=1)
        p.add_task(10)
        self.assertIn(10, p.task_ids)
        p.remove_task(10)
        self.assertNotIn(10, p.task_ids)

    def test_to_dict_roundtrip(self):
        p = Project("My Proj", owner_id=2, description="desc", due_date="2030-06-01")
        p.add_task(7)
        d = p.to_dict()
        p2 = Project.from_dict(d)
        self.assertEqual(p.title, p2.title)
        self.assertEqual(p.task_ids, p2.task_ids)


# ==================================================================
# Model: Task
# ==================================================================

class TestTask(unittest.TestCase):
    """Tests for the Task class."""

    def setUp(self):
        Task._next_id = 1

    def test_valid_creation(self):
        t = Task("Write tests", project_id=1)
        self.assertEqual(t.title, "Write tests")
        self.assertEqual(t.status, TaskStatus.TODO)

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            Task("", project_id=1)

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            Task("T", project_id=1, status="flying")

    def test_complete(self):
        t = Task("T", project_id=1)
        t.complete()
        self.assertEqual(t.status, TaskStatus.DONE)

    def test_start(self):
        t = Task("T", project_id=1)
        t.start()
        self.assertEqual(t.status, TaskStatus.IN_PROGRESS)

    def test_reset(self):
        t = Task("T", project_id=1)
        t.complete()
        t.reset()
        self.assertEqual(t.status, TaskStatus.TODO)

    def test_to_dict_roundtrip(self):
        t = Task("Fix bug", project_id=3, assigned_to="Bob", status="in_progress")
        d = t.to_dict()
        t2 = Task.from_dict(d)
        self.assertEqual(t.title, t2.title)
        self.assertEqual(t.status, t2.status)
        self.assertEqual(t.assigned_to, t2.assigned_to)

    def test_str_contains_title(self):
        t = Task("Deploy", project_id=1)
        self.assertIn("Deploy", str(t))


# ==================================================================
# Utils: Helpers
# ==================================================================

class TestHelpers(unittest.TestCase):
    """Tests for utility helper functions."""

    def test_validate_email_valid(self):
        self.assertTrue(validate_email("test@example.com"))

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email("notanemail"))
        self.assertFalse(validate_email("missing@dot"))

    def test_validate_date_valid(self):
        self.assertTrue(validate_date("2025-12-31"))
        self.assertTrue(validate_date(""))   # empty = no deadline

    def test_validate_date_invalid(self):
        self.assertFalse(validate_date("31-12-2025"))
        self.assertFalse(validate_date("2025/12/31"))

    def _make_users(self):
        User._next_id = 1
        return [
            User("Alice", "alice@x.com"),
            User("Bob", "bob@x.com"),
        ]

    def test_find_user_by_name(self):
        users = self._make_users()
        self.assertEqual(find_user_by_name(users, "alice").name, "Alice")

    def test_find_user_by_name_case_insensitive(self):
        users = self._make_users()
        self.assertEqual(find_user_by_name(users, "ALICE").name, "Alice")

    def test_find_user_by_name_not_found(self):
        users = self._make_users()
        self.assertIsNone(find_user_by_name(users, "Charlie"))

    def test_find_user_by_id(self):
        users = self._make_users()
        self.assertEqual(find_user_by_id(users, users[0].id).name, "Alice")

    def _make_projects(self, owner_id=1):
        Project._next_id = 1
        return [
            Project("Alpha", owner_id=owner_id),
            Project("Beta", owner_id=2),
        ]

    def test_find_project_by_title(self):
        projects = self._make_projects()
        self.assertEqual(find_project_by_title(projects, "alpha").title, "Alpha")

    def test_find_project_by_id(self):
        projects = self._make_projects()
        pid = projects[0].id
        self.assertEqual(find_project_by_id(projects, pid).title, "Alpha")

    def test_projects_for_user(self):
        projects = self._make_projects(owner_id=1)
        result = projects_for_user(projects, 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Alpha")

    def _make_tasks(self, project_id=1):
        Task._next_id = 1
        return [
            Task("Task A", project_id=project_id),
            Task("Task B", project_id=2),
        ]

    def test_find_task_by_title(self):
        tasks = self._make_tasks()
        self.assertEqual(find_task_by_title(tasks, "task a").title, "Task A")

    def test_find_task_by_id(self):
        tasks = self._make_tasks()
        tid = tasks[0].id
        self.assertEqual(find_task_by_id(tasks, tid).title, "Task A")

    def test_tasks_for_project(self):
        tasks = self._make_tasks(project_id=1)
        result = tasks_for_project(tasks, 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Task A")


# ==================================================================
# Utils: Storage (integration test using temp dir)
# ==================================================================

class TestStorage(unittest.TestCase):
    """Integration tests for JSON persistence layer."""

    def setUp(self):
        """Redirect DATA_DIR to a temp directory for isolation."""
        self.tmp_dir = tempfile.mkdtemp()
        import utils.storage as storage_mod
        self._original_data_dir = storage_mod.DATA_DIR
        storage_mod.DATA_DIR = Path(self.tmp_dir)
        storage_mod.USERS_FILE = Path(self.tmp_dir) / "users.json"
        storage_mod.PROJECTS_FILE = Path(self.tmp_dir) / "projects.json"
        storage_mod.TASKS_FILE = Path(self.tmp_dir) / "tasks.json"

    def tearDown(self):
        import utils.storage as storage_mod
        storage_mod.DATA_DIR = self._original_data_dir

    def test_save_and_load_users(self):
        from utils.storage import save_users, load_users
        User._next_id = 1
        users = [User("Alice", "alice@example.com"), User("Bob", "bob@example.com")]
        save_users(users)
        loaded = load_users()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["name"], "Alice")

    def test_save_and_load_projects(self):
        from utils.storage import save_projects, load_projects
        Project._next_id = 1
        projects = [Project("Proj", owner_id=1)]
        save_projects(projects)
        loaded = load_projects()
        self.assertEqual(loaded[0]["title"], "Proj")

    def test_save_and_load_tasks(self):
        from utils.storage import save_tasks, load_tasks
        Task._next_id = 1
        tasks = [Task("Fix", project_id=1, assigned_to="Alice")]
        save_tasks(tasks)
        loaded = load_tasks()
        self.assertEqual(loaded[0]["title"], "Fix")
        self.assertEqual(loaded[0]["assigned_to"], "Alice")

    def test_missing_file_returns_empty_list(self):
        from utils.storage import load_users
        self.assertEqual(load_users(), [])

    def test_malformed_json_returns_empty_list(self):
        from utils.storage import load_users, USERS_FILE
        USERS_FILE.write_text("NOT VALID JSON")
        self.assertEqual(load_users(), [])


# ==================================================================
# Core: Tracker
# ==================================================================

class TestTracker(unittest.TestCase):
    """Tests for the Tracker application logic layer."""

    def setUp(self):
        """Create a Tracker backed by a temp directory."""
        self.tmp_dir = tempfile.mkdtemp()
        import utils.storage as storage_mod
        storage_mod.DATA_DIR = Path(self.tmp_dir)
        storage_mod.USERS_FILE = Path(self.tmp_dir) / "users.json"
        storage_mod.PROJECTS_FILE = Path(self.tmp_dir) / "projects.json"
        storage_mod.TASKS_FILE = Path(self.tmp_dir) / "tasks.json"
        # Reset ID counters
        User._next_id = 1
        Project._next_id = 1
        Task._next_id = 1

        from core.tracker import Tracker
        self.tracker = Tracker()

    # Users
    def test_add_user(self):
        u = self.tracker.add_user("Alice", "alice@example.com")
        self.assertEqual(u.name, "Alice")
        self.assertEqual(len(self.tracker.users), 1)

    def test_add_duplicate_email_raises(self):
        self.tracker.add_user("Alice", "alice@example.com")
        with self.assertRaises(ValueError):
            self.tracker.add_user("Alice2", "alice@example.com")

    def test_get_user_by_name(self):
        self.tracker.add_user("Alice", "alice@example.com")
        u = self.tracker.get_user("Alice")
        self.assertIsNotNone(u)

    def test_get_user_by_id(self):
        u = self.tracker.add_user("Alice", "alice@example.com")
        found = self.tracker.get_user(str(u.id))
        self.assertEqual(found.id, u.id)

    def test_delete_user_cascades_projects(self):
        u = self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("Proj", str(u.id))
        self.tracker.delete_user("Alice")
        self.assertEqual(len(self.tracker.projects), 0)

    def test_update_user(self):
        self.tracker.add_user("Alice", "alice@example.com")
        updated = self.tracker.update_user("Alice", name="Alicia")
        self.assertEqual(updated.name, "Alicia")

    # Projects
    def test_add_project(self):
        self.tracker.add_user("Alice", "alice@example.com")
        p = self.tracker.add_project("API", "Alice")
        self.assertEqual(p.title, "API")

    def test_add_duplicate_project_raises(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        with self.assertRaises(ValueError):
            self.tracker.add_project("API", "Alice")

    def test_list_projects_by_user(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_user("Bob", "bob@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_project("Web", "Bob")
        alice_projects = self.tracker.list_projects("Alice")
        self.assertEqual(len(alice_projects), 1)
        self.assertEqual(alice_projects[0].title, "API")

    def test_search_projects(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API Gateway", "Alice", description="restful")
        self.tracker.add_project("Frontend", "Alice")
        results = self.tracker.search_projects("api")
        self.assertEqual(len(results), 1)

    def test_delete_project_cascades_tasks(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Fix bug", "API")
        self.tracker.delete_project("API")
        self.assertEqual(len(self.tracker.tasks), 0)

    # Tasks
    def test_add_task(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        t = self.tracker.add_task("Write tests", "API", assigned_to="Alice")
        self.assertEqual(t.title, "Write tests")
        self.assertEqual(t.assigned_to, "Alice")

    def test_complete_task(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Deploy", "API")
        t = self.tracker.complete_task("Deploy")
        self.assertEqual(t.status, TaskStatus.DONE)

    def test_start_task(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Deploy", "API")
        t = self.tracker.start_task("Deploy")
        self.assertEqual(t.status, TaskStatus.IN_PROGRESS)

    def test_update_task(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Deploy", "API")
        t = self.tracker.update_task("Deploy", assigned_to="Bob")
        self.assertEqual(t.assigned_to, "Bob")

    def test_delete_task(self):
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Deploy", "API")
        self.tracker.delete_task("Deploy")
        self.assertEqual(len(self.tracker.tasks), 0)

    def test_persistence_across_reload(self):
        """Data written to disk should survive a new Tracker instantiation."""
        self.tracker.add_user("Alice", "alice@example.com")
        self.tracker.add_project("API", "Alice")
        self.tracker.add_task("Write docs", "API")

        from core.tracker import Tracker
        fresh = Tracker()
        self.assertEqual(len(fresh.users), 1)
        self.assertEqual(len(fresh.projects), 1)
        self.assertEqual(len(fresh.tasks), 1)


# ==================================================================
# CLI: Command handlers (unit-tested with mock Tracker)
# ==================================================================

class TestCLICommands(unittest.TestCase):
    """Unit tests for CLI command handler functions using mock Tracker."""

    def _make_args(self, **kwargs) -> MagicMock:
        """Build a mock argparse.Namespace with given kwargs as attributes."""
        args = MagicMock()
        for k, v in kwargs.items():
            setattr(args, k, v)
        return args

    def test_cmd_add_user_success(self):
        from main import cmd_add_user
        tracker = MagicMock()
        tracker.add_user.return_value = MagicMock(name="Alice", email="a@b.com", id=1)
        args = self._make_args(name="Alice", email="a@b.com")
        result = cmd_add_user(args, tracker)
        self.assertEqual(result, 0)
        tracker.add_user.assert_called_once_with(name="Alice", email="a@b.com")

    def test_cmd_add_user_invalid_email(self):
        from main import cmd_add_user
        tracker = MagicMock()
        args = self._make_args(name="Alice", email="not-an-email")
        result = cmd_add_user(args, tracker)
        self.assertEqual(result, 1)
        tracker.add_user.assert_not_called()

    def test_cmd_add_user_duplicate_email(self):
        from main import cmd_add_user
        tracker = MagicMock()
        tracker.add_user.side_effect = ValueError("already exists")
        args = self._make_args(name="Alice", email="a@b.com")
        result = cmd_add_user(args, tracker)
        self.assertEqual(result, 1)

    def test_cmd_list_users(self):
        from main import cmd_list_users
        tracker = MagicMock()
        tracker.list_users.return_value = []
        args = self._make_args()
        result = cmd_list_users(args, tracker)
        self.assertEqual(result, 0)

    def test_cmd_add_project_success(self):
        from main import cmd_add_project
        tracker = MagicMock()
        tracker.add_project.return_value = MagicMock(title="API", id=1)
        args = self._make_args(user="Alice", title="API", desc="", due_date="")
        result = cmd_add_project(args, tracker)
        self.assertEqual(result, 0)

    def test_cmd_add_project_invalid_date(self):
        from main import cmd_add_project
        tracker = MagicMock()
        args = self._make_args(user="Alice", title="API", desc="", due_date="99-99-9999")
        result = cmd_add_project(args, tracker)
        self.assertEqual(result, 1)
        tracker.add_project.assert_not_called()

    def test_cmd_complete_task_success(self):
        from main import cmd_complete_task
        tracker = MagicMock()
        tracker.complete_task.return_value = MagicMock(title="Deploy")
        args = self._make_args(task="Deploy", project="")
        result = cmd_complete_task(args, tracker)
        self.assertEqual(result, 0)

    def test_cmd_complete_task_not_found(self):
        from main import cmd_complete_task
        tracker = MagicMock()
        tracker.complete_task.side_effect = ValueError("not found")
        args = self._make_args(task="Ghost", project="")
        result = cmd_complete_task(args, tracker)
        self.assertEqual(result, 1)

    def test_cmd_add_task_success(self):
        from main import cmd_add_task
        tracker = MagicMock()
        tracker.add_task.return_value = MagicMock(title="Write tests", id=1)
        args = self._make_args(project="API", title="Write tests", assign="", status="todo")
        result = cmd_add_task(args, tracker)
        self.assertEqual(result, 0)

    def test_cmd_delete_task(self):
        from main import cmd_delete_task
        tracker = MagicMock()
        tracker.delete_task.return_value = MagicMock(title="Deploy", id=1)
        args = self._make_args(task="Deploy", project="")
        result = cmd_delete_task(args, tracker)
        self.assertEqual(result, 0)


# ==================================================================
# Runner
# ==================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
