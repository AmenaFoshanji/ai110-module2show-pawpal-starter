"""PawPal+ demo script.

A temporary "testing ground" to verify the logic layer works from the terminal.
Run it with:  python main.py

It builds an owner with two pets and several care tasks (added deliberately
out of time order), then exercises the Scheduler's sorting, filtering, and
scheduling methods so we can see they work.
"""

from datetime import time

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task


def show(task: Task) -> str:
    """One-line description of a task for printing."""
    when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "any time"
    status = "done" if task.completed else "pending"
    return (
        f"  {when:>8}  {task.title} ({task.duration_minutes} min) "
        f"[{task.priority.name.lower()}, {status}]"
    )


def main() -> None:
    # 1. Create an owner with a daily time budget and a preferred start time.
    owner = Owner(name="Jordan", available_minutes=90, preferred_start=time(8, 0))

    # 2. Create two pets and register them under the owner.
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # 3. Add tasks OUT OF ORDER on purpose (evening before morning, untimed in
    #    the middle) so the sorting method has something real to fix.
    mochi.add_task(Task("Evening walk", 30, Priority.MEDIUM, preferred_time=time(18, 0)))
    mochi.add_task(Task("Fetch / enrichment", 25, Priority.LOW))  # no set time
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, preferred_time=time(7, 0)))

    luna.add_task(Task("Grooming", 20, Priority.LOW, Recurrence.WEEKLY))
    luna.add_task(Task("Feeding", 10, Priority.HIGH, Recurrence.DAILY, preferred_time=time(8, 0)))
    luna.add_task(Task("Litter cleanup", 15, Priority.MEDIUM))  # no set time

    # Mark a one-off task complete so the completion filter has something to show.
    # (Fetch is Recurrence.NONE, so completing it does NOT spawn a new instance.)
    next(t for t in mochi.tasks if t.title == "Fetch / enrichment").mark_complete()

    scheduler = Scheduler()

    print(f"{owner.name} is caring for {len(owner.pets)} pets "
          f"with {len(owner.list_tasks())} total tasks today.\n")

    # --- Tasks as entered (out of order) ---------------------------------
    print("TASKS AS ENTERED (out of order)")
    for task in owner.list_tasks():
        print(show(task))

    # --- Sorting: by preferred time --------------------------------------
    print("\nSORTED BY TIME (earliest first; untimed last)")
    for task in scheduler.sort_by_time(owner.list_tasks()):
        print(show(task))

    # --- Sorting: by priority then duration ------------------------------
    print("\nSORTED BY PRIORITY (highest first, then shortest)")
    for task in scheduler.sort_tasks(owner.list_tasks()):
        print(show(task))

    # --- Filtering -------------------------------------------------------
    print("\nFILTER: pending tasks only")
    for task in scheduler.filter_tasks(owner, completed=False):
        print(show(task))

    print("\nFILTER: completed tasks only")
    for task in scheduler.filter_tasks(owner, completed=True):
        print(show(task))

    print("\nFILTER: Mochi's tasks only")
    for task in scheduler.filter_tasks(owner, pet_name="Mochi"):
        print(show(task))

    # --- Recurrence: completing a recurring task spawns the next one -----
    print("\nRECURRENCE: completing a daily task auto-creates the next occurrence")
    feeding = next(t for t in luna.tasks if t.title == "Feeding")  # daily
    print(f"  Before: Luna has {len(luna.tasks)} tasks.")
    feeding.mark_complete()
    print(f"  Marked '{feeding.title}' (daily) complete ->")
    print(f"  After:  Luna has {len(luna.tasks)} tasks.")
    for task in luna.tasks:
        if task.title == "Feeding":
            print(show(task))

    # --- Scheduling: today's plan ----------------------------------------
    plan = scheduler.build_plan(owner)
    print("\n" + "=" * 52)
    print("TODAY'S SCHEDULE")
    print("=" * 52)
    print(plan.explain())
    print("=" * 52)


if __name__ == "__main__":
    main()
