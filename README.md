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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All scheduling logic lives in the logic layer, `pawpal_system.py`. The table below maps each
implemented feature to the method that provides it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | `sort_tasks` orders by priority (highest first), then shortest duration as a tie-break; `sort_by_time` orders by each task's `preferred_time` (earliest first) and pushes untimed tasks to the end. |
| Filtering | `Scheduler.filter_tasks()` | Returns an owner's tasks filtered by completion status (`completed=True/False`) and/or pet name (`pet_name=...`, case-insensitive). Both filters are optional and compose. |
| Conflict handling | `Scheduler.build_plan()` (via `Scheduler.fits()`) | Tasks are packed back-to-back from the start time, so placed items never overlap — each task starts exactly when the previous one ends. `fits()` enforces the time budget; tasks that no longer fit are recorded in `DailyPlan.skipped` rather than dropped. (Note: fixed `preferred_time` slots are not yet enforced — see Tradeoffs in `reflection.md`.) |
| Recurring tasks | `Task.next_occurrence()`, `Task.mark_complete()` | Completing a `DAILY` or `WEEKLY` task automatically creates a fresh, pending copy for the next occurrence and adds it to the same pet. One-off tasks (`Recurrence.NONE`) do not repeat. |

The plan itself is assembled by `Scheduler.build_plan()` and explained in plain language by
`DailyPlan.explain()`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
