import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def export_users(users, filepath):
    """Write all users to a CSV file."""
    path = Path(filepath)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["id", "name", "email", "projects", "created_at"]
        )
        writer.writeheader()
        for u in users:
            writer.writerow({
                "id": u.id, "name": u.name, "email": u.email,
                "projects": len(u.project_ids), "created_at": u.created_at,
            })
    return len(users)

def export_projects(projects, filepath):
    """Write all projects to a CSV file."""
    path = Path(filepath)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "id", "title", "description", "due_date",
            "tasks", "owner_id", "created_at"
        ])
        writer.writeheader()
        for p in projects:
            writer.writerow({
                "id": p.id, "title": p.title, "description": p.description,
                "due_date": p.due_date, "tasks": len(p.task_ids),
                "owner_id": p.owner_id, "created_at": p.created_at,
            })
    return len(projects)

def export_tasks(tasks, filepath):
    """Write all tasks to a CSV file."""
    path = Path(filepath)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "id", "title", "status", "assigned_to",
            "project_id", "created_at", "updated_at"
        ])
        writer.writeheader()
        for t in tasks:
            writer.writerow({
                "id": t.id, "title": t.title, "status": t.status,
                "assigned_to": t.assigned_to, "project_id": t.project_id,
                "created_at": t.created_at, "updated_at": t.updated_at,
            })
    return len(tasks)
