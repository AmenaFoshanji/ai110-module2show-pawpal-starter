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
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == pet_name)
            pet.add_task(
                Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=Priority[priority_label.upper()],
                )
            )
            st.success(f"Added '{task_title}' for {pet.name}.")

    # Show each pet's current tasks, read live from the Owner object.
    for pet in owner.pets:
        if pet.tasks:
            st.markdown(f"**{pet.name}'s tasks**")
            st.table(
                [
                    {
                        "Task": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority.name.lower(),
                        "Done": t.completed,
                    }
                    for t in pet.tasks
                ]
            )

st.divider()

st.subheader("Build schedule")
if st.button("Generate schedule"):
    if not owner.list_tasks():
        st.warning("No tasks to schedule yet. Add a pet and some tasks first.")
    else:
        plan = Scheduler().build_plan(owner)
        st.code(plan.explain())
