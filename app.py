from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session memory -------------------------------------------------------
# Streamlit reruns this entire script top-to-bottom on every interaction, so
# anything created at module scope is rebuilt (and emptied) each time. To make
# the Owner — and the Pets/Tasks it holds — persist across reruns, we keep it in
# st.session_state, which behaves like a dict that survives between runs.
#
# Check-before-create: only build a fresh Owner the first time. If one already
# lives in the session "vault", reuse it so the user's data isn't wiped on every
# button click or page refresh.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

# Convenient handle for the rest of the script to read/modify.
owner = st.session_state.owner

# The scheduler is stateless, so one shared instance is fine for the whole page.
scheduler = Scheduler()

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, a pet care planning assistant.

Set your day's time budget, add your pets and their care tasks, then generate a
daily plan. The UI is wired to the logic layer in `pawpal_system.py`.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner & day settings")
# Editing these writes straight back onto the persisted Owner object.
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Minutes available today",
        min_value=15,
        max_value=1440,
        value=owner.available_minutes,
        step=15,
    )
)
owner.preferred_start = st.time_input("Preferred start time", value=owner.preferred_start)

st.divider()

st.subheader("Pets")
# Add a pet: the form data is handled by Owner.add_pet(), which appends a new
# Pet to the owner's pet list. The rerun triggered by the submit then re-reads
# owner.pets below, so the new pet shows up immediately.
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="")
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if new_pet_name.strip():
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_species))
            st.success(f"Added {new_pet_name.strip()}.")
        else:
            st.warning("Please enter a pet name.")

if owner.pets:
    st.write("Current pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Tasks")
# Tasks attach to a specific pet, so a pet must exist first.
if not owner.pets:
    st.info("Add a pet first, then you can add tasks for it.")
else:
    # Add a task: Pet.add_task() handles the data, appending a Task to that pet.
    with st.form("add_task_form", clear_on_submit=True):
        pet_name = st.selectbox("For which pet?", [p.name for p in owner.pets])
        task_title = st.text_input("Task title", value="Morning walk")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col2:
            priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col3, col4 = st.columns(2)
        with col3:
            pin_time = st.checkbox("Pin to a specific time?")
        with col4:
            chosen_time = st.time_input("Preferred time", value=time(8, 0))
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == pet_name)
            pet.add_task(
                Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=Priority[priority_label.upper()],
                    preferred_time=chosen_time if pin_time else None,
                )
            )
            st.success(f"Added '{task_title}' for {pet.name}.")

    # Conflict detection: warn about tasks pinned to the same clock time.
    for group in scheduler.find_conflicts(owner.list_tasks()):
        slot = group[0].preferred_time.strftime("%H:%M")
        names = ", ".join(f"{t.pet.name}: {t.title}" for t in group)
        st.warning(f"⚠️ Time conflict at {slot} — {names}")

    # Filter control: show all tasks, only pending, or only completed.
    view = st.radio("Show", ["All", "Pending", "Completed"], horizontal=True)
    completed_filter = {"All": None, "Pending": False, "Completed": True}[view]
    tasks = scheduler.filter_tasks(owner, completed=completed_filter)

    # Sort the filtered tasks into chronological order for display.
    tasks = scheduler.sort_by_time(tasks)

    if tasks:
        st.table(
            [
                {
                    "Time": t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
                    "Pet": t.pet.name if t.pet else "—",
                    "Task": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority.name.lower(),
                    "Done": "✓" if t.completed else "",
                }
                for t in tasks
            ]
        )
    else:
        st.info(f"No {view.lower()} tasks to show.")

st.divider()

st.subheader("Build schedule")
if st.button("Generate schedule"):
    if not owner.list_tasks():
        st.warning("No tasks to schedule yet. Add a pet and some tasks first.")
    else:
        plan = scheduler.build_plan(owner)
        st.success(
            f"Scheduled {len(plan.items)} task(s) — {plan.total_minutes} of "
            f"{owner.available_minutes} available minutes used."
        )
        if plan.items:
            st.table(
                [
                    {
                        "Start": item.start_time.strftime("%H:%M"),
                        "End": item.end_time.strftime("%H:%M"),
                        "Pet": item.task.pet.name if item.task.pet else "—",
                        "Task": item.task.title,
                        "Duration (min)": item.task.duration_minutes,
                        "Priority": item.task.priority.name.lower(),
                    }
                    for item in plan.items
                ]
            )
        if plan.skipped:
            skipped = ", ".join(
                f"{t.title} ({t.duration_minutes} min)" for t in plan.skipped
            )
            st.warning(f"Skipped — not enough time: {skipped}")

        # The plan's own plain-language reasoning, tucked away for the curious.
        with st.expander("Why this plan?"):
            st.code(plan.explain())
