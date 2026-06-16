from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError
from urllib.request import urlopen

from .entities import Evidence
from .paths import KNOWLEDGE_DIR, LLM_WIKI_API_INFRA_DIR, REMOTE_LLM_WIKI_SEARCH_INDEX_URL


KNOWLEDGE_FILES = ("api_docs.json", "faq.json", "error_codes.json", "sops.json")
WIKI_FALLBACK_GLOBS = ("wiki/**/*.md", "sources/extracted-md/*.md")


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    line_no: int
    title: str
    text: str
    category: str = "knowledge"


def search_knowledge(task_type: str, query: str, limit: int = 5) -> list[Evidence]:
    """Search the exported demo knowledge first, then fall back to llm-wiki."""
    keywords = _keywords(task_type, query)
    local_hits = _rank(_load_exported_knowledge(), keywords, limit)
    if local_hits:
        return local_hits

    fallback_hits = _rank(_load_llm_wiki_fallback(), keywords, limit)
    if fallback_hits:
        return fallback_hits

    remote_hits = _rank(_load_remote_llm_wiki_index(), keywords, limit)
    if remote_hits:
        return remote_hits

    return []


def format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return (
            "未在当前 demo 知识包命中依据；本地 llm-wiki 和远程 llm-wiki "
            "兜底也未命中或不可用。请确认 API 文档已整理并导出。"
        )
    return "\n".join(
        f"- {item.source}:{item.line_no} {item.text}" for item in evidence
    )


def _rank(chunks: Iterable[KnowledgeChunk], keywords: list[str], limit: int) -> list[Evidence]:
    scored: list[tuple[int, Evidence]] = []
    for chunk in chunks:
        haystack = f"{chunk.title}\n{chunk.text}\n{chunk.source}".lower()
        score = 0
        for keyword in keywords:
            normalized = keyword.lower().strip()
            if not normalized:
                continue
            if normalized in haystack:
                score += 2 if normalized in chunk.title.lower() else 1
        if score:
            text = f"{chunk.title}：{chunk.text}" if chunk.title else chunk.text
            scored.append((score, Evidence(chunk.source, chunk.line_no, _compact(text))))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [evidence for _, evidence in scored[:limit]]


def _load_exported_knowledge() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    if not KNOWLEDGE_DIR.exists():
        return chunks

    for file_name in KNOWLEDGE_FILES:
        path = KNOWLEDGE_DIR / file_name
        if not path.exists():
            continue
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue
            chunks.append(_record_to_chunk(file_name, index, record))

    return chunks


def _record_to_chunk(file_name: str, index: int, record: dict[str, Any]) -> KnowledgeChunk:
    source_ref = record.get("source") or file_name
    item_id = record.get("id") or record.get("code") or index
    source = f"knowledge/{file_name}#{item_id} ({source_ref})"

    if file_name == "faq.json":
        title = str(record.get("question") or "FAQ")
        text = str(record.get("answer") or "")
        category = "faq"
    elif file_name == "error_codes.json":
        title = f"错误码 {record.get('code', '')}".strip()
        text = "；".join(
            str(part)
            for part in (record.get("meaning"), record.get("suggestion"))
            if part
        )
        category = "error_code"
    elif file_name == "sops.json":
        title = str(record.get("title") or record.get("id") or "SOP")
        text = "；".join(
            part
            for part in (
                _join_values("适用场景", record.get("applies_to")),
                _join_values("需要信息", record.get("required_info")),
                _join_values("步骤", record.get("steps")),
            )
            if part
        )
        category = "sop"
    else:
        title = str(record.get("title") or record.get("id") or "API 文档")
        text = str(record.get("content") or "")
        category = str(record.get("category") or "api_doc")

    return KnowledgeChunk(
        source=source,
        line_no=index,
        title=title,
        text=text,
        category=category,
    )


def _load_llm_wiki_fallback() -> list[KnowledgeChunk]:
    base = LLM_WIKI_API_INFRA_DIR
    chunks: list[KnowledgeChunk] = []
    if not base.exists():
        return chunks

    seen: set[Path] = set()
    for pattern in WIKI_FALLBACK_GLOBS:
        for path in sorted(base.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            relative = path.relative_to(base).as_posix()
            chunks.extend(_markdown_chunks(relative, lines))

    return chunks


def _load_remote_llm_wiki_index() -> list[KnowledgeChunk]:
    url = REMOTE_LLM_WIKI_SEARCH_INDEX_URL.strip()
    if not url:
        return []

    try:
        with urlopen(url, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError, UnicodeDecodeError):
        return []

    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        return []

    chunks: list[KnowledgeChunk] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            continue
        source = str(record.get("source") or "search_index.json")
        chunks.append(
            KnowledgeChunk(
                source=f"remote-llm-wiki/{source}",
                line_no=int(record.get("line_no") or index),
                title=str(record.get("title") or Path(source).stem),
                text=str(record.get("text") or ""),
                category="remote-llm-wiki",
            )
        )
    return chunks


def _markdown_chunks(source: str, lines: list[str]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    title = ""
    buffer: list[str] = []
    start_line = 1

    def flush() -> None:
        if not buffer:
            return
        text = " ".join(line.strip() for line in buffer if line.strip())
        if text:
            chunks.append(
                KnowledgeChunk(
                    source=f"llm-wiki/{source}",
                    line_no=start_line,
                    title=title or Path(source).stem,
                    text=text,
                    category="llm-wiki",
                )
            )

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            title = stripped.lstrip("#").strip()
            buffer = []
            start_line = line_no
            continue
        if not stripped:
            if len(buffer) >= 4:
                flush()
                buffer = []
                start_line = line_no + 1
            continue
        if not buffer:
            start_line = line_no
        buffer.append(stripped)
        if len(" ".join(buffer)) > 700:
            flush()
            buffer = []
            start_line = line_no + 1

    flush()
    return chunks


def _keywords(task_type: str, query: str) -> list[str]:
    task_keywords = {
        "signature_debug": [
            "签名",
            "验签",
            "sign",
            "SIGN_INVALID",
            "-1",
            "参数排序",
            "ASCII",
            "UTF-8",
            "timestamp",
            "app_id",
            "appid",
            "appsecret",
            "HMAC",
            "SHA1",
            "base64",
        ],
        "callback_debug": [
            "回调",
            "callback",
            "重试",
            "500",
            "200",
            "HTTPS",
            "订单号",
            "触发动作",
            "投诉",
        ],
        "api_field_qa": [],
        "credential_request": ["appsecret", "凭证", "密钥", "安全", "appid"],
        "api_onboarding": ["接入", "流程", "appid", "appsecret", "SHA-1", "白名单"],
        "renewal_debug": ["续租", "解锁码", "订单", "renewal"],
    }
    return _dedupe(task_keywords.get(task_type, []) + _query_terms(query))


def _query_terms(query: str) -> list[str]:
    terms = re.findall(r"/[A-Za-z0-9_\-/]+|[A-Za-z0-9_:\-.]{2,}|[\u4e00-\u9fff]{2,}", query)
    return [term.strip("，。；：、,.!?()[]{}\"'") for term in terms if term.strip()]


def _join_values(label: str, value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return f"{label}：" + "、".join(str(item) for item in value if item)
    return f"{label}：{value}"


def _compact(text: str, max_length: int = 360) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1] + "…"


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result
