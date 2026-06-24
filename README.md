# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

All logic lives in `pawpal_system.py`; the Streamlit UI in `app.py` is a thin layer over it.

- **Multi-pet care tracking** — one owner can have many pets, each with its own task list
  (`Owner`, `Pet`, `Task`).
- **Priority-aware daily planning** — `Scheduler.build_plan()` selects and orders tasks by
  priority (highest first), then shortest duration, packing them back-to-back from the owner's
  preferred start time.
- **Time-budget enforcement** — `Scheduler.fits()` keeps the plan within the owner's
  `available_minutes`; tasks that don't fit are reported in `DailyPlan.skipped` instead of being
  dropped silently.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks chronologically by
  `preferred_time`, with untimed tasks placed last.
- **Sorting by priority** — `Scheduler.sort_tasks()` orders by priority, then by shortest
  duration as a tie-break.
- **Filtering** — `Scheduler.filter_tasks()` filters tasks by completion status and/or pet name
  (case-insensitive); the two filters compose.
- **Conflict warnings** — `Scheduler.find_conflicts()` flags tasks pinned to the same
  `preferred_time` so the UI can warn the user about clashes.
- **Daily / weekly recurrence** — completing a recurring task (`Task.mark_complete()` →
  `Task.next_occurrence()`) automatically creates the next pending occurrence on the same pet;
  one-off tasks do not repeat.
- **Plain-language plan explanation** — `DailyPlan.explain()` states what was scheduled, when,
  and what was skipped and why.
- **Persistent UI state** — `app.py` stores the owner in `st.session_state`, so pets and tasks
  survive Streamlit's reruns.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Below is the actual terminal output from running the demo script (`python main.py`),
which builds an owner with two pets and six tasks, then prints the generated plan:

```
Jordan is caring for 2 pets with 6 total tasks today.

================================================
TODAY'S SCHEDULE
================================================
Daily plan for 2026-06-23: 5 task(s) scheduled, 85 min total.
Order: highest priority first, then shortest task, packed from your start time until available time runs out.
  08:00-08:10  Feeding (10 min) [priority: high]
  08:10-08:20  Feeding (10 min) [priority: high]
  08:20-08:50  Morning walk (30 min) [priority: high]
  08:50-09:05  Litter cleanup (15 min) [priority: medium]
  09:05-09:25  Grooming (20 min) [priority: low]
Skipped 1 task(s) - not enough time:
  - Fetch / enrichment (25 min) [priority: low]
================================================
```

The owner's 90-minute budget fills with the highest-priority tasks first; the lowest-priority
task that no longer fits is skipped rather than silently dropped.

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite in `tests/test_pawpal.py` (7 tests) covers the most important behaviors of the
logic layer:

- **Task completion** — `mark_complete()` flips a task's status to done.
- **Task management** — adding a task to a pet increases that pet's task count.
- **Recurrence logic** — completing a `DAILY`/`WEEKLY` task auto-creates the next occurrence,
  while a one-off (`NONE`) task does not.
- **Sorting correctness** — `sort_by_time()` returns tasks in chronological order, with
  untimed tasks placed last.
- **Conflict detection** — `find_conflicts()` flags tasks pinned to the same time, and does
  not flag unique or untimed tasks.

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\amena\Downloads\ai110-module2show-pawpal-starter-main\ai110-module2show-pawpal-starter-main
plugins: anyio-4.13.0
collected 7 items

tests\test_pawpal.py .......                                             [100%]

============================== 7 passed in 0.01s ==============================
```

### Confidence level

**★★★☆☆ (3 / 5).** All 7 tests pass and the core building blocks — completion, recurrence,
sorting, and conflict detection — are each covered by a focused test. Confidence is held at 3
rather than higher because the suite tests these behaviors mostly in isolation and does not yet
cover important edge cases: exact-fit time budgets in `build_plan()`, greedy packing continuing
after a skip, re-completing an already-completed recurring task (which currently spawns a
duplicate), and conflict *resolution* (the scheduler can flag duplicate times but does not yet
honor `preferred_time` when placing tasks). Adding those would raise confidence toward 5.

## 📐 Smarter Scheduling

All scheduling logic lives in the logic layer, `pawpal_system.py`. The table below maps each
implemented feature to the method that provides it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | `sort_tasks` orders by priority (highest first), then shortest duration as a tie-break; `sort_by_time` orders by each task's `preferred_time` (earliest first) and pushes untimed tasks to the end. |
| Filtering | `Scheduler.filter_tasks()` | Returns an owner's tasks filtered by completion status (`completed=True/False`) and/or pet name (`pet_name=...`, case-insensitive). Both filters are optional and compose. |
| Conflict handling | `Scheduler.find_conflicts()`, `Scheduler.build_plan()` (via `Scheduler.fits()`) | `find_conflicts()` flags tasks pinned to the same `preferred_time` so the UI can warn the user. In the plan itself, tasks are packed back-to-back from the start time, so placed items never overlap — each starts when the previous one ends. `fits()` enforces the time budget; tasks that no longer fit are recorded in `DailyPlan.skipped` rather than dropped. (Note: detected `preferred_time` conflicts are surfaced as warnings but not yet auto-resolved in the plan — see Tradeoffs in `reflection.md`.) |
| Recurring tasks | `Task.next_occurrence()`, `Task.mark_complete()` | Completing a `DAILY` or `WEEKLY` task automatically creates a fresh, pending copy for the next occurrence and adds it to the same pet. One-off tasks (`Recurrence.NONE`) do not repeat. |

The plan itself is assembled by `Scheduler.build_plan()` and explained in plain language by
`DailyPlan.explain()`.

## 📸 Demo Walkthrough

### Running the app

```bash
streamlit run app.py
```

### Main UI features and actions

The Streamlit app (`app.py`) is organized top-to-bottom as a single page:

- **Owner & day settings** — set the owner's name, the minutes available today (the time
  budget), and the preferred start time. These feed the scheduler directly.
- **Pets** — add a pet (name + species) via a form. Added pets appear immediately in a
  "Current pets" list.
- **Tasks** — add a task for a chosen pet with a title, duration, priority, and an optional
  pinned time ("Pin to a specific time?"). The task list supports:
  - a **filter** toggle (All / Pending / Completed),
  - **chronological sorting** of the displayed tasks,
  - **conflict warnings** when two tasks are pinned to the same time.
- **Build schedule** — one click generates the day's plan, shown as a clean table with a
  success summary, a warning listing any skipped tasks, and an expandable "Why this plan?"
  explanation.

### Example workflow

1. Set **Minutes available today** to, say, `90` and a preferred start of `08:00`.
2. **Add a pet** — e.g. "Mochi" (dog). It appears under Current pets.
3. **Add tasks** for Mochi — "Morning walk" (30 min, high), "Feeding" (10 min, high), and
   "Fetch / enrichment" (25 min, low). Optionally pin Feeding to `08:00`.
4. Add a second pet ("Luna", cat) and a couple of her tasks to see multi-pet planning.
5. Use the **filter** to view only Pending tasks; the list is shown **sorted by time**.
6. If two tasks share a pinned time, a **conflict warning** appears above the table.
7. Click **Generate schedule** to see today's plan: the highest-priority tasks are placed
   first, the total time stays within your budget, and anything that didn't fit is listed as
   skipped.

### Key Scheduler behaviors shown

- **Sorting** — `sort_by_time()` (chronological) for the task list, and `sort_tasks()`
  (priority, then duration) inside the plan.
- **Filtering** — `filter_tasks()` powers the All / Pending / Completed toggle.
- **Conflict warnings** — `find_conflicts()` flags same-time clashes.
- **Recurrence** — completing a daily/weekly task spawns its next occurrence.
- **Budget-aware planning + explanation** — `build_plan()` packs within the time budget and
  `explain()` justifies the result.

### Sample CLI output (`python main.py`)

The demo script exercises the same logic layer from the terminal — adding tasks out of order,
then sorting, filtering, demonstrating recurrence, and building the schedule:

```
Jordan is caring for 2 pets with 6 total tasks today.

TASKS AS ENTERED (out of order)
     18:00  Evening walk (30 min) [medium, pending]
  any time  Fetch / enrichment (25 min) [low, done]
     07:00  Morning walk (30 min) [high, pending]
  any time  Grooming (20 min) [low, pending]
     08:00  Feeding (10 min) [high, pending]
  any time  Litter cleanup (15 min) [medium, pending]

SORTED BY TIME (earliest first; untimed last)
     07:00  Morning walk (30 min) [high, pending]
     08:00  Feeding (10 min) [high, pending]
     18:00  Evening walk (30 min) [medium, pending]
  any time  Litter cleanup (15 min) [medium, pending]
  any time  Fetch / enrichment (25 min) [low, done]
  any time  Grooming (20 min) [low, pending]

SORTED BY PRIORITY (highest first, then shortest)
     08:00  Feeding (10 min) [high, pending]
     07:00  Morning walk (30 min) [high, pending]
  any time  Litter cleanup (15 min) [medium, pending]
     18:00  Evening walk (30 min) [medium, pending]
  any time  Grooming (20 min) [low, pending]
  any time  Fetch / enrichment (25 min) [low, done]

FILTER: pending tasks only
     18:00  Evening walk (30 min) [medium, pending]
     07:00  Morning walk (30 min) [high, pending]
  any time  Grooming (20 min) [low, pending]
     08:00  Feeding (10 min) [high, pending]
  any time  Litter cleanup (15 min) [medium, pending]

FILTER: completed tasks only
  any time  Fetch / enrichment (25 min) [low, done]

FILTER: Mochi's tasks only
     18:00  Evening walk (30 min) [medium, pending]
  any time  Fetch / enrichment (25 min) [low, done]
     07:00  Morning walk (30 min) [high, pending]

RECURRENCE: completing a daily task auto-creates the next occurrence
  Before: Luna has 3 tasks.
  Marked 'Feeding' (daily) complete ->
  After:  Luna has 4 tasks.
     08:00  Feeding (10 min) [high, done]
     08:00  Feeding (10 min) [high, pending]

====================================================
TODAY'S SCHEDULE
====================================================
Daily plan for 2026-06-23: 4 task(s) scheduled, 85 min total.
Order: highest priority first, then shortest task, packed from your start time until available time runs out.
  08:00-08:10  Feeding (10 min) [priority: high]
  08:10-08:40  Morning walk (30 min) [priority: high]
  08:40-08:55  Litter cleanup (15 min) [priority: medium]
  08:55-09:25  Evening walk (30 min) [priority: medium]
Skipped 1 task(s) - not enough time:
  - Grooming (20 min) [priority: low]
====================================================
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
