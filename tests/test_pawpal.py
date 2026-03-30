import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

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
    mochi.add_task(Task("Walk",    20, "high",   "walk"))
    mochi.add_task(Task("Feed",    10, "high",   "feed"))
    luna.add_task( Task("Feed",     5, "high",   "feed"))
    luna.add_task( Task("Play",    15, "low",    "enrichment"))
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


# ── Task tests ─────────────────────────────────────────────────────────────────

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
    task = Task("Brushing", 15, "low", "groom")
    assert task.is_high_priority() is False


# ── Pet tests ──────────────────────────────────────────────────────────────────

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
    done_task = Task("Old task", 5, "low")
    done_task.mark_done()
    pending_task = Task("New task", 10, "high")
    sample_pet.add_task(done_task)
    sample_pet.add_task(pending_task)
    pending = sample_pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "New task"


# ── Owner tests ────────────────────────────────────────────────────────────────

def test_owner_get_all_tasks_across_pets(owner_with_pets):
    """get_all_tasks() should return tasks from all pets combined."""
    all_tasks = owner_with_pets.get_all_tasks()
    assert len(all_tasks) == 4

def test_set_available_time(owner_with_pets):
    """set_available_time() should update the owner's time budget."""
    owner_with_pets.set_available_time(45)
    assert owner_with_pets.get_available_time() == 45


# ── Scheduler tests ────────────────────────────────────────────────────────────

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
