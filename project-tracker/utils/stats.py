from utils.helpers import projects_for_user, tasks_for_project

def user_summary(user, all_projects, all_tasks):
    """Return task completion summary for a single user."""
    projects = projects_for_user(all_projects, user.id)
    tasks = [t for p in projects for t in tasks_for_project(all_tasks, p.id)]
    done        = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    todo        = sum(1 for t in tasks if t.status == "todo")
    total       = len(tasks)
    return {
        "name": user.name, "email": user.email,
        "total_projects": len(projects), "total_tasks": total,
        "done": done, "in_progress": in_progress, "todo": todo,
        "completion_pct": round((done / total) * 100, 1) if total else 0.0,
    }

def project_summary(project, all_tasks):
    """Return task completion summary for a single project."""
    tasks = tasks_for_project(all_tasks, project.id)
    done        = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    todo        = sum(1 for t in tasks if t.status == "todo")
    total       = len(tasks)
    return {
        "title": project.title, "due_date": project.due_date,
        "is_overdue": project.is_overdue, "total_tasks": total,
        "done": done, "in_progress": in_progress, "todo": todo,
        "completion_pct": round((done / total) * 100, 1) if total else 0.0,
    }

def global_summary(all_users, all_projects, all_tasks):
    """Return overall system-wide statistics."""
    done        = sum(1 for t in all_tasks if t.status == "done")
    in_progress = sum(1 for t in all_tasks if t.status == "in_progress")
    todo        = sum(1 for t in all_tasks if t.status == "todo")
    total       = len(all_tasks)
    return {
        "total_users": len(all_users), "total_projects": len(all_projects),
        "total_tasks": total, "done": done, "in_progress": in_progress,
        "todo": todo,
        "completion_pct": round((done / total) * 100, 1) if total else 0.0,
        "overdue_projects": sum(1 for p in all_projects if p.is_overdue),
    }
