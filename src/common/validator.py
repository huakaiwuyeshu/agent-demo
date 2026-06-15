from __future__ import annotations

from .entities import TaskDraft, ValidationResult
from .schemas import required_fields


def validate_task(draft: TaskDraft) -> ValidationResult:
    if "contains_appsecret" in draft.security_flags:
        return ValidationResult(
            status="blocked",
            blocked_reasons=["用户输入中包含 appsecret，不能进入普通模型上下文或普通日志。"],
        )

    if draft.task_type == "unknown":
        return ValidationResult(
            status="needs_clarification",
            missing_fields=["task_type"],
        )

    missing = [field for field in required_fields(draft.task_type) if not draft.fields.get(field)]
    if missing:
        return ValidationResult(status="needs_clarification", missing_fields=missing)

    return ValidationResult(status="executable")
