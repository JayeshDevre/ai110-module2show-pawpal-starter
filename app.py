import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session State Initialization ──────────────────────────────────────────────
# Streamlit reruns this script on every interaction.
# st.session_state is the persistent "vault" — objects created here survive reruns.
# Pattern: check if the key exists before creating, so we never overwrite live data.

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

# ── Section 1: Owner Setup ────────────────────────────────────────────────────
st.subheader("1. Owner")

col_a, col_b = st.columns(2)
with col_a:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
with col_b:
    available_time = st.number_input(
        "Available time (minutes)", min_value=10, max_value=480,
        value=st.session_state.owner.available_minutes,
    )

if st.button("Save owner"):
    # Direct attribute update — no recreation, so pets are not lost
    st.session_state.owner.name = owner_name
    st.session_state.owner.set_available_time(available_time)  # → Owner.set_available_time()
    st.success(f"Owner '{owner_name}' saved with {available_time} min budget.")

st.divider()

# ── Section 2: Add a Pet ──────────────────────────────────────────────────────
# UI action → owner.add_pet(new_pet)
# Streamlit shows the update immediately because session_state is mutated in place.

st.subheader("2. Add a Pet")

col1, col2 = st.columns(2)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    # Wire: create Pet object → call owner.add_pet() → session_state auto-reflects the change
    pet = Pet(name=new_pet_name, species=new_pet_species)
    st.session_state.owner.add_pet(pet)   # → Owner.add_pet()
    st.success(f"Added pet: {new_pet_name} ({new_pet_species})")

# Show all current pets so the user sees the update immediately after clicking "Add pet"
if st.session_state.owner.pets:
    st.write("Your pets:")
    for i, p in enumerate(st.session_state.owner.pets):
        task_count = len(p.get_pending_tasks())   # → Pet.get_pending_tasks()
        st.markdown(f"  **{i+1}. {p.name}** ({p.species}) — {task_count} pending task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Section 3: Add Tasks to a Pet ────────────────────────────────────────────
# UI action → pet.add_task(new_task)

st.subheader("3. Add Tasks")

if not st.session_state.owner.pets:
    st.warning("Add at least one pet first.")
else:
    # Let the user pick which pet to assign the task to
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)
    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)

    col3, col4, col5 = st.columns(3)
    with col3:
        task_title = st.text_input("Task title", value="Morning walk")
    with col4:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col5:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        new_task = Task(title=task_title, duration_minutes=int(duration), priority=priority)
        selected_pet.add_task(new_task)   # → Pet.add_task()
        st.success(f"Added '{task_title}' to {selected_pet.name}")

    # Show all pending tasks for the selected pet
    pending = selected_pet.get_pending_tasks()   # → Pet.get_pending_tasks()
    if pending:
        st.write(f"Tasks for **{selected_pet.name}**:")
        st.table([
            {"Task": t.title, "Duration (min)": t.duration_minutes, "Priority": t.priority}
            for t in pending
        ])
    else:
        st.info(f"No tasks yet for {selected_pet.name}.")

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
# UI action → Scheduler(owner).build_schedule()

st.subheader("4. Generate Schedule")

if st.button("Generate schedule"):
    if not st.session_state.owner.pets:
        st.warning("Add a pet and some tasks first.")
    elif not st.session_state.owner.get_all_tasks():   # → Owner.get_all_tasks()
        st.warning("No pending tasks found across any pet.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule = scheduler.build_schedule()   # → Scheduler.build_schedule()

        st.success(f"Scheduled {len(schedule)} task(s) for {st.session_state.owner.name}!")
        for item in schedule:
            st.markdown(f"- {item.explain()}")   # → ScheduledTask.explain()

        used = st.session_state.owner.available_minutes - scheduler.remaining_minutes
        st.caption(f"Time used: {used} / {st.session_state.owner.available_minutes} min")
