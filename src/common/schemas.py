from __future__ import annotations


FIELD_LABELS: dict[str, str] = {
    "api_path": "接口路径",
    "appid": "appid",
    "raw_sign_string": "签名前原始字符串",
    "error_code": "错误码",
    "request_time": "请求时间",
    "callback_url": "回调地址",
    "order_id": "订单号",
    "trigger_action": "触发动作",
    "field_name": "字段名",
}


TASK_SCHEMAS: dict[str, dict[str, object]] = {
    "signature_debug": {
        "label": "签名失败排查",
        "required_fields": [
            "api_path",
            "appid",
            "raw_sign_string",
            "error_code",
            "request_time",
        ],
        "skill": "signature_debug",
    },
    "callback_debug": {
        "label": "回调异常排查",
        "required_fields": [
            "callback_url",
            "order_id",
            "trigger_action",
            "request_time",
        ],
        "skill": "callback_debug",
    },
    "api_field_qa": {
        "label": "API 字段问答",
        "required_fields": ["field_name"],
        "skill": "api_field_qa",
    },
    "credential_request": {
        "label": "凭证相关请求",
        "required_fields": ["appid"],
        "skill": None,
        "requires_human_review": True,
    },
    "unknown": {
        "label": "未识别任务",
        "required_fields": [],
        "skill": None,
    },
}


def task_label(task_type: str) -> str:
    return str(TASK_SCHEMAS.get(task_type, TASK_SCHEMAS["unknown"])["label"])


def required_fields(task_type: str) -> list[str]:
    schema = TASK_SCHEMAS.get(task_type, TASK_SCHEMAS["unknown"])
    return list(schema.get("required_fields", []))


def skill_name(task_type: str) -> str | None:
    schema = TASK_SCHEMAS.get(task_type, TASK_SCHEMAS["unknown"])
    skill = schema.get("skill")
    return str(skill) if skill else None


def requires_human_review(task_type: str) -> bool:
    schema = TASK_SCHEMAS.get(task_type, TASK_SCHEMAS["unknown"])
    return bool(schema.get("requires_human_review", False))


def field_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name)
