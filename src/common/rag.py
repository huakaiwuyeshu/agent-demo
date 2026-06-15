from __future__ import annotations

from .entities import Evidence
from .paths import DATA_DIR


DOC_FILES = ["api_docs.md", "error_codes.md"]


def search_knowledge(task_type: str, query: str, limit: int = 5) -> list[Evidence]:
    keywords = _keywords(task_type, query)
    scored: list[tuple[int, Evidence]] = []

    for file_name in DOC_FILES:
        path = DATA_DIR / file_name
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            normalized = line.lower()
            score = sum(1 for keyword in keywords if keyword.lower() in normalized)
            if score:
                scored.append((score, Evidence(file_name, line_no, line.strip())))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [evidence for _, evidence in scored[:limit]]


def format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "未找到可引用的文档依据。"
    return "\n".join(
        f"- {item.source}:{item.line_no} {item.text}" for item in evidence
    )


def _keywords(task_type: str, query: str) -> list[str]:
    if task_type == "signature_debug":
        return ["签名", "SIGN_INVALID", "参数排序", "UTF-8", "timestamp", "appsecret"]
    if task_type == "callback_debug":
        return ["回调", "CALLBACK_TIMEOUT", "HTTPS", "2xx"]
    if task_type == "api_field_qa":
        return ["字段", "appid", "order_id", "timestamp", "sign"]
    return [word for word in query.replace("，", " ").replace("。", " ").split() if word]
