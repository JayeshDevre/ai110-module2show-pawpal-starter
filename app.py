import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session State Initialization ──────────────────────────────────────────────
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
    st.session_state.owner.name = owner_name
    st.session_state.owner.set_available_time(available_time)
    st.success(f"Owner '{owner_name}' saved — {available_time} min daily budget.")

st.divider()

# ── Section 2: Add a Pet ──────────────────────────────────────────────────────
st.subheader("2. Add a Pet")

col1, col2 = st.columns(2)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    pet = Pet(name=new_pet_name, species=new_pet_species)
    st.session_state.owner.add_pet(pet)
    st.success(f"Added {new_pet_name} ({new_pet_species})")

if st.session_state.owner.pets:
    st.write("Your pets:")
    for i, p in enumerate(st.session_state.owner.pets):
        task_count = len(p.get_pending_tasks())
        st.markdown(f"  **{i+1}. {p.name}** ({p.species}) — {task_count} pending task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Section 3: Add Tasks ──────────────────────────────────────────────────────
st.subheader("3. Add Tasks")

if not st.session_state.owner.pets:
    st.warning("Add at least one pet first.")
else:
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
        selected_pet.add_task(new_task)
        st.success(f"Added '{task_title}' to {selected_pet.name}")

    pending = selected_pet.get_pending_tasks()
    if pending:
        st.write(f"Tasks for **{selected_pet.name}**:")
        st.table([
            {"Task": t.title, "Duration (min)": t.duration_minutes,
             "Priority": t.priority, "Frequency": t.frequency}
            for t in pending
        ])
    else:
        st.info(f"No tasks yet for {selected_pet.name}.")

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
st.subheader("4. Generate Schedule")

# Filter controls — let user narrow the schedule view before generating
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    view_pet = st.selectbox(
        "View tasks for",
        ["All pets"] + [p.name for p in st.session_state.owner.pets],
        key="view_pet_filter",
    )
with filter_col2:
    sort_mode = st.radio("Sort schedule by", ["Priority", "Time"], horizontal=True)

if st.button("Generate schedule"):
    if not st.session_state.owner.pets:
        st.warning("Add a pet and some tasks first.")
    elif not st.session_state.owner.get_all_tasks():
        st.warning("No pending tasks found. Add tasks in Section 3.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule = scheduler.build_schedule()

        # ── Time budget progress bar ──────────────────────────────────────────
        used = st.session_state.owner.available_minutes - scheduler.remaining_minutes
        total = st.session_state.owner.available_minutes
        st.caption(f"Time used: {used} / {total} min")
        st.progress(used / total if total > 0 else 0)

        # ── Conflict warnings — shown ABOVE the schedule table ────────────────
        # Placed here so the owner sees problems before reading the plan.
        # st.warning() is used (not st.error) because the app keeps running —
        # the owner can still use the schedule but should review flagged items.
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.warning(
                f"**{len(conflicts)} time overlap(s) detected** — review before using this plan:"
            )
            for w in conflicts:
                # Strip leading spaces from the raw warning string for clean display
                st.warning(w.strip())

        # ── Skipped tasks — tasks that didn't fit the budget ──────────────────
        if scheduler.skipped:
            with st.expander(f"⚠️ {len(scheduler.skipped)} task(s) skipped (not enough time)"):
                st.table([
                    {"Task": t.title, "Duration (min)": t.duration_minutes,
                     "Priority": t.priority}
                    for t in scheduler.skipped
                ])

        # ── Schedule table — apply pet filter and sort mode ───────────────────
        pet_filter = None if view_pet == "All pets" else view_pet
        filtered = scheduler.filter_schedule(pet_name=pet_filter)

        # sort_by_time() uses integer start_offset — exact arithmetic, no string issues
        display = (
            scheduler.sort_by_time()
            if sort_mode == "Time"
            else filtered   # priority order is the default from build_schedule()
        )
        # Re-apply pet filter after sort_by_time() since it operates on full schedule
        if sort_mode == "Time" and pet_filter:
            pet_task_ids = {
                id(t)
                for p in st.session_state.owner.pets if p.name == pet_filter
                for t in p.get_tasks()
            }
            display = [st for st in display if id(st.task) in pet_task_ids]

        if not display:
            st.info(f"No scheduled tasks for '{view_pet}'.")
        else:
            st.success(f"Scheduled {len(display)} task(s) for {st.session_state.owner.name}!")
            st.table([
                {
                    "Time": f"{item.start_time} – {item.end_time}",
                    "Task": item.task.title,
                    "Duration (min)": item.task.duration_minutes,
                    "Priority": item.task.priority,
                    "Why": item.reason,
                }
                for item in display
            ])
