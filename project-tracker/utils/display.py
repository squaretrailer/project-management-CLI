"""
utils/display.py
----------------
All Rich-based formatting helpers for CLI output.
Centralises table/panel/status rendering so commands stay clean.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

STATUS_STYLES = {
    "todo": "bold yellow",
    "in_progress": "bold blue",
    "done": "bold green",
}


def _status_text(status: str) -> Text:
    """Return a colour-coded Rich Text object for a task status."""
    label = status.replace("_", " ").upper()
    style = STATUS_STYLES.get(status, "white")
    return Text(label, style=style)


def success(message: str) -> None:
    console.print(f"[bold green]✔  {message}[/bold green]")


def error(message: str) -> None:
    console.print(f"[bold red]✘  {message}[/bold red]")


def info(message: str) -> None:
    console.print(f"[dim]ℹ  {message}[/dim]")


def warn(message: str) -> None:
    console.print(f"[bold yellow]⚠  {message}[/bold yellow]")


def print_users(users: list) -> None:
    """Render a Rich table of all User objects."""
    if not users:
        info("No users found.")
        return
    table = Table(title="[bold cyan]Users[/bold cyan]", box=box.ROUNDED,
                  show_lines=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Email", style="cyan")
    table.add_column("Projects", justify="center")
    table.add_column("Created", style="dim")
    for u in users:
        table.add_row(str(u.id), u.name, u.email, str(len(u.project_ids)), u.created_at[:10])
    console.print(table)


def print_user_detail(user, projects: list) -> None:
    """Render a detailed panel for a single user plus their projects."""
    body = Text()
    body.append("ID:      ", style="dim"); body.append(f"{user.id}\n", style="bold white")
    body.append("Name:    ", style="dim"); body.append(f"{user.name}\n", style="bold white")
    body.append("Email:   ", style="dim"); body.append(f"{user.email}\n", style="cyan")
    body.append("Joined:  ", style="dim"); body.append(f"{user.created_at[:10]}\n", style="white")
    body.append(f"Projects: {len(projects)}", style="dim")
    console.print(Panel(body, title=f"[bold cyan]User — {user.name}[/bold cyan]", expand=False))
    if projects:
        print_projects(projects, title=f"Projects owned by {user.name}")


def print_projects(projects: list, title: str = "Projects") -> None:
    """Render a Rich table of Project objects."""
    if not projects:
        info("No projects found.")
        return
    table = Table(title=f"[bold cyan]{title}[/bold cyan]", box=box.ROUNDED,
                  show_lines=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Title", style="bold white")
    table.add_column("Description")
    table.add_column("Due Date", justify="center")
    table.add_column("Tasks", justify="center")
    table.add_column("Created", style="dim")
    for p in projects:
        due = p.due_date if p.due_date else "—"
        if p.is_overdue:
            due = f"[bold red]{due} ⚠[/bold red]"
        table.add_row(str(p.id), p.title, p.description or "—", due,
                      str(len(p.task_ids)), p.created_at[:10])
    console.print(table)


def print_project_detail(project, tasks: list, owner_name: str = "") -> None:
    """Render a detailed panel for a single project plus its tasks."""
    body = Text()
    body.append("ID:          ", style="dim"); body.append(f"{project.id}\n", style="bold white")
    body.append("Title:       ", style="dim"); body.append(f"{project.title}\n", style="bold white")
    if project.description:
        body.append("Description: ", style="dim"); body.append(f"{project.description}\n", style="white")
    if owner_name:
        body.append("Owner:       ", style="dim"); body.append(f"{owner_name}\n", style="cyan")
    due = project.due_date if project.due_date else "None"
    body.append("Due Date:    ", style="dim")
    body.append(f"{due}\n", style="bold red" if project.is_overdue else "white")
    body.append(f"Tasks:       {len(tasks)}", style="dim")
    console.print(Panel(body, title=f"[bold cyan]Project — {project.title}[/bold cyan]", expand=False))
    if tasks:
        print_tasks(tasks, title=f"Tasks in '{project.title}'")


def print_tasks(tasks: list, title: str = "Tasks") -> None:
    """Render a Rich table of Task objects."""
    if not tasks:
        info("No tasks found.")
        return
    table = Table(title=f"[bold cyan]{title}[/bold cyan]", box=box.ROUNDED,
                  show_lines=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Title", style="bold white")
    table.add_column("Status", justify="center")
    table.add_column("Assigned To")
    table.add_column("Updated", style="dim")
    for t in tasks:
        table.add_row(str(t.id), t.title, _status_text(t.status),
                      t.assigned_to or "—", t.updated_at[:10])
    console.print(table)


def print_banner() -> None:
    """Print the application welcome banner."""
    banner = Text()
    banner.append("  Project Tracker CLI\n", style="bold cyan")
    banner.append("  Multi-user project & task management\n", style="dim")
    console.print(Panel(banner, box=box.DOUBLE_EDGE, expand=False))