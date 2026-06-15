from __future__ import annotations

from .entities import TaskDraft, ValidationResult
from .schemas import field_label, task_label


def build_clarification(draft: TaskDraft, validation: ValidationResult) -> str:
    if validation.status == "blocked":
        return "这个请求触发了安全边界：" + "；".join(validation.blocked_reasons)

    if "task_type" in validation.missing_fields:
        return "我还不能判断这是哪类 API 接入问题。请补充：问题类型、相关接口、错误现象或错误码。"

    missing = "、".join(field_label(field) for field in validation.missing_fields)
    return (
        f"我已识别为「{task_label(draft.task_type)}」，但还缺少阻塞信息：{missing}。\n"
        "请补充这些信息后我再继续排查。不要发送 appsecret、密钥或完整敏感凭证。"
    )
