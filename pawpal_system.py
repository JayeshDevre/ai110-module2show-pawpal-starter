from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations
from typing import List, Dict, Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
DAILY_FREQUENCIES = {"daily", "as-needed"}   # treated as always due today

# How many days until the next occurrence for each frequency
RECURRENCE_DAYS: Dict[str, Optional[int]] = {
    "daily":     1,
    "weekly":    7,
    "as-needed": None,   # no automatic recurrence
}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str              # "low", "medium", "high"
    category: str = "general"  # e.g. "walk", "feed", "meds", "groom"
    frequency: str = "daily"   # "daily", "weekly", "as-needed"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def is_due_today(self, already_done_titles: List[str]) -> bool:
        """
        Return True if this task should appear in today's schedule.
        - daily / as-needed: always due if not completed and due_date <= today
        - weekly: only due if it hasn't already been completed this cycle
        """
        if self.due_date > date.today():
            return False   # not yet due
        if self.frequency in DAILY_FREQUENCIES:
            return not self.completed
        if self.frequency == "weekly":
            return self.title not in already_done_titles
        return not self.completed

    def next_occurrence(self) -> Optional["Task"]:
        """Return a fresh Task scheduled for the next due date, or None for as-needed tasks.

        Uses timedelta to calculate the next date:
          daily  → today + timedelta(days=1)
          weekly → today + timedelta(days=7)
        The new instance starts incomplete and inherits all other attributes.
        """
        interval = RECURRENCE_DAYS.get(self.frequency)
        if interval is None:
            return None   # as-needed tasks don't auto-recur
        next_due = date.today() + timedelta(days=interval)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            completed=False,
            due_date=next_due,
        )

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        """Return a readable string representation of the task."""
        status = "done" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, due={self.due_date}, status={status})"
        )


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks (including completed) for this pet."""
        return self.tasks

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed."""
        return [t for t in self.tasks if not t.completed]

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task done and automatically add the next occurrence if the task recurs.

        Returns the new Task instance if one was created, or None for as-needed tasks.
        This keeps recurrence logic out of the UI — the caller just calls complete_task()
        and the pet's list stays up to date automatically.
        """
        task.mark_done()
        next_task = task.next_occurrence()   # timedelta-based, None for as-needed
        if next_task:
            self.tasks.append(next_task)
        return next_task

    def filter_tasks(
        self,
        status: Optional[str] = None,   # "pending" | "done"
        category: Optional[str] = None,
    ) -> List[Task]:
        """
        Return tasks filtered by optional status and/or category.
        status="pending" → incomplete tasks only
        status="done"    → completed tasks only
        category="walk"  → tasks matching that category
        """
        result = self.tasks
        if status == "pending":
            result = [t for t in result if not t.completed]
        elif status == "done":
            result = [t for t in result if t.completed]
        if category:
            result = [t for t in result if t.category == category]
        return result

    def __repr__(self) -> str:
        """Return a readable string representation of the pet."""
        return f"Pet(name='{self.name}', species='{self.species}', tasks={len(self.tasks)})"


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: Dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)
    completed_weekly_tasks: List[str] = field(default_factory=list)  # tracks weekly task titles done this cycle

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Update the owner's daily time budget in minutes."""
        self.available_minutes = minutes

    def get_available_time(self) -> int:
        """Return the owner's daily time budget in minutes."""
        return self.available_minutes

    def get_all_tasks(self) -> List[Task]:
        """Return all pending tasks across every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_pending_tasks())
        return all_tasks

    def filter_tasks_by_pet(self, pet_name: str) -> List[Task]:
        """Return all pending tasks belonging to the named pet."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.get_pending_tasks()
        return []

    def filter_tasks_by_status(self, status: str) -> List[Task]:
        """Return tasks across all pets matching 'pending' or 'done'."""
        result = []
        for pet in self.pets:
            result.extend(pet.filter_tasks(status=status))
        return result


@dataclass
class ScheduledTask:
    task: Task
    start_offset: int   # minutes from midnight — enables arithmetic for conflict detection
    end_offset: int     # start_offset + task.duration_minutes
    reason: str = ""

    @property
    def start_time(self) -> str:
        """Human-readable start time string."""
        return _minutes_to_time(self.start_offset)

    @property
    def end_time(self) -> str:
        """Human-readable end time string."""
        return _minutes_to_time(self.end_offset)

    def overlaps_with(self, other: "ScheduledTask") -> bool:
        """Return True if this scheduled task overlaps in time with another."""
        return self.start_offset < other.end_offset and self.end_offset > other.start_offset

    def explain(self) -> str:
        """Return a formatted string showing when and why this task was scheduled."""
        return (
            f"[{self.start_time} - {self.end_time}] {self.task.title} "
            f"({self.task.duration_minutes} min) — {self.reason}"
        )


def _minutes_to_time(total_minutes: int) -> str:
    """Convert an offset in minutes from midnight to a readable time string."""
    hours = total_minutes // 60
    mins = total_minutes % 60
    period = "AM" if hours < 12 else "PM"
    display_hour = hours if hours <= 12 else hours - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:{mins:02d} {period}"


class Scheduler:
    START_HOUR = 8  # schedule begins at 8:00 AM

    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: List[ScheduledTask] = []
        self.skipped: List[Task] = []           # tasks that didn't fit — conflict report
        self.remaining_minutes: int = owner.get_available_time()

    def build_schedule(self) -> List[ScheduledTask]:
        """
        Collect due tasks from all pets, sort by priority then duration (shorter first),
        greedily schedule tasks that fit the time budget, and record skipped tasks.
        """
        self.schedule = []
        self.skipped = []
        self.remaining_minutes = self.owner.get_available_time()

        tasks = self._get_due_tasks()
        sorted_tasks = self._sort_by_priority(tasks)

        current_offset = self.START_HOUR * 60  # minutes from midnight

        for task in sorted_tasks:
            if self._fits_in_time(task):
                end_offset = current_offset + task.duration_minutes
                reason = self._build_reason(task)
                self.schedule.append(
                    ScheduledTask(
                        task=task,
                        start_offset=current_offset,
                        end_offset=end_offset,
                        reason=reason,
                    )
                )
                current_offset = end_offset
                self.remaining_minutes -= task.duration_minutes

                # Mark weekly tasks as done so they aren't re-scheduled this cycle
                if task.frequency == "weekly":
                    self.owner.completed_weekly_tasks.append(task.title)
            else:
                self.skipped.append(task)   # conflict report — task didn't fit

        return self.schedule

    def _get_due_tasks(self) -> List[Task]:
        """Return only tasks that are due today, respecting recurrence rules."""
        due = []
        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if task.is_due_today(self.owner.completed_weekly_tasks):
                    due.append(task)
        return due

    def sort_by_time(self) -> List[ScheduledTask]:
        """Return the current schedule sorted by start_offset (earliest first).

        Uses a lambda key on the integer start_offset so the sort is exact arithmetic,
        not string comparison — e.g. 480 (8:00 AM) < 510 (8:30 AM) < 600 (10:00 AM).
        """
        return sorted(self.schedule, key=lambda st: st.start_offset)

    def filter_schedule(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,   # "pending" | "done"
    ) -> List[ScheduledTask]:
        """Return scheduled tasks filtered by pet name and/or task completion status.

        pet_name="Mochi"  → only tasks belonging to Mochi
        status="pending"  → only tasks not yet marked done
        status="done"     → only tasks already marked done
        Both filters can be combined.
        """
        result = self.schedule
        if pet_name:
            # Find which pet owns each scheduled task by checking the pet's task list
            pet_task_sets = {
                pet.name: {id(t) for t in pet.get_tasks()}
                for pet in self.owner.pets
            }
            result = [
                st for st in result
                if id(st.task) in pet_task_sets.get(pet_name, set())
            ]
        if status == "pending":
            result = [st for st in result if not st.task.completed]
        elif status == "done":
            result = [st for st in result if st.task.completed]
        return result

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks high → medium → low; within same priority, shorter tasks first."""
        return sorted(
            tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )

    def _fits_in_time(self, task: Task) -> bool:
        """Return True if the task duration fits within the remaining time budget."""
        return task.duration_minutes <= self.remaining_minutes

    def _build_reason(self, task: Task) -> str:
        """Generate a plain-English explanation for why this task was scheduled."""
        priority_label = f"{task.priority}-priority"
        freq_label = f"frequency: {task.frequency}"
        return f"Scheduled as {priority_label} task ({freq_label})"

    def force_add(self, task: Task, start_offset: int) -> ScheduledTask:
        """Manually place a task at a specific time offset (minutes from midnight).

        Bypasses the greedy algorithm — use this to inject tasks at fixed times
        or to deliberately create overlaps for testing conflict detection.
        Returns the ScheduledTask so the caller can inspect it.
        """
        end_offset = start_offset + task.duration_minutes
        st = ScheduledTask(
            task=task,
            start_offset=start_offset,
            end_offset=end_offset,
            reason="manually scheduled",
        )
        self.schedule.append(st)
        return st

    def detect_conflicts(self) -> List[str]:
        """Check every pair of scheduled tasks for time overlaps.

        Lightweight strategy: iterate all unique pairs using enumerate + slice,
        call overlaps_with() on each pair. Returns warning strings — never raises.
        An empty list means the schedule is conflict-free.
        """
        # combinations(schedule, 2) yields every unique pair (a, b) without repeats —
        # cleaner than a manual enumerate+slice and expresses intent directly.
        return [
            f"  WARNING: '{a.task.title}' [{a.start_time}-{a.end_time}] "
            f"overlaps with '{b.task.title}' [{b.start_time}-{b.end_time}]"
            for a, b in combinations(self.schedule, 2)
            if a.overlaps_with(b)
        ]

    def conflict_report(self) -> str:
        """Return a report of tasks that could not be scheduled due to time constraints."""
        if not self.skipped:
            return "All tasks fit within the available time."
        lines = [f"Skipped {len(self.skipped)} task(s) — not enough time:"]
        for t in self.skipped:
            lines.append(f"  - {t.title} ({t.duration_minutes} min, {t.priority} priority)")
        return "\n".join(lines)

    def summary(self) -> str:
        """Return a human-readable summary of the full schedule and any conflicts."""
        if not self.schedule:
            return "No tasks scheduled."
        lines = [f"Schedule for {self.owner.name}:"]
        for st in self.schedule:
            lines.append(f"  {st.explain()}")
        lines.append(
            f"  Time used: {self.owner.get_available_time() - self.remaining_minutes} min "
            f"/ {self.owner.get_available_time()} min available"
        )
        if self.skipped:
            lines.append(self.conflict_report())
        overlap_warnings = self.detect_conflicts()
        if overlap_warnings:
            lines.append("\nTime Overlap Warnings:")
            lines.extend(overlap_warnings)
        return "\n".join(lines)
