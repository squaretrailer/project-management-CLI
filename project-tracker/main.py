#!/usr/bin/env python3
"""
main.py  –  CLI entry point for the Project Tracker application.

Usage examples:
  python main.py add-user --name "Alice" --email alice@example.com
  python main.py add-project --user Alice --title "My App" --due-date 2025-12-31
  python main.py add-task --project "My App" --title "Write tests" --assign Alice
  python main.py complete-task --task "Write tests" --project "My App"
  python main.py list-tasks --project "My App"
"""

import argparse
import logging
import sys

from core.tracker import Tracker
from utils.display import (
    console, success, error, info,
    print_users, print_user_detail,
    print_projects, print_project_detail,
    print_tasks, print_banner,
)
from utils.helpers import validate_email, validate_date, tasks_for_project

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def get_tracker() -> Tracker:
    """Instantiate Tracker, loading all data from disk."""
    return Tracker()


# ── User handlers ──────────────────────────────────────────────────

def cmd_add_user(args, tracker) -> int:
    if not validate_email(args.email):
        error(f"Invalid email: '{args.email}'"); return 1
    try:
        u = tracker.add_user(name=args.name, email=args.email)
        success(f"User created: {u.name} <{u.email}> (ID {u.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_list_users(args, tracker) -> int:
    print_users(tracker.list_users()); return 0

def cmd_show_user(args, tracker) -> int:
    user = tracker.get_user(args.user)
    if not user:
        error(f"User '{args.user}' not found."); return 1
    print_user_detail(user, tracker.list_projects(user_identifier=str(user.id))); return 0

def cmd_update_user(args, tracker) -> int:
    if args.email and not validate_email(args.email):
        error(f"Invalid email: '{args.email}'"); return 1
    try:
        u = tracker.update_user(args.user, name=args.name or None, email=args.email or None)
        success(f"User updated: {u}"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_delete_user(args, tracker) -> int:
    user = tracker.get_user(args.user)
    if not user:
        error(f"User '{args.user}' not found."); return 1
    if not args.yes:
        console.print(f"[bold yellow]Delete '{user.name}' and all their data? [y/N][/bold yellow] ", end="")
        if input().strip().lower() not in ("y", "yes"):
            info("Aborted."); return 0
    try:
        d = tracker.delete_user(args.user)
        success(f"Deleted user: {d.name} (ID {d.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1


# ── Project handlers ───────────────────────────────────────────────

def cmd_add_project(args, tracker) -> int:
    if args.due_date and not validate_date(args.due_date):
        error(f"Invalid date '{args.due_date}'. Use YYYY-MM-DD."); return 1
    try:
        p = tracker.add_project(args.title, args.user, args.desc or "", args.due_date or "")
        success(f"Project created: '{p.title}' (ID {p.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_list_projects(args, tracker) -> int:
    try:
        projects = tracker.list_projects(user_identifier=args.user or None)
    except ValueError as e:
        error(str(e)); return 1
    title = f"Projects for '{args.user}'" if args.user else "All Projects"
    print_projects(projects, title=title); return 0

def cmd_show_project(args, tracker) -> int:
    project, owner = tracker.get_project_with_owner(args.project)
    if not project:
        error(f"Project '{args.project}' not found."); return 1
    print_project_detail(project, tasks_for_project(tracker.tasks, project.id),
                         owner_name=owner.name if owner else "Unknown"); return 0

def cmd_update_project(args, tracker) -> int:
    if args.due_date and not validate_date(args.due_date):
        error(f"Invalid date '{args.due_date}'. Use YYYY-MM-DD."); return 1
    try:
        p = tracker.update_project(args.project, title=args.title or None,
                                   description=args.desc, due_date=args.due_date)
        success(f"Project updated: '{p.title}' (ID {p.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_delete_project(args, tracker) -> int:
    project = tracker.get_project(args.project)
    if not project:
        error(f"Project '{args.project}' not found."); return 1
    if not args.yes:
        console.print(f"[bold yellow]Delete '{project.title}' and all its tasks? [y/N][/bold yellow] ", end="")
        if input().strip().lower() not in ("y", "yes"):
            info("Aborted."); return 0
    try:
        d = tracker.delete_project(args.project)
        success(f"Deleted project: '{d.title}' (ID {d.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_search_projects(args, tracker) -> int:
    results = tracker.search_projects(args.query)
    print_projects(results, title=f"Search results for '{args.query}'"); return 0


# ── Task handlers ──────────────────────────────────────────────────

def cmd_add_task(args, tracker) -> int:
    try:
        t = tracker.add_task(args.title, args.project, args.assign or "", args.status or "todo")
        success(f"Task created: '{t.title}' (ID {t.id}) in '{args.project}'"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_list_tasks(args, tracker) -> int:
    try:
        tasks = tracker.list_tasks(project_identifier=args.project or None)
    except ValueError as e:
        error(str(e)); return 1
    if args.status:
        tasks = [t for t in tasks if t.status == args.status]
    title = f"Tasks in '{args.project}'" if args.project else "All Tasks"
    if args.status:
        title += f" [{args.status}]"
    print_tasks(tasks, title=title); return 0

def cmd_complete_task(args, tracker) -> int:
    try:
        t = tracker.complete_task(args.task, project_identifier=args.project or None)
        success(f"Task '{t.title}' marked as DONE."); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_start_task(args, tracker) -> int:
    try:
        t = tracker.start_task(args.task, project_identifier=args.project or None)
        success(f"Task '{t.title}' marked as IN_PROGRESS."); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_update_task(args, tracker) -> int:
    try:
        t = tracker.update_task(args.task, title=args.title or None, assigned_to=args.assign,
                                status=args.status or None, project_identifier=args.project or None)
        success(f"Task updated: '{t.title}' (ID {t.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1

def cmd_delete_task(args, tracker) -> int:
    try:
        d = tracker.delete_task(args.task, project_identifier=args.project or None)
        success(f"Deleted task: '{d.title}' (ID {d.id})"); return 0
    except ValueError as e:
        error(str(e)); return 1


# ── Argument parser ────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project_tracker",
        description="Multi-user CLI project & task management tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # Users
    p = sub.add_parser("add-user", help="Create a new user.")
    p.add_argument("--name", required=True); p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_add_user)

    p = sub.add_parser("list-users", help="List all users.")
    p.set_defaults(func=cmd_list_users)

    p = sub.add_parser("show-user", help="Show a user's details and projects.")
    p.add_argument("--user", required=True)
    p.set_defaults(func=cmd_show_user)

    p = sub.add_parser("update-user", help="Update name or email.")
    p.add_argument("--user", required=True); p.add_argument("--name", default="")
    p.add_argument("--email", default="")
    p.set_defaults(func=cmd_update_user)

    p = sub.add_parser("delete-user", help="Delete user and all their data.")
    p.add_argument("--user", required=True); p.add_argument("--yes", "-y", action="store_true")
    p.set_defaults(func=cmd_delete_user)

    # Projects
    p = sub.add_parser("add-project", help="Add a project to a user.")
    p.add_argument("--user", required=True); p.add_argument("--title", required=True)
    p.add_argument("--desc", default=""); p.add_argument("--due-date", default="", dest="due_date")
    p.set_defaults(func=cmd_add_project)

    p = sub.add_parser("list-projects", help="List projects (optionally by user).")
    p.add_argument("--user", default="")
    p.set_defaults(func=cmd_list_projects)

    p = sub.add_parser("show-project", help="Show a project's details and tasks.")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_show_project)

    p = sub.add_parser("update-project", help="Update project fields.")
    p.add_argument("--project", required=True); p.add_argument("--title", default="")
    p.add_argument("--desc", default=None); p.add_argument("--due-date", default=None, dest="due_date")
    p.set_defaults(func=cmd_update_project)

    p = sub.add_parser("delete-project", help="Delete a project and its tasks.")
    p.add_argument("--project", required=True); p.add_argument("--yes", "-y", action="store_true")
    p.set_defaults(func=cmd_delete_project)

    p = sub.add_parser("search-projects", help="Search projects by title or description.")
    p.add_argument("--query", required=True)
    p.set_defaults(func=cmd_search_projects)

    # Tasks
    p = sub.add_parser("add-task", help="Add a task to a project.")
    p.add_argument("--project", required=True); p.add_argument("--title", required=True)
    p.add_argument("--assign", default="")
    p.add_argument("--status", default="todo", choices=["todo", "in_progress", "done"])
    p.set_defaults(func=cmd_add_task)

    p = sub.add_parser("list-tasks", help="List tasks (optionally by project/status).")
    p.add_argument("--project", default="")
    p.add_argument("--status", default="", choices=["", "todo", "in_progress", "done"])
    p.set_defaults(func=cmd_list_tasks)

    p = sub.add_parser("complete-task", help="Mark a task as done.")
    p.add_argument("--task", required=True); p.add_argument("--project", default="")
    p.set_defaults(func=cmd_complete_task)

    p = sub.add_parser("start-task", help="Mark a task as in-progress.")
    p.add_argument("--task", required=True); p.add_argument("--project", default="")
    p.set_defaults(func=cmd_start_task)

    p = sub.add_parser("update-task", help="Update task fields.")
    p.add_argument("--task", required=True); p.add_argument("--project", default="")
    p.add_argument("--title", default=""); p.add_argument("--assign", default=None)
    p.add_argument("--status", default="", choices=["", "todo", "in_progress", "done"])
    p.set_defaults(func=cmd_update_task)

    p = sub.add_parser("delete-task", help="Delete a task.")
    p.add_argument("--task", required=True); p.add_argument("--project", default="")
    p.set_defaults(func=cmd_delete_task)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    print_banner()
    tracker = get_tracker()
    return args.func(args, tracker)


if __name__ == "__main__":
    sys.exit(main())