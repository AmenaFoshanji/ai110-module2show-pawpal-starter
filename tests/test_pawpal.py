"""Basic tests for the PawPal+ logic layer."""

from pawpal_system import Pet, Priority, Recurrence, Task


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
