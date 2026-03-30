import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_task():
    return Task(title="Morning walk", duration_minutes=20, priority="high", category="walk")

@pytest.fixture
def sample_pet():
    return Pet(name="Mochi", species="dog")

@pytest.fixture
def owner_with_pets():
    mochi = Pet(name="Mochi", species="dog")
    luna  = Pet(name="Luna",  species="cat")
    mochi.add_task(Task("Walk",  20, "high", "walk"))
    mochi.add_task(Task("Feed",  10, "high", "feed"))
    luna.add_task( Task("Feed",   5, "high", "feed"))
    luna.add_task( Task("Play",  15, "low",  "enrichment"))
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


# ── Task: happy paths ──────────────────────────────────────────────────────────

def test_task_starts_incomplete(sample_task):
    """A newly created task should not be marked as completed."""
    assert sample_task.completed is False

def test_mark_done_changes_status(sample_task):
    """Calling mark_done() should set completed to True."""
    sample_task.mark_done()
    assert sample_task.completed is True

def test_is_high_priority_true(sample_task):
    """Task with priority='high' should return True from is_high_priority()."""
    assert sample_task.is_high_priority() is True

def test_is_high_priority_false():
    """Task with priority='low' should return False from is_high_priority()."""
    assert Task("Brushing", 15, "low", "groom").is_high_priority() is False


# ── Task: recurring tasks ──────────────────────────────────────────────────────

def test_daily_task_next_occurrence_due_tomorrow():
    """next_occurrence() for a daily task should set due_date to today + 1 day."""
    task = Task("Feed", 10, "high", frequency="daily")
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert nxt.completed is False

def test_weekly_task_next_occurrence_due_in_7_days():
    """next_occurrence() for a weekly task should set due_date to today + 7 days."""
    task = Task("Flea meds", 5, "high", frequency="weekly")
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == date.today() + timedelta(days=7)

def test_as_needed_task_has_no_next_occurrence():
    """next_occurrence() for an as-needed task should return None."""
    task = Task("Bath", 30, "medium", frequency="as-needed")
    assert task.next_occurrence() is None

def test_complete_task_marks_done_and_creates_next(sample_pet):
    """complete_task() should mark the task done and append the next occurrence."""
    task = Task("Walk", 20, "high", frequency="daily")
    sample_pet.add_task(task)
    nxt = sample_pet.complete_task(task)
    assert task.completed is True
    assert nxt is not None
    assert nxt in sample_pet.get_tasks()
    assert nxt.completed is False

def test_complete_as_needed_task_does_not_create_next(sample_pet):
    """complete_task() on an as-needed task should not add a new task."""
    task = Task("Bath", 30, "medium", frequency="as-needed")
    sample_pet.add_task(task)
    before_count = len(sample_pet.get_tasks())
    result = sample_pet.complete_task(task)
    assert result is None
    assert len(sample_pet.get_tasks()) == before_count   # no new task added

def test_future_due_date_task_excluded_from_schedule(sample_pet):
    """A task with a future due_date should not appear in today's schedule."""
    future_task = Task("Vet visit", 60, "high", due_date=date.today() + timedelta(days=3))
    sample_pet.add_task(future_task)
    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(sample_pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    scheduled_titles = [st.task.title for st in scheduler.schedule]
    assert "Vet visit" not in scheduled_titles


# ── Pet: happy paths ───────────────────────────────────────────────────────────

def test_add_task_increases_count(sample_pet, sample_task):
    """Adding a task to a Pet should increase its task count by 1."""
    assert len(sample_pet.get_tasks()) == 0
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == 1

def test_add_multiple_tasks(sample_pet):
    """Adding three tasks should result in a task count of 3."""
    for i in range(3):
        sample_pet.add_task(Task(f"Task {i}", 10, "low"))
    assert len(sample_pet.get_tasks()) == 3

def test_get_pending_tasks_excludes_completed(sample_pet):
    """Completed tasks should not appear in get_pending_tasks()."""
    done = Task("Old task", 5, "low")
    done.mark_done()
    pending = Task("New task", 10, "high")
    sample_pet.add_task(done)
    sample_pet.add_task(pending)
    result = sample_pet.get_pending_tasks()
    assert len(result) == 1
    assert result[0].title == "New task"


# ── Pet: edge cases ────────────────────────────────────────────────────────────

def test_pet_with_no_tasks_has_empty_pending(sample_pet):
    """A pet with no tasks should return an empty pending list."""
    assert sample_pet.get_pending_tasks() == []

def test_filter_tasks_by_category(sample_pet):
    """filter_tasks(category='walk') should return only walk tasks."""
    sample_pet.add_task(Task("Walk",   20, "high", category="walk"))
    sample_pet.add_task(Task("Groom",  15, "medium", category="groom"))
    result = sample_pet.filter_tasks(category="walk")
    assert len(result) == 1
    assert result[0].category == "walk"

def test_filter_tasks_by_status_done(sample_pet):
    """filter_tasks(status='done') should return only completed tasks."""
    t1 = Task("Walk",  20, "high")
    t2 = Task("Groom", 15, "medium")
    t1.mark_done()
    sample_pet.add_task(t1)
    sample_pet.add_task(t2)
    result = sample_pet.filter_tasks(status="done")
    assert len(result) == 1
    assert result[0].title == "Walk"


# ── Owner tests ────────────────────────────────────────────────────────────────

def test_owner_get_all_tasks_across_pets(owner_with_pets):
    """get_all_tasks() should return tasks from all pets combined."""
    assert len(owner_with_pets.get_all_tasks()) == 4

def test_set_available_time(owner_with_pets):
    """set_available_time() should update the owner's time budget."""
    owner_with_pets.set_available_time(45)
    assert owner_with_pets.get_available_time() == 45

def test_owner_with_no_pets_returns_no_tasks():
    """An owner with no pets should return an empty task list."""
    owner = Owner(name="Alex", available_minutes=60)
    assert owner.get_all_tasks() == []


# ── Scheduler: happy paths ─────────────────────────────────────────────────────

def test_scheduler_respects_time_budget(owner_with_pets):
    """Scheduler should never exceed the owner's available_minutes."""
    owner_with_pets.set_available_time(25)
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    used = sum(st.task.duration_minutes for st in scheduler.schedule)
    assert used <= 25

def test_scheduler_orders_high_priority_first(owner_with_pets):
    """The first scheduled task should be a high-priority task."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    assert scheduler.schedule[0].task.priority == "high"

def test_scheduler_empty_when_no_time(owner_with_pets):
    """With 0 available minutes, no tasks should be scheduled."""
    owner_with_pets.set_available_time(0)
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    assert len(scheduler.schedule) == 0

def test_task_exactly_fills_budget_gets_scheduled(sample_pet):
    """A task whose duration exactly equals remaining_minutes should be scheduled."""
    sample_pet.add_task(Task("Exact fit", 30, "high"))
    owner = Owner(name="Jordan", available_minutes=30)
    owner.add_pet(sample_pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert len(scheduler.schedule) == 1
    assert scheduler.schedule[0].task.title == "Exact fit"


# ── Scheduler: edge cases ──────────────────────────────────────────────────────

def test_scheduler_with_no_pets_produces_empty_schedule():
    """An owner with no pets should produce an empty schedule."""
    owner = Owner(name="Alex", available_minutes=60)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert scheduler.schedule == []

def test_scheduler_with_pet_with_no_tasks_produces_empty_schedule(sample_pet):
    """A pet with no tasks should result in an empty schedule."""
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(sample_pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert scheduler.schedule == []

def test_skipped_tasks_tracked_when_over_budget(sample_pet):
    """Tasks that don't fit should appear in scheduler.skipped."""
    sample_pet.add_task(Task("Big task", 50, "high"))
    sample_pet.add_task(Task("Small task", 10, "low"))
    owner = Owner(name="Jordan", available_minutes=15)
    owner.add_pet(sample_pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert len(scheduler.skipped) > 0

def test_shorter_task_scheduled_before_longer_same_priority(sample_pet):
    """Within the same priority, shorter tasks should be scheduled first."""
    sample_pet.add_task(Task("Long high",  30, "high"))
    sample_pet.add_task(Task("Short high", 10, "high"))
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(sample_pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert scheduler.schedule[0].task.title == "Short high"


# ── Scheduler: sort_by_time ────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order(owner_with_pets):
    """sort_by_time() should return tasks ordered earliest start_offset first."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    sorted_schedule = scheduler.sort_by_time()
    offsets = [st.start_offset for st in sorted_schedule]
    assert offsets == sorted(offsets)

def test_sort_by_time_empty_schedule_returns_empty_list():
    """sort_by_time() on an empty schedule should return []."""
    owner = Owner(name="Alex", available_minutes=60)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    assert scheduler.sort_by_time() == []


# ── Scheduler: filter_schedule ────────────────────────────────────────────────

def test_filter_schedule_by_pet_name(owner_with_pets):
    """filter_schedule(pet_name='Mochi') should return only Mochi's tasks."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    mochi_tasks = scheduler.filter_schedule(pet_name="Mochi")
    mochi_pet = next(p for p in owner_with_pets.pets if p.name == "Mochi")
    mochi_task_ids = {id(t) for t in mochi_pet.get_tasks()}
    assert all(id(st.task) in mochi_task_ids for st in mochi_tasks)

def test_filter_schedule_by_status_done(owner_with_pets):
    """filter_schedule(status='done') should return only completed scheduled tasks."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    scheduler.schedule[0].task.mark_done()
    done = scheduler.filter_schedule(status="done")
    assert len(done) == 1
    assert done[0].task.completed is True

def test_filter_schedule_by_status_pending(owner_with_pets):
    """filter_schedule(status='pending') should exclude completed tasks."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    scheduler.schedule[0].task.mark_done()
    pending = scheduler.filter_schedule(status="pending")
    assert all(not st.task.completed for st in pending)

def test_filter_schedule_unknown_pet_returns_empty(owner_with_pets):
    """filter_schedule with a non-existent pet name should return []."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    result = scheduler.filter_schedule(pet_name="Ghost")
    assert result == []


# ── Scheduler: conflict detection ─────────────────────────────────────────────

def test_detect_conflicts_clean_schedule_returns_empty(owner_with_pets):
    """A normally built schedule should have zero time conflicts."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    assert scheduler.detect_conflicts() == []

def test_detect_conflicts_finds_overlapping_tasks(owner_with_pets):
    """force_add at an occupied time slot should trigger a conflict warning."""
    scheduler = Scheduler(owner=owner_with_pets)
    scheduler.build_schedule()
    clash = Task("Vet call", 15, "high")
    scheduler.force_add(clash, start_offset=8 * 60)   # same start as first task
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) > 0
    assert "WARNING" in conflicts[0]

def test_detect_conflicts_no_false_positives():
    """Adjacent tasks (one ends exactly when next starts) should NOT be flagged."""
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Task A", 20, "high"))
    pet.add_task(Task("Task B", 10, "high"))
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    scheduler.build_schedule()
    # sequential schedule has no overlaps
    assert scheduler.detect_conflicts() == []
