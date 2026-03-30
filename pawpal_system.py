from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    category: str = "general"  # e.g. "walk", "feed", "meds", "groom"

    def is_high_priority(self) -> bool:
        pass

    def __repr__(self) -> str:
        pass


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: Dict = field(default_factory=dict)

    def set_available_time(self, minutes: int) -> None:
        pass

    def get_available_time(self) -> int:
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_time: str  # e.g. "8:00 AM"
    reason: str = ""

    def explain(self) -> str:
        pass


class Scheduler:
    def __init__(self, pet: Pet, owner: Owner):
        self.pet = pet
        self.owner = owner
        self.schedule: List[ScheduledTask] = []

    def build_schedule(self) -> List[ScheduledTask]:
        pass

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        pass

    def _fits_in_time(self, task: Task) -> bool:
        pass
