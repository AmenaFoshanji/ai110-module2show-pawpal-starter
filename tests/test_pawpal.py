"""Basic tests for the PawPal+ logic layer."""

from datetime import time

from pawpal_system import Pet, Priority, Recurrence, Scheduler, Task


def test_mark_complete_changes_task_status():
    """Completing a task should flip its `completed` status to True."""
    task = Task("Morning walk", 30, Priority.HIGH)
    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should grow that pet's task list by one."""
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0  # no tasks yet

    pet.add_task(Task("Feeding", 10, Priority.HIGH))

    assert len(pet.tasks) == 1


def test_completing_recurring_task_spawns_next_occurrence():
    """Completing a daily/weekly task should auto-add a fresh pending copy."""
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Feeding", 10, Priority.HIGH, Recurrence.DAILY))
    assert len(pet.tasks) == 1

    pet.tasks[0].mark_complete()

    # Original is now done; a new pending Feeding has been created on the pet.
    assert len(pet.tasks) == 2
    new_task = pet.tasks[1]
    assert new_task.title == "Feeding"
    assert new_task.completed is False
    assert new_task.recurrence is Recurrence.DAILY
    assert new_task.id != pet.tasks[0].id  # a genuinely new instance


def test_completing_one_off_task_does_not_spawn():
    """A non-recurring task should not create a next occurrence."""
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Vet visit", 60, Priority.HIGH, Recurrence.NONE))

    pet.tasks[0].mark_complete()

    assert len(pet.tasks) == 1


# --- Sorting correctness --------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time should order timed tasks earliest-first, untimed last."""
    scheduler = Scheduler()
    tasks = [
        Task("Evening walk", 20, Priority.LOW, preferred_time=time(18, 0)),
        Task("Anytime play", 20, Priority.LOW),  # no preferred_time
        Task("Morning walk", 20, Priority.HIGH, preferred_time=time(7, 0)),
        Task("Noon feed", 10, Priority.MEDIUM, preferred_time=time(12, 0)),
    ]

    ordered = scheduler.sort_by_time(tasks)
    titles = [t.title for t in ordered]

    # 07:00 -> 12:00 -> 18:00, then the untimed task at the end.
    assert titles == ["Morning walk", "Noon feed", "Evening walk", "Anytime play"]


# --- Conflict detection ---------------------------------------------------

def test_scheduler_flags_duplicate_times():
    """find_conflicts should group tasks pinned to the same preferred_time."""
    scheduler = Scheduler()
    tasks = [
        Task("Meds", 5, Priority.HIGH, preferred_time=time(9, 0)),
        Task("Breakfast", 10, Priority.MEDIUM, preferred_time=time(9, 0)),  # clash
        Task("Walk", 30, Priority.LOW, preferred_time=time(7, 0)),
    ]

    conflicts = scheduler.find_conflicts(tasks)

    assert len(conflicts) == 1  # exactly one clashing time (09:00)
    assert {t.title for t in conflicts[0]} == {"Meds", "Breakfast"}


def test_no_conflicts_for_unique_or_unset_times():
    """Unique times — and multiple untimed tasks — should not be flagged."""
    scheduler = Scheduler()
    tasks = [
        Task("A", 10, preferred_time=time(8, 0)),
        Task("B", 10, preferred_time=time(9, 0)),
        Task("C", 10),  # untimed -> never conflicts
        Task("D", 10),  # untimed -> never conflicts
    ]

    assert scheduler.find_conflicts(tasks) == []
