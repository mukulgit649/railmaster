"""In-memory mutable state for the simulation. Resets on process restart."""

from .data import default_conditions

_conditions = default_conditions()


def get_conditions() -> dict:
    return _conditions


def set_conditions(new_conditions: dict) -> dict:
    global _conditions
    _conditions = new_conditions
    return _conditions


def reset_conditions() -> dict:
    global _conditions
    _conditions = default_conditions()
    return _conditions
