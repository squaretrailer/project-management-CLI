# Project Tracker CLI

A fully-featured command-line project management tool built in Python. Manage users, projects, and tasks from your terminal with persistent JSON storage, cascade-safe deletes, and a colour-coded Rich interface.

Built as part of a multi-user project tracker assignment demonstrating OOP design, CLI architecture, file I/O persistence, external package usage, and unit testing.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Object Model](#object-model)
- [Setup](#setup)
- [Running the CLI](#running-the-cli)
- [Command Reference](#command-reference)
- [Example Workflow](#example-workflow)
- [Data Persistence](#data-persistence)
- [Running Tests](#running-tests)
- [Dependencies](#dependencies)
- [Known Limitations](#known-limitations)

---

## Features

- **User management** — create, update, delete users with name and email validation
- **Project management** — assign projects to users with optional descriptions and YYYY-MM-DD due dates; automatic overdue detection with visual warnings
- **Task management** — assign tasks to projects with a clear status workflow: `todo → in_progress → done`
- **Search** — case-insensitive full-text search across project titles and descriptions
- **Cascade deletes** — deleting a user removes all their projects; deleting a project removes all its tasks
- **Persistent storage** — all data saved to local JSON files; atomic writes prevent corruption on failure
- **Rich CLI output** — colour-coded tables, panels, and status badges powered by the `rich` library
- **76 unit tests** — full coverage across models, helpers, storage layer, Tracker logic, and CLI handlers

---

## Project Structure

```
project_tracker/
│
├── main.py                  # CLI entry point — argparse subcommands and handlers
├── requirements.txt         # Python package dependencies
├── README.md
│
├── models/                  # Data model layer
│   ├── __init__.py
│   ├── user.py              # Person base class → User subclass (inheritance)
│   ├── project.py           # Project class with due-date validation
│   └── task.py              # Task class + TaskStatus enum
│
├── core/                    # Business logic layer
│   ├── __init__.py
│   └── tracker.py           # Tracker — CRUD operations, relationship management, persistence
│
├── utils/                   # Utility layer
│   ├── __init__.py
│   ├── storage.py           # Atomic JSON read/write with error handling
│   ├── display.py           # Rich-powered tables, panels, and feedback helpers
│   └── helpers.py           # Lookup functions and input validators
│
├── data/                    # Auto-created JSON data files (gitignored or committed empty)
│   ├── users.json
│   ├── projects.json
│   └── tasks.json
│
└── tests/
    └── test_all.py          # 76 unit tests across all layers
```

---

## Object Model

The system uses inheritance and one-to-many relationships across three entities:

```
Person  (base class — shared name/email validation)
└── User
    ├── id            auto-assigned int (class-level counter)
    ├── name          str, validated (non-empty, whitespace stripped)
    ├── email         str, validated (regex), stored lowercase, unique
    ├── created_at    ISO-8601 timestamp
    └── project_ids ──────────────────────────────────────────┐
                                                               ▼
                                                          Project
                                                           ├── id           auto-assigned int
                                                           ├── title        str, validated
                                                           ├── description  str (optional)
                                                           ├── due_date     YYYY-MM-DD (optional)
                                                           ├── owner_id     → User.id
                                                           ├── created_at   ISO-8601 timestamp
                                                           └── task_ids ──────────────────┐
                                                                                          ▼
                                                                                        Task
                                                                                         ├── id           auto-assigned int
                                                                                         ├── title        str, validated
                                                                                         ├── status       todo | in_progress | done
                                                                                         ├── assigned_to  str (optional)
                                                                                         ├── project_id   → Project.id
                                                                                         ├── created_at   ISO-8601 timestamp
                                                                                         └── updated_at   ISO-8601 timestamp
```

### OOP features used

| Feature | Where |
|---|---|
| Inheritance | `Person → User` |
| `@property` + setters | `name`, `email`, `title`, `due_date`, `status` on all models |
| Class-level ID counters | `User._next_id`, `Project._next_id`, `Task._next_id` |
| `__str__` / `__repr__` | All three model classes |
| `to_dict` / `from_dict` | Serialisation on all three model classes |
| Encapsulation | Private `_name`, `_email`, `_id`, `_status`, `_due_date` attributes |
| Enum | `TaskStatus(str, Enum)` for status values |

---

## Setup

### Prerequisites

- Python 3.10 or higher (uses `int | None` union syntax)
- pip

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd project_tracker
```

### 2. Create a virtual environment (recommended)

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or with Pipenv:

```bash
pip install pipenv
pipenv install
pipenv shell
```

---

## Running the CLI

All commands are run from the `project_tracker/` directory:

```bash
python main.py <command> [options]
```

Get help at any level:

```bash
python main.py --help
python main.py add-user --help
python main.py add-project --help
```

Enable verbose debug logging with `-v`:

```bash
python main.py -v list-projects
```

---

## Command Reference

### Users

| Command | Required flags | Optional flags | Description |
|---|---|---|---|
| `add-user` | `--name`, `--email` | | Create a new user |
| `list-users` | | | List all users in a table |
| `show-user` | `--user` | | Show user details and their projects |
| `update-user` | `--user` | `--name`, `--email` | Update a user's name or email |
| `delete-user` | `--user` | `--yes` / `-y` | Delete user and all their projects/tasks |

```bash
python main.py add-user --name "Alice" --email alice@example.com
python main.py list-users
python main.py show-user --user Alice
python main.py update-user --user Alice --name "Alicia" --email alicia@example.com
python main.py delete-user --user Alice --yes
```

> `--user` accepts either the user's **name** or their **numeric ID**.

---

### Projects

| Command | Required flags | Optional flags | Description |
|---|---|---|---|
| `add-project` | `--user`, `--title` | `--desc`, `--due-date` | Add a project to a user |
| `list-projects` | | `--user` | List all projects, or filter by user |
| `show-project` | `--project` | | Show project details and its tasks |
| `update-project` | `--project` | `--title`, `--desc`, `--due-date` | Update project fields |
| `delete-project` | `--project` | `--yes` / `-y` | Delete project and all its tasks |
| `search-projects` | `--query` | | Search by title or description |

```bash
python main.py add-project --user Alice --title "API Redesign" --desc "REST API v2" --due-date 2025-12-31
python main.py list-projects
python main.py list-projects --user Alice
python main.py show-project --project "API Redesign"
python main.py update-project --project "API Redesign" --due-date 2026-03-01
python main.py search-projects --query "api"
python main.py delete-project --project "API Redesign" --yes
```

> `--project` accepts either the project's **title** or its **numeric ID**.
> Projects with a past due date display a red ⚠ overdue warning automatically.

---

### Tasks

| Command | Required flags | Optional flags | Description |
|---|---|---|---|
| `add-task` | `--project`, `--title` | `--assign`, `--status` | Add a task to a project |
| `list-tasks` | | `--project`, `--status` | List all tasks, or filter by project/status |
| `start-task` | `--task` | `--project` | Mark a task as `in_progress` |
| `complete-task` | `--task` | `--project` | Mark a task as `done` |
| `update-task` | `--task` | `--project`, `--title`, `--assign`, `--status` | Update task fields |
| `delete-task` | `--task` | `--project` | Delete a task |

```bash
python main.py add-task --project "API Redesign" --title "Write OpenAPI spec" --assign Alice
python main.py add-task --project "API Redesign" --title "Write tests" --assign Bob --status in_progress
python main.py list-tasks --project "API Redesign"
python main.py list-tasks --status todo
python main.py start-task --task "Write OpenAPI spec"
python main.py complete-task --task "Write OpenAPI spec"
python main.py update-task --task "Write tests" --assign Alice --status done
python main.py delete-task --task "Write tests" --project "API Redesign"
```

> `--task` accepts either the task's **title** or its **numeric ID**.
> `--status` choices: `todo`, `in_progress`, `done`.

---

## Example Workflow

A complete end-to-end session:

```bash
# 1. Create your team
python main.py add-user --name "Alice" --email alice@dev.io
python main.py add-user --name "Bob"   --email bob@dev.io

# 2. Create projects
python main.py add-project --user Alice --title "Backend API"  --desc "REST API v2"   --due-date 2025-09-30
python main.py add-project --user Bob   --title "Frontend App" --desc "React SPA"     --due-date 2025-10-15

# 3. Add tasks
python main.py add-task --project "Backend API"  --title "Design schema"      --assign Alice
python main.py add-task --project "Backend API"  --title "Implement endpoints" --assign Alice
python main.py add-task --project "Backend API"  --title "Write tests"         --assign Bob
python main.py add-task --project "Frontend App" --title "Setup React"         --assign Bob
python main.py add-task --project "Frontend App" --title "Build dashboard"     --assign Bob

# 4. Progress tasks
python main.py start-task    --task "Design schema"
python main.py complete-task --task "Design schema"
python main.py start-task    --task "Implement endpoints"

# 5. Review
python main.py list-users
python main.py show-project  --project "Backend API"
python main.py list-tasks    --project "Backend API" --status done
python main.py list-tasks    --status in_progress
python main.py search-projects --query "react"
```

---

## Data Persistence

All data is stored as human-readable, pretty-printed JSON in the `data/` directory. Files are created automatically on first run.

```
data/
├── users.json       # All user records
├── projects.json    # All project records
└── tasks.json       # All task records
```

### Sample `data/users.json`

```json
[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@dev.io",
    "project_ids": [1],
    "created_at": "2025-06-10T14:32:00"
  }
]
```

### Reliability

- Writes use a **temp file + `os.replace`** pattern — data is never left half-written if the process is interrupted
- Missing files return an empty list (no crash on first run)
- Malformed JSON is caught and logged — the app continues with empty data rather than crashing
- **Cascade deletes** keep the files consistent: deleting a user removes their projects; deleting a project removes its tasks

---

## Running Tests

```bash
# Using pytest (recommended)
python -m pytest tests/ -v

# Using unittest directly
python -m unittest tests/test_all.py -v
```

### Test coverage — 76 tests across 6 classes

| Test class | What it covers |
|---|---|
| `TestPerson` | Name/email validation, whitespace stripping, lowercasing |
| `TestUser` | ID auto-assignment, project linking, serialisation roundtrip |
| `TestProject` | Title validation, due-date parsing, overdue detection, serialisation |
| `TestTask` | Status transitions (`complete`, `start`, `reset`), validation, serialisation |
| `TestHelpers` | All lookup functions (by name, by ID, by title), filter helpers |
| `TestStorage` | Save/load for all three entities, missing-file handling, malformed JSON handling |
| `TestTracker` | Full CRUD, cascade deletes, duplicate prevention, persistence across reload |
| `TestCLICommands` | CLI handlers via `MagicMock` — success paths, validation errors, not-found errors |

All tests run in isolated temp directories — they never touch real `data/` files.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| [`rich`](https://rich.readthedocs.io/) | ≥ 13.7.0 | Colour-coded tables, panels, and styled text in the terminal |
| [`tabulate`](https://pypi.org/project/tabulate/) | ≥ 0.9.0 | Fallback tabular formatting |
| [`colorama`](https://pypi.org/project/colorama/) | ≥ 0.4.6 | Cross-platform ANSI colour support on Windows |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## Known Limitations

- **No authentication** — all commands run with full admin access; there is no login system
- **Single-process only** — concurrent access from multiple terminals is not safe (last write wins)
- **Free-text assignee** — `--assign` accepts any string; it is not validated against registered users
- **No export** — there is no CSV or PDF export feature yet
- **In-memory only during a session** — the Tracker loads all data at startup; very large datasets (tens of thousands of records) would be slow

---

## License

MIT