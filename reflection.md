# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML included five classes:

- **Task** — holds a single care activity (title, duration, priority, category). Responsible for knowing whether it is high-priority via `is_high_priority()`.
- **Pet** — represents the animal being cared for (name, species). Owns a list of `Task` objects and exposes `add_task()` / `get_tasks()` so the rest of the system doesn't touch the list directly.
- **Owner** — represents the person managing care (name, available time budget in minutes, preferences dict). Responsible for tracking and exposing the daily time constraint.
- **ScheduledTask** — a wrapper around `Task` that adds placement info (start time, reason). Responsible for explaining why and when a task was scheduled via `explain()`.
- **Scheduler** — the engine. Takes a `Pet` and `Owner`, reads tasks and constraints, and produces an ordered list of `ScheduledTask` objects via `build_schedule()`. Private helpers `_sort_by_priority()` and `_fits_in_time()` handle the two core decisions.

**b. Design changes**

After reviewing the skeleton for missing relationships and logic bottlenecks, two changes were made:

1. **Added `end_time` to `ScheduledTask`** — The original design only stored `start_time`. Without `end_time`, the scheduler has no way to detect overlapping tasks or display a proper timeline. `end_time` can be computed as `start_time + task.duration_minutes` and is essential for conflict detection.

2. **Added `remaining_minutes` to `Scheduler`** — The `_fits_in_time()` method existed but had nothing to check against at runtime. Without a mutable counter tracking how much of the owner's time budget has been consumed, the method can never work correctly. `remaining_minutes` is initialized from `owner.available_minutes` and decremented as tasks are scheduled.

One unused import (`Optional`) was also removed to keep the file clean.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints:

1. **Time budget** (`owner.available_minutes`) — no task is added if it would exceed the remaining minutes. This is a hard constraint; the scheduler never overbooks.
2. **Task priority** (`high → medium → low`) — tasks are sorted before scheduling so high-priority tasks are always placed first. Within the same priority level, shorter tasks go first so more tasks fit within the budget.

`due_date` acts as a third, implicit constraint: tasks with a future `due_date` are excluded from today's schedule entirely, regardless of priority.

Time budget was treated as the most important constraint because exceeding a pet owner's available time makes the plan useless in practice. Priority determines *which* tasks get the limited slots.

**b. Tradeoffs**

The scheduler uses a **greedy algorithm**: it sorts tasks by priority + duration, then adds each task if it fits — never backtracking.

**Tradeoff:** A single large high-priority task (e.g., a 60-minute vet visit) will consume most of the time budget and block several shorter medium- or low-priority tasks that together would have been more useful. The scheduler never asks "what combination of tasks produces the best outcome?" — it just takes the first thing that fits.

**Why it's reasonable here:** For a daily pet care scenario, the tasks are typically short (5–30 min), the number of tasks is small (< 20), and owners generally agree that high-priority tasks *should* run first. A globally optimal knapsack solution would be harder to explain to a user and adds complexity that isn't needed at this scale. The greedy approach is transparent, fast, and predictable.

---

## 3. AI Collaboration

**a. How you used AI**

I used VS Code Copilot across every phase of the project, but I was deliberate about *what* I asked it to do at each stage:

- **Design brainstorming (Chat — early phase):** I described the pet care scenario in plain English and asked Copilot to suggest classes, attributes, and relationships. This gave me a starting list of candidates faster than staring at a blank page. I then filtered and restructured those suggestions before putting anything into the UML. The most effective prompts were specific and bounded — for example: *"Given a Task class with a duration and priority, what private helpers would a Scheduler need to place tasks without exceeding a time budget?"* Open-ended prompts like *"design a scheduler"* produced bloated suggestions I had to cut down.

- **Implementation (Agent Mode — middle phase):** Once the UML was locked, I used Agent Mode to flesh out method bodies from docstrings. This worked best when I had already written the method signature and a one-line docstring, because Copilot filled in the body without drifting from the intended design. Asking it to implement a whole class from scratch often produced code that was technically correct but didn't match the architecture (e.g., it kept suggesting the Scheduler take a single `Pet` argument instead of an `Owner`).

- **Conflict detection simplification (Chat — algorithm phase):** After writing the nested-loop version of `detect_conflicts()`, I pasted the method and asked: *"How could this be simplified using Python standard library tools?"* Copilot suggested `itertools.combinations`, which collapsed a 10-line double loop into a single clean `for a, b in combinations(self.schedule, 2)` line. This was the most impactful single suggestion of the project.

- **Test scaffolding (Chat — testing phase):** I described the behavior I wanted to test in plain language (*"a task with a future due_date should not appear in today's schedule"*) and asked Copilot to write the pytest fixture and assertion. It generated correct test bodies about 80% of the time; the other 20% needed a fix to match the actual method signatures.

**b. Judgment and verification**

The clearest moment where I rejected an AI suggestion involved time representation. When I asked Copilot to help implement `ScheduledTask`, it stored `start_time` and `end_time` as formatted strings like `"8:00 AM"`. That looks fine in the UI, but I immediately saw the problem: you cannot do arithmetic on strings. Sorting by time, computing overlaps, and detecting conflicts all require numeric comparisons.

I rejected the string approach and redesigned `ScheduledTask` to store `start_offset` and `end_offset` as plain integers (minutes from midnight). I added `@property` methods that convert to display strings only when needed for the UI. The overlap check then became a simple integer comparison: `self.start_offset < other.end_offset and other.start_offset < self.end_offset`. I verified the fix by running the `test_detect_conflicts_no_false_positives` test, which confirms adjacent tasks are not wrongly flagged, and `test_sort_by_time_returns_chronological_order`, which confirms integer-sort order is correct.

The general verification strategy was: write the test first that would catch the bug, then confirm the redesign makes the test pass.

**c. Separate sessions for different phases**

Using separate Copilot chat sessions for design, implementation, and testing made a real difference. Each session had a narrow, fresh context — the design session contained only the UML, the implementation session contained only the class stubs. This prevented Copilot from mixing concerns: it never tried to "fix" a test by changing the production class, because the production file wasn't in context. It also forced me to re-state the intent at the start of each session, which doubled as a self-check that I still understood the plan.

**d. Being the lead architect**

The most important lesson was that AI is a fast executor, not a good decision-maker. Copilot could produce a working scheduler in minutes, but "working" meant *passing whatever tests it wrote for itself* — not necessarily matching the design I had in my UML or the constraints the scenario required. Every time I let Copilot make a structural decision (how many constructor arguments, where to store time, which class owns a responsibility), I had to refactor later.

The workflow that worked: I made every architectural decision myself (what the class diagram looks like, what each method is responsible for, what the data types are), then used Copilot only to fill in the bodies. As lead architect, my job was to keep the system coherent across files and phases. Copilot's job was to save me from typing boilerplate.

---

## 4. Testing and Verification

**a. What you tested**

The 36-test suite covers five behavioral areas:

1. **Task lifecycle** — A new task starts incomplete; `mark_done()` flips it; `is_high_priority()` reflects the priority string correctly. These tests matter because the entire scheduler depends on the `completed` flag being reliable.

2. **Recurring task logic** — `next_occurrence()` must return `due_date = today + 1` for daily, `today + 7` for weekly, and `None` for as-needed. A bug here silently creates tasks with wrong dates that would appear (or not appear) on the wrong day. I also tested that `complete_task()` atomically marks the current task done *and* appends the next occurrence — the two operations must happen together or the recurrence chain breaks.

3. **Scheduling correctness** — The scheduler must always respect the time budget (never exceed `available_minutes`), always place high-priority tasks before low-priority ones, break ties by duration (shorter first), and track skipped tasks. These are the core promises of the greedy algorithm; any regression here makes the schedule meaningless.

4. **Edge cases** — Zero available minutes produces an empty schedule; a pet with no tasks produces an empty schedule; a task whose duration exactly equals the remaining budget is scheduled (not skipped). Edge cases are important because they are the most likely source of silent failures — the app would appear to work but produce wrong output in unusual but real situations.

5. **Conflict detection correctness** — A normally built sequential schedule must return zero conflicts (no false positives); `force_add` at an occupied slot must produce at least one warning (true positive). Testing both directions prevents a bug where `detect_conflicts()` always returns empty (or always returns warnings), which would make it useless.

**b. Confidence**

Confidence level: **★★★★☆ (4/5)**.

I am confident the scheduling engine is correct for the scenarios covered by the tests. The greedy algorithm, time budget enforcement, recurrence chain, and conflict detection all have direct test coverage and pass consistently.

One star is withheld for two reasons: (1) the `app.py` UI layer has no automated tests — session state mutations, button interactions, and filter/sort combinations are untested; (2) multi-pet edge cases where two pets share a task title could confuse the `completed_weekly_tasks` deduplication logic, but no test currently exercises that scenario.

Next tests I would add with more time:
- Two pets with a task of the same title — verify weekly deduplication doesn't cross-contaminate pets.
- `force_add` with a start offset that makes a task extend past midnight — verify `end_offset` wrapping doesn't break `overlaps_with()`.
- `filter_schedule(pet_name=..., status=...)` with both filters active simultaneously.
- A schedule where every task is skipped — verify `scheduler.schedule` is empty and `scheduler.skipped` contains all tasks.

---

## 5. Reflection

**a. What went well**

The part I am most satisfied with is the time representation decision. Switching from string times to integer minute offsets (`start_offset`, `end_offset`) was a small change in the data model but it unlocked three features cleanly: exact-arithmetic conflict detection, integer-sort chronological ordering, and a trivially correct `overlaps_with()` predicate. The `@property` pattern kept the display layer clean without leaking the implementation. In hindsight it is the right design, and I am glad I caught the string-time issue before writing tests against it.

**b. What you would improve**

If I had another iteration, I would redesign the `Owner.completed_weekly_tasks` list. The current approach tracks completed weekly task *titles* as strings, which means two pets with a task named "Feed" would incorrectly share the same deduplication record. A better design would key the record on `(pet_name, task_title)` tuples, or move the completion tracking into the `Pet` or `Task` object itself so each instance has its own state. I would also add a proper `run_app.sh` script and environment validation so the app fails loudly if dependencies are missing rather than crashing inside Streamlit with an import error.

**c. Key takeaway**

The most important thing I learned is that **a design diagram is a contract, not a suggestion**. Every time I let Copilot drift from the UML — changing constructor signatures, adding attributes that belonged to a different class, returning different types than specified — I paid for it later with debugging or refactoring time. The UML was not bureaucracy; it was the single source of truth that kept five classes coherent across a multi-hour build. Keeping it updated as the design evolved (especially adding `end_offset` and `remaining_minutes`) meant the code and the diagram stayed in sync, and I always knew exactly what each class was supposed to do. The lead architect's job is to maintain that contract, and no AI tool can do that for you.
