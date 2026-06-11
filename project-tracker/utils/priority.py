from enum import Enum

class Priority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

PRIORITY_STYLES = {
    Priority.LOW:    "dim green",
    Priority.MEDIUM: "bold yellow",
    Priority.HIGH:   "bold red",
}

def priority_label(value: str) -> str:
    """Return a display label for a priority value."""
    return value.upper()
