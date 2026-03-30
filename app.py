import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Display helpers ────────────────────────────────────────────────────────────

_CATEGORY_EMOJI = {
    "walk":       "🦮",
    "feed":       "🍖",
    "meds":       "💊",
    "groom":      "✂️",
    "enrichment": "🧸",
    "general":    "📋",
}

_PRIORITY_COLOR = {
    "high":   "#e74c3c",
    "medium": "#f39c12",
    "low":    "#27ae60",
}

_SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈"}
_FREQ_EMOJI    = {"daily": "🔁", "weekly": "📅", "as-needed": "🎯"}


def category_emoji(category: str) -> str:
    return _CATEGORY_EMOJI.get(category, "📋")


def priority_badge(priority: str) -> str:
    """Return an inline HTML colored badge for a priority level."""
    color = _PRIORITY_COLOR.get(priority, "#888")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:700">'
        f'{priority.upper()}</span>'
    )


def species_emoji(species: str) -> str:
    return _SPECIES_EMOJI.get(species, "🐾")


def freq_emoji(frequency: str) -> str:
    return _FREQ_EMOJI.get(frequency, "📋")


def pending_dot(count: int) -> str:
    """Traffic-light dot based on how many tasks are pending."""
    if count == 0:
        return "🟢"
    if count <= 3:
        return "🟡"
    return "🔴"


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
    st.success(f"✅ Owner **{owner_name}** saved — {available_time} min daily budget.")

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
    st.success(
        f"{species_emoji(new_pet_species)} Added **{new_pet_name}** ({new_pet_species})"
    )

if st.session_state.owner.pets:
    st.write("Your pets:")
    for i, p in enumerate(st.session_state.owner.pets):
        count = len(p.get_pending_tasks())
        st.markdown(
            f"&nbsp;&nbsp;**{i+1}. {species_emoji(p.species)} {p.name}** "
            f"({p.species}) — {pending_dot(count)} {count} pending task(s)"
        )
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
    selected_pet = next(
        p for p in st.session_state.owner.pets if p.name == selected_pet_name
    )

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        task_title = st.text_input("Task title", value="Morning walk")
    with col4:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col5:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col6:
        category = st.selectbox(
            "Category",
            ["walk", "feed", "meds", "groom", "enrichment", "general"],
        )

    if st.button("Add task"):
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
        )
        selected_pet.add_task(new_task)
        st.success(
            f"{category_emoji(category)} Added **'{task_title}'** to "
            f"{species_emoji(selected_pet.species)} {selected_pet.name}"
        )

    pending = selected_pet.get_pending_tasks()
    if pending:
        st.write(
            f"Tasks for **{species_emoji(selected_pet.species)} {selected_pet.name}**:"
        )
        rows = "".join(
            f"<tr style='border-top:1px solid #e8e8e8'>"
            f"<td style='padding:6px 10px'>{category_emoji(t.category)} {t.title}</td>"
            f"<td style='padding:6px 10px;text-align:center'>{t.duration_minutes}</td>"
            f"<td style='padding:6px 10px'>{priority_badge(t.priority)}</td>"
            f"<td style='padding:6px 10px;text-align:center'>"
            f"{freq_emoji(t.frequency)} {t.frequency}</td>"
            f"</tr>"
            for t in pending
        )
        st.markdown(
            f"""<table style='width:100%;border-collapse:collapse;font-size:0.9rem'>
              <thead><tr style='background:#f0f2f6'>
                <th style='text-align:left;padding:7px 10px'>Task</th>
                <th style='padding:7px 10px'>Duration (min)</th>
                <th style='padding:7px 10px'>Priority</th>
                <th style='padding:7px 10px'>Frequency</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>""",
            unsafe_allow_html=True,
        )
    else:
        st.info(
            f"No tasks yet for {species_emoji(selected_pet.species)} {selected_pet.name}."
        )

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
st.subheader("4. Generate Schedule")

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
        scheduler.build_schedule()

        # ── Colored time budget bar ───────────────────────────────────────────
        used  = st.session_state.owner.available_minutes - scheduler.remaining_minutes
        total = st.session_state.owner.available_minutes
        pct   = used / total if total > 0 else 0
        bar_color = (
            _PRIORITY_COLOR["high"]   if pct > 0.85 else
            _PRIORITY_COLOR["medium"] if pct > 0.60 else
            _PRIORITY_COLOR["low"]
        )
        st.markdown(
            f"""<div style='margin-bottom:4px;font-size:0.85rem;color:#555'>
              ⏱ Time used: <b>{used}</b> / {total} min &nbsp;
              {'🔴' if pct > 0.85 else '🟡' if pct > 0.60 else '🟢'}
            </div>
            <div style='background:#e0e0e0;border-radius:8px;
                        height:12px;overflow:hidden;margin-bottom:12px'>
              <div style='background:{bar_color};width:{pct*100:.1f}%;
                          height:100%;border-radius:8px'></div>
            </div>""",
            unsafe_allow_html=True,
        )

        # ── Conflict warnings — shown ABOVE the schedule ──────────────────────
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.warning(
                f"**⚠️ {len(conflicts)} time overlap(s) detected** — "
                f"review before using this plan:"
            )
            for w in conflicts:
                st.warning(w.strip())

        # ── Skipped tasks ─────────────────────────────────────────────────────
        if scheduler.skipped:
            with st.expander(
                f"⏭ {len(scheduler.skipped)} task(s) skipped (not enough time)"
            ):
                rows = "".join(
                    f"<tr style='border-top:1px solid #e8e8e8'>"
                    f"<td style='padding:5px 10px'>"
                    f"{category_emoji(t.category)} {t.title}</td>"
                    f"<td style='padding:5px 10px;text-align:center'>"
                    f"{t.duration_minutes}</td>"
                    f"<td style='padding:5px 10px'>{priority_badge(t.priority)}</td>"
                    f"</tr>"
                    for t in scheduler.skipped
                )
                st.markdown(
                    f"""<table style='width:100%;border-collapse:collapse;
                        font-size:0.88rem'>
                      <thead><tr style='background:#f0f2f6'>
                        <th style='text-align:left;padding:6px 10px'>Task</th>
                        <th style='padding:6px 10px'>Duration (min)</th>
                        <th style='padding:6px 10px'>Priority</th>
                      </tr></thead>
                      <tbody>{rows}</tbody>
                    </table>""",
                    unsafe_allow_html=True,
                )

        # ── Schedule cards — apply pet filter and sort mode ───────────────────
        pet_filter = None if view_pet == "All pets" else view_pet
        filtered   = scheduler.filter_schedule(pet_name=pet_filter)

        display = scheduler.sort_by_time() if sort_mode == "Time" else filtered
        # Re-apply pet filter after sort_by_time() — it operates on the full schedule
        if sort_mode == "Time" and pet_filter:
            pet_task_ids = {
                id(t)
                for p in st.session_state.owner.pets if p.name == pet_filter
                for t in p.get_tasks()
            }
            display = [s for s in display if id(s.task) in pet_task_ids]

        if not display:
            st.info(f"No scheduled tasks for '{view_pet}'.")
        else:
            st.success(
                f"✅ Scheduled **{len(display)}** task(s) for "
                f"**{st.session_state.owner.name}**!"
            )

            # One styled card per scheduled task
            cards = ""
            for item in display:
                cat_em  = category_emoji(item.task.category)
                color   = _PRIORITY_COLOR.get(item.task.priority, "#888")
                pri_lbl = item.task.priority.upper()
                fq_em   = freq_emoji(item.task.frequency)
                cards += (
                    f"<div style='"
                    f"display:flex;align-items:center;gap:10px;"
                    f"padding:10px 14px;margin-bottom:8px;"
                    f"border-left:4px solid {color};"
                    f"background:#fafafa;border-radius:6px;"
                    f"font-size:0.88rem;'>"
                    f"<div style='color:#555;min-width:140px;font-family:monospace'>"
                    f"🕐 {item.start_time} – {item.end_time}</div>"
                    f"<div style='flex:1;font-weight:600'>{cat_em} {item.task.title}</div>"
                    f"<div style='min-width:52px;text-align:center;color:#555'>"
                    f"⏱ {item.task.duration_minutes}m</div>"
                    f"<div><span style='background:{color};color:#fff;"
                    f"padding:2px 8px;border-radius:12px;"
                    f"font-size:0.72rem;font-weight:700'>{pri_lbl}</span></div>"
                    f"<div style='min-width:72px;text-align:center;color:#666'>"
                    f"{fq_em} {item.task.frequency}</div>"
                    f"<div style='color:#999;font-size:0.78rem;flex:1;"
                    f"text-align:right;font-style:italic'>{item.reason}</div>"
                    f"</div>"
                )
            st.markdown(cards, unsafe_allow_html=True)
