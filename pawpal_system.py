"""PawPal+ logic layer.

This module holds the backend classes for PawPal+, the pet care planning
assistant. It is the "logic layer": it knows nothing about Streamlit or any UI.
The UI (app.py) creates these objects, feeds them user input, and displays the
results.

Design (see design.mmd for the UML class diagram):

    Owner  1 --> *  Pet  1 --> *  Task --> Priority
    Scheduler ..> DailyPlan 1 --> * ScheduledItem --> Task

The scheduling policy is greedy and explainable: tasks are ordered by priority
(highest first), then by shortest duration, and packed sequentially from the
owner's preferred start time until their available minutes run out. Tasks that
do not fit are recorded as skipped rather than silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from uuid import uuid4


def _add_minutes(start: time, minutes: int) -> time:
    """Return the clock time `minutes` after `start` (wraps past midnight)."""
    return (datetime.combine(date.min, start) + timedelta(minutes=minutes)).time()


class Priority(IntEnum):
    """How important a task is. IntEnum so tasks can be sorted by priority."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(Enum):
    """How often a task repeats. Replaces the original recurring bool flag."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Task:
    """A single pet care task, e.g. a 20-minute morning walk."""

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    recurrence: Recurrence = Recurrence.NONE
    preferred_time: time | None = None
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)
    # Back-reference to the owning Pet, set by Pet.add_task. Excluded from repr
    # and equality so it can't cause infinite recursion between Pet and Task.
    pet: "Pet | None" = field(default=None, repr=False, compare=False)

    def mark_complete(self) -> None:
        """Mark this task as completed.

        If the task recurs (daily or weekly), completing it automatically creates
        a fresh, pending instance for the next occurrence and adds it to the same
        pet — so recurring care never silently drops off the list.
        """
        self.completed = True
        upcoming = self.next_occurrence()
        if upcoming is not None and self.pet is not None:
            self.pet.add_task(upcoming)

    def next_occurrence(self) -> "Task | None":
        """Return a fresh pending Task for the next occurrence, or None.

        One-off tasks (Recurrence.NONE) return None. Daily/weekly tasks return a
        copy with the same details but a new id and completed reset to False. The
        cadence is preserved, so the new instance will itself recur when done.
        """
        if self.recurrence == Recurrence.NONE:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            preferred_time=self.preferred_time,
        )


@dataclass
class Pet:
    """A pet owned by an Owner. Holds the list of care tasks for that pet."""

    name: str
    species: str = "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet, recording this pet on the task.

        The back-reference lets a recurring task add its next occurrence to the
        right pet when it is completed.
        """
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet, matched by its unique id."""
        self.tasks = [t for t in self.tasks if t.id != task.id]


@dataclass
class Owner:
    """The pet owner. Holds profile info and the day's scheduling constraints."""

    name: str
    available_minutes: int = 120
    preferred_start: time = time(8, 0)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def list_tasks(self) -> list[Task]:
        """Return all tasks across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


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
        return sum(item.task.duration_minutes for item in self.items)

    def add_item(self, item: ScheduledItem) -> None:
        """Append a scheduled item to the plan."""
        self.items.append(item)

    def explain(self) -> str:
        """Return human-readable reasoning for why the plan looks the way it does."""
        lines = [
            f"Daily plan for {self.day.isoformat()}: "
            f"{len(self.items)} task(s) scheduled, {self.total_minutes} min total.",
            "Order: highest priority first, then shortest task, packed from your "
            "start time until available time runs out.",
        ]
        for item in self.items:
            task = item.task
            lines.append(
                f"  {item.start_time:%H:%M}-{item.end_time:%H:%M}  "
                f"{task.title} ({task.duration_minutes} min) "
                f"[priority: {task.priority.name.lower()}]"
            )
        if self.skipped:
            lines.append(f"Skipped {len(self.skipped)} task(s) - not enough time:")
            for task in self.skipped:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) "
                    f"[priority: {task.priority.name.lower()}]"
                )
        return "\n".join(lines)


class Scheduler:
    """Turns an owner's tasks into a DailyPlan, respecting time and priority.

    The scheduler no longer stores the owner's constraints itself; it reads
    available_minutes and preferred_start from the Owner at planning time, so
    there is a single source of truth for those values.
    """

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (highest first), then shortest first.

        Shorter tasks break ties so that more high-priority work fits in the day.
        """
        return sorted(tasks, key=lambda t: (-int(t.priority), t.duration_minutes))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their preferred_time, earliest first.

        preferred_time is optional, so tasks that have no set time are pushed to
        the end (a missing time should not sort before a real 06:00 task). Higher
        priority breaks ties when two tasks share the same time.
        """
        return sorted(
            tasks,
            key=lambda t: (
                t.preferred_time is None,  # False (0) sorts before True (1)
                t.preferred_time or time.max,  # placeholder only used when None
                -int(t.priority),
            ),
        )

    def filter_tasks(
        self,
        owner: Owner,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return an owner's tasks, optionally filtered by completion and/or pet.

        Both filters are optional (keyword-only):
        - completed=True  -> only finished tasks; completed=False -> only pending.
        - pet_name="Mochi" -> only that pet's tasks (case-insensitive).

        Leaving a filter as None means "don't filter on it", so calling with no
        filters returns every task across all pets.
        """
        results: list[Task] = []
        for pet in owner.pets:
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    def find_conflicts(self, tasks: list[Task]) -> list[list[Task]]:
        """Return groups of tasks that are pinned to the same preferred_time.

        Two tasks asking for the same clock time cannot both happen then, so they
        are reported as a conflict. Untimed tasks (preferred_time is None) float
        freely and never conflict, so they are ignored. Each returned group has
        two or more tasks; an empty list means there are no time conflicts.
        """
        by_time: dict[time, list[Task]] = {}
        for task in tasks:
            if task.preferred_time is None:
                continue
            by_time.setdefault(task.preferred_time, []).append(task)
        return [group for group in by_time.values() if len(group) > 1]

    def fits(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining available time."""
        return task.duration_minutes <= remaining_minutes

    def build_plan(self, owner: Owner, day: date | None = None) -> DailyPlan:
        """Select and order an owner's tasks into a DailyPlan for the given day.

        Pulls the task list (owner.list_tasks) and the time constraints
        (available_minutes, preferred_start) directly from the owner. Already
        completed tasks are ignored. Tasks are placed in priority order and
        packed back-to-back from the start time; any that no longer fit in the
        remaining time are recorded as skipped.
        """
        if day is None:
            day = date.today()

        plan = DailyPlan(day=day)
        candidates = [t for t in owner.list_tasks() if not t.completed]
        remaining = owner.available_minutes
        clock = owner.preferred_start

        for task in self.sort_tasks(candidates):
            if self.fits(task, remaining):
                end = _add_minutes(clock, task.duration_minutes)
                plan.add_item(ScheduledItem(task=task, start_time=clock, end_time=end))
                clock = end
                remaining -= task.duration_minutes
            else:
                plan.skipped.append(task)

        return plan
