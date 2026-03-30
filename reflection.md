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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
