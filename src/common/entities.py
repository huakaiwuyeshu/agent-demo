from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    message: str
    notes: str

    def with_message(self, message: str) -> "Scenario":
        return Scenario(
            name=self.name,
            title=f"{self.title}（自定义输入）",
            message=message,
            notes=self.notes,
        )


@dataclass
class TaskDraft:
    task_type: str
    fields: dict[str, Any]
    confidence: float
    raw_message: str
    security_flags: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    status: str
    missing_fields: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)

    @property
    def executable(self) -> bool:
        return self.status == "executable"


@dataclass
class Step:
    title: str
    content: str


@dataclass
class RunResult:
    version: str
    name: str
    added_capability: str
    scenario: Scenario
    steps: list[Step]
    final_output: str
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    source: str
    line_no: int
    text: str


@dataclass
class ToolResult:
    name: str
    status: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)
