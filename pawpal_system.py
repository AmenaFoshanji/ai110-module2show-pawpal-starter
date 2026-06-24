"""PawPal+ logic layer.

This module holds the backend classes for PawPal+, the pet care planning
assistant. It is the "logic layer": it knows nothing about Streamlit or any UI.
The UI (app.py) creates these objects, feeds them user input, and displays the
results.

Design (see design.mmd for the UML class diagram):

    Owner  1 --> *  Pet  1 --> *  Task --> Priority
    Scheduler ..> DailyPlan 1 --> * ScheduledItem --> Task

Classes are stubbed first (attributes + method signatures, no scheduling logic
yet) so the structure can be reviewed before behavior is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import IntEnum


class Priority(IntEnum):
    """How important a task is. IntEnum so tasks can be sorted by priority."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    """A single pet care task, e.g. a 20-minute morning walk."""

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    recurring: bool = False
    completed: bool = False

    def mark_done(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError

    def priority_weight(self) -> int:
        """Return a numeric weight used when sorting tasks (higher = sooner)."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet owned by an Owner. Holds the list of care tasks for that pet."""

    name: str
    species: str = "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner. Holds profile info and the day's scheduling constraints."""

    name: str
    available_minutes: int = 120
    preferred_start: time = time(8, 0)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def list_tasks(self) -> list[Task]:
        """Return all tasks across all of this owner's pets."""
        raise NotImplementedError


@dataclass
class ScheduledItem:
    """A task placed at a concrete time within a DailyPlan."""

    task: Task
    start_time: time
    end_time: time


@dataclass
class DailyPlan:
    """The result of scheduling: timed items, skipped tasks, and an explanation."""

    day: date
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total minutes of scheduled (non-skipped) tasks."""
        raise NotImplementedError

    def add_item(self, item: ScheduledItem) -> None:
        """Append a scheduled item to the plan."""
        raise NotImplementedError

    def explain(self) -> str:
        """Return human-readable reasoning for why the plan looks the way it does."""
        raise NotImplementedError


class Scheduler:
    """Turns a list of tasks into a DailyPlan, respecting time and priority."""

    def __init__(self, available_minutes: int, start_time: time = time(8, 0)) -> None:
        self.available_minutes = available_minutes
        self.start_time = start_time

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by the scheduling policy (e.g. priority first)."""
        raise NotImplementedError

    def fits(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining available time."""
        raise NotImplementedError

    def build_plan(self, tasks: list[Task], day: date | None = None) -> DailyPlan:
        """Select and order tasks into a DailyPlan for the given day."""
        raise NotImplementedError
