from __future__ import annotations

from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.tools import format_tool_results, run_signature_tools
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    steps = [
        Step(title="任务识别", content=f"task_type={draft.task_type}"),
        Step(title="执行前校验", content=f"status={validation.status}, missing={validation.missing_fields}"),
    ]

    if not validation.executable:
        final_output = build_clarification(draft, validation)
    elif draft.task_type == "signature_debug":
        results = run_signature_tools(draft)
        steps.append(Step(title="工具调用结果", content=format_tool_results(results)))
        final_output = _summarize(results)
    else:
        final_output = "当前版本只演示签名排查工具。其他任务会先停在 Skill 或人工处理。"

    return RunResult(
        version="v5",
        name="工具调用",
        added_capability="在字段满足后调用确定性工具，检查参数排序、错误码和示例日志。",
        scenario=scenario,
        steps=steps,
        final_output=final_output,
    )


def _summarize(results) -> str:
    failed = [result for result in results if result.status == "fail"]
    if failed:
        return (
            "工具检查发现明确问题："
            + "；".join(result.detail for result in failed)
            + "建议先按 expected_order 重建签名前字符串后重试。"
        )
    warnings = [result for result in results if result.status == "warn"]
    if warnings:
        return "没有发现硬性失败，但存在需要人工确认的告警：" + "；".join(result.detail for result in warnings)
    return "工具检查未发现异常。建议继续比对服务端和客户端签名前字符串是否完全一致。"
