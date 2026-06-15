from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from .entities import RunResult


def format_result(result: RunResult) -> str:
    lines = [
        "",
        "=" * 88,
        f"{result.version.upper()} · {result.name}",
        "-" * 88,
        f"新增能力：{result.added_capability}",
        f"场景：{result.scenario.title}",
        f"用户输入：{result.scenario.message}",
        "",
    ]

    for index, step in enumerate(result.steps, start=1):
        lines.append(f"[{index}] {step.title}")
        lines.append(step.content)
        lines.append("")

    lines.append("最终输出")
    lines.append(result.final_output)
    lines.append("=" * 88)
    return "\n".join(lines)


def pretty_json(value: Any) -> str:
    return json.dumps(_to_plain(value), ensure_ascii=False, indent=2)


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value
