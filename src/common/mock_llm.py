from __future__ import annotations

import re
from typing import Any

from .entities import TaskDraft


def direct_chat_answer(message: str) -> str:
    return (
        "可以先从常见原因排查：参数排序是否正确、签名前字符串是否一致、"
        "编码是否为 UTF-8、timestamp 是否过期、appid 是否和环境匹配。"
        "如果仍然失败，请提供接口路径、appid、错误码、请求时间和签名前原始字符串。"
    )


def extract_task(message: str) -> TaskDraft:
    task_type = _detect_task_type(message)
    fields = _empty_fields()

    fields["api_path"] = _first_match(r"(/[A-Za-z0-9_\-/]+)", message)
    fields["appid"] = _first_match(r"(?:appid|app_id)\s*[=:：]\s*([A-Za-z0-9_\-]+)", message)
    fields["error_code"] = _first_match(r"(?:错误码|error_code)\s*[=:：]\s*([A-Z0-9_\-]+)", message)
    fields["request_time"] = _first_match(
        r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)",
        message,
    )
    fields["raw_sign_string"] = _first_match(
        r"(?:签名前字符串|签名原文|raw_sign_string)\s*[=:：]?\s*([^，。\n]+)",
        message,
    )
    fields["callback_url"] = _first_match(r"(https://[A-Za-z0-9_\-./?=&%]+)", message)
    fields["order_id"] = _first_match(r"(?:order_id|订单号)\s*[=:：]\s*([A-Za-z0-9_\-]+)", message)
    fields["field_name"] = _detect_field_name(message)

    security_flags: list[str] = []
    if re.search(r"appsecret\s*[=:：]\s*\S+", message, flags=re.IGNORECASE):
        security_flags.append("contains_appsecret")
    elif "appsecret" in message.lower():
        security_flags.append("mentions_appsecret")

    confidence = 0.86 if task_type != "unknown" else 0.32
    return TaskDraft(
        task_type=task_type,
        fields=fields,
        confidence=confidence,
        raw_message=message,
        security_flags=security_flags,
    )


def _detect_task_type(message: str) -> str:
    lowered = message.lower()
    if "签名" in message or "sign_invalid" in lowered or "验签" in message:
        return "signature_debug"
    if "回调" in message or "callback" in lowered:
        return "callback_debug"
    if "字段" in message or "什么意思" in message:
        return "api_field_qa"
    if "appid" in lowered and "appsecret" in lowered:
        return "credential_request"
    return "unknown"


def _empty_fields() -> dict[str, Any]:
    return {
        "api_path": None,
        "appid": None,
        "raw_sign_string": None,
        "error_code": None,
        "request_time": None,
        "callback_url": None,
        "order_id": None,
        "trigger_action": None,
        "field_name": None,
    }


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _detect_field_name(message: str) -> str | None:
    for field in ["appid", "order_id", "timestamp", "sign", "appsecret"]:
        if field in message.lower():
            return field
    return None
