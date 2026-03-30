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

## Smarter Scheduling

Beyond the basic greedy planner, the system implements four additional features:

### Sorting by time
`Scheduler.sort_by_time()` returns the schedule ordered chronologically using integer minute offsets as the sort key — exact arithmetic rather than fragile string comparison.

### Filtering
Tasks can be sliced by pet, category, or completion status at multiple levels:
- `Pet.filter_tasks(status, category)` — filters one pet's tasks
- `Owner.filter_tasks_by_pet(name)` / `Owner.filter_tasks_by_status(status)` — cross-pet filters
- `Scheduler.filter_schedule(pet_name, status)` — filters the live schedule

### Recurring tasks
`Task.next_occurrence()` uses Python's `timedelta` to calculate the next due date:
- `daily` → today + 1 day
- `weekly` → today + 7 days
- `as-needed` → no recurrence (returns `None`)

Calling `Pet.complete_task(task)` marks the task done and automatically appends the next occurrence to the pet's task list.

### Conflict detection
`Scheduler.detect_conflicts()` checks every unique pair of scheduled tasks using `itertools.combinations` and `ScheduledTask.overlaps_with()`. It returns a list of warning strings — never raises — so the app continues running even if the schedule has overlaps.

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

36 tests across 5 areas:

| Area | Tests | What's verified |
|---|---|---|
| **Task** | 6 | Completion status, priority flag, recurrence (`daily`/`weekly`/`as-needed`), future `due_date` excluded |
| **Pet** | 6 | Add/get tasks, pending filter, `complete_task()` auto-recurrence, category + status filtering |
| **Owner** | 3 | Cross-pet task collection, time budget update, no-pets edge case |
| **Scheduler — core** | 7 | Priority ordering, time budget enforcement, skipped task tracking, shorter-first tie-breaking, empty schedule edge cases |
| **Scheduler — advanced** | 14 | `sort_by_time()` chronological order, `filter_schedule()` by pet/status, `detect_conflicts()` overlap detection and false-positive prevention |

### Confidence level

★★★★☆ (4/5)

The core scheduling behaviors (priority ordering, time budget, recurrence, conflict detection) are fully covered by automated tests and all pass. One star is withheld because the `app.py` UI layer has no automated tests — Streamlit interactions would require browser-level testing tools beyond the current scope.

---

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
