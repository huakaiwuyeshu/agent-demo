from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class TaskState:
    task_type: str
    status: str = "created"
    task_id: str = field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    completed_steps: list[str] = field(default_factory=list)
    pending_fields: list[str] = field(default_factory=list)
    next_action: str | None = None

    def mark(self, step: str) -> None:
        self.completed_steps.append(step)

    def wait_for_fields(self, fields: list[str]) -> None:
        self.status = "waiting_for_user"
        self.pending_fields = fields
        self.next_action = "clarify"

    def ready_to_execute(self) -> None:
        self.status = "ready_to_execute"
        self.pending_fields = []
        self.next_action = "run_skill_and_tools"

    def finished(self) -> None:
        self.status = "finished"
        self.next_action = None

    def blocked(self, reason: str) -> None:
        self.status = "blocked"
        self.next_action = reason
