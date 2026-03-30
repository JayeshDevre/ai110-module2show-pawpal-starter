from dataclasses import dataclass, field
from typing import List, Dict


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    category: str = "general"  # e.g. "walk", "feed", "meds", "groom"
    frequency: str = "daily"   # "daily", "weekly", "as-needed"
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        """Return a readable string representation of the task."""
        status = "done" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, status={status})"
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

    def __repr__(self) -> str:
        """Return a readable string representation of the pet."""
        return f"Pet(name='{self.name}', species='{self.species}', tasks={len(self.tasks)})"


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: Dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

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


@dataclass
class ScheduledTask:
    task: Task
    start_time: str   # e.g. "8:00 AM"
    end_time: str     # e.g. "8:20 AM"
    reason: str = ""

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
        self.remaining_minutes: int = owner.get_available_time()

    def build_schedule(self) -> List[ScheduledTask]:
        """
        Retrieve all pending tasks from all pets, sort by priority,
        then greedily add tasks that fit within the owner's time budget.
        """
        self.schedule = []
        self.remaining_minutes = self.owner.get_available_time()

        tasks = self.owner.get_all_tasks()
        sorted_tasks = self._sort_by_priority(tasks)

        current_offset = self.START_HOUR * 60  # minutes from midnight

        for task in sorted_tasks:
            if self._fits_in_time(task):
                start = _minutes_to_time(current_offset)
                end = _minutes_to_time(current_offset + task.duration_minutes)
                reason = self._build_reason(task)

                self.schedule.append(
                    ScheduledTask(task=task, start_time=start, end_time=end, reason=reason)
                )
                current_offset += task.duration_minutes
                self.remaining_minutes -= task.duration_minutes

        return self.schedule

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks high → medium → low."""
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def _fits_in_time(self, task: Task) -> bool:
        """Return True if the task duration fits within the remaining time budget."""
        return task.duration_minutes <= self.remaining_minutes

    def _build_reason(self, task: Task) -> str:
        """Generate a plain-English explanation for why this task was scheduled."""
        priority_label = f"{task.priority}-priority"
        freq_label = f"frequency: {task.frequency}"
        return f"Scheduled as {priority_label} task ({freq_label})"

    def summary(self) -> str:
        """Return a human-readable summary of the full schedule."""
        if not self.schedule:
            return "No tasks scheduled."
        lines = [f"Schedule for {self.owner.name}:"]
        for st in self.schedule:
            lines.append(f"  {st.explain()}")
        lines.append(
            f"  Time used: {self.owner.get_available_time() - self.remaining_minutes} min "
            f"/ {self.owner.get_available_time()} min available"
        )
        return "\n".join(lines)
