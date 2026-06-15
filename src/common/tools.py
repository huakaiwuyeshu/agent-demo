from __future__ import annotations

import json
from datetime import datetime

from .entities import TaskDraft, ToolResult
from .paths import DATA_DIR


def run_signature_tools(draft: TaskDraft) -> list[ToolResult]:
    raw_sign_string = str(draft.fields.get("raw_sign_string") or "")
    return [
        check_signature_order(raw_sign_string),
        check_timestamp_present(raw_sign_string),
        search_error_code(str(draft.fields.get("error_code") or "")),
        query_sandbox_log(
            str(draft.fields.get("appid") or ""),
            str(draft.fields.get("api_path") or ""),
            str(draft.fields.get("request_time") or ""),
        ),
    ]


def check_signature_order(raw_sign_string: str) -> ToolResult:
    params = _parse_params(raw_sign_string)
    names = [name for name, _ in params]
    expected = sorted(names)

    if not params:
        return ToolResult(
            name="check_signature_order",
            status="skipped",
            detail="没有拿到可解析的签名前字符串。",
        )

    if names == expected:
        return ToolResult(
            name="check_signature_order",
            status="pass",
            detail="参数名顺序符合字母序升序。",
            data={"current_order": names, "expected_order": expected},
        )

    return ToolResult(
        name="check_signature_order",
        status="fail",
        detail="参数名顺序不符合字母序升序。",
        data={"current_order": names, "expected_order": expected},
    )


def check_timestamp_present(raw_sign_string: str) -> ToolResult:
    params = dict(_parse_params(raw_sign_string))
    timestamp = params.get("timestamp")
    if not timestamp:
        return ToolResult(
            name="check_timestamp_present",
            status="fail",
            detail="签名前字符串中没有 timestamp。",
        )

    if timestamp.isdigit():
        return ToolResult(
            name="check_timestamp_present",
            status="pass",
            detail="已找到 timestamp。演示工具只校验存在性，真实环境应继续校验时间偏差。",
            data={"timestamp": timestamp},
        )

    return ToolResult(
        name="check_timestamp_present",
        status="warn",
        detail="timestamp 存在，但不是纯数字格式。",
        data={"timestamp": timestamp},
    )


def search_error_code(error_code: str) -> ToolResult:
    if not error_code:
        return ToolResult(
            name="search_error_code",
            status="skipped",
            detail="缺少错误码，无法查询错误码说明。",
        )

    path = DATA_DIR / "error_codes.md"
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if error_code in line:
            return ToolResult(
                name="search_error_code",
                status="pass",
                detail=line.strip(),
            )

    return ToolResult(
        name="search_error_code",
        status="warn",
        detail=f"未在错误码文档中找到 {error_code}。",
    )


def query_sandbox_log(appid: str, api_path: str, request_time: str) -> ToolResult:
    path = DATA_DIR / "sample_logs.json"
    logs = json.loads(path.read_text(encoding="utf-8"))

    for item in logs:
        if (
            item.get("appid") == appid
            and item.get("api_path") == api_path
            and item.get("request_time") == request_time
        ):
            return ToolResult(
                name="query_sandbox_log",
                status="pass",
                detail=item["log_summary"],
                data=item,
            )

    return ToolResult(
        name="query_sandbox_log",
        status="warn",
        detail="示例日志中没有匹配记录。",
    )


def format_tool_results(results: list[ToolResult]) -> str:
    lines: list[str] = []
    for result in results:
        lines.append(f"- {result.name}: {result.status}。{result.detail}")
        if result.data:
            lines.append(f"  data={result.data}")
    return "\n".join(lines)


def _parse_params(raw_sign_string: str) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = []
    for part in raw_sign_string.split("&"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if name:
            params.append((name, value.strip()))
    return params
