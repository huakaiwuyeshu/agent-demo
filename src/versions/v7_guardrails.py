from __future__ import annotations

from src.common.agent_state import TaskState
from src.common.audit import AuditLog, mask_sensitive_text
from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.render import pretty_json
from src.common.schemas import requires_human_review
from src.common.tools import format_tool_results, run_signature_tools
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    audit = AuditLog()
    masked_message = mask_sensitive_text(scenario.message)
    audit.record("user_input_received", {"message_summary": masked_message})

    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    state = TaskState(task_type=draft.task_type)
    state.mark("identify_task")
    audit.record(
        "task_identified",
        {
            "task_type": draft.task_type,
            "confidence": draft.confidence,
            "security_flags": draft.security_flags,
        },
    )

    steps = [
        Step(title="安全预处理", content=f"普通日志中的输入摘要：{masked_message}"),
        Step(title="Task State 创建", content=pretty_json(state)),
        Step(title="Schema / Guardrail 校验", content=pretty_json(validation)),
    ]

    if validation.status == "blocked":
        state.mark("guardrail_block")
        state.blocked("security_boundary")
        audit.record("blocked", {"reasons": validation.blocked_reasons})
        final_output = build_clarification(draft, validation)
    elif requires_human_review(draft.task_type):
        state.mark("human_gate")
        state.blocked("requires_human_review")
        audit.record("human_review_required", {"task_type": draft.task_type})
        final_output = "这个任务涉及凭证或高风险动作，Agent 只能整理材料，不能自动执行；需要人工审核。"
    elif not validation.executable:
        state.mark("clarify_missing_fields")
        state.wait_for_fields(validation.missing_fields)
        audit.record("needs_clarification", {"missing_fields": validation.missing_fields})
        final_output = build_clarification(draft, validation)
    else:
        state.mark("validate_schema")
        state.ready_to_execute()
        audit.record("ready_to_execute", {"next_action": state.next_action})

        if draft.task_type == "signature_debug":
            tool_results = run_signature_tools(draft)
            state.mark("run_signature_tools")
            audit.record(
                "tools_called",
                {
                    "tools": [item.name for item in tool_results],
                    "statuses": [item.status for item in tool_results],
                },
            )
            steps.append(Step(title="受控工具调用", content=format_tool_results(tool_results)))
            final_output = _final_answer(tool_results)
        else:
            final_output = "当前任务已通过安全边界，等待对应 Skill 的工具实现。"

        state.mark("answer")
        state.finished()
        audit.record("task_finished", {"status": state.status})

    steps.append(Step(title="Task State 最终状态", content=pretty_json(state)))
    steps.append(Step(title="Audit 摘要", content=audit.summary()))

    return RunResult(
        version="v7",
        name="状态 / 审计 / 安全边界",
        added_capability="增加 Task State、Audit、敏感信息脱敏、阻断策略和人工审核闸门。",
        scenario=scenario,
        steps=steps,
        final_output=final_output,
    )


def _final_answer(tool_results) -> str:
    order_result = next((item for item in tool_results if item.name == "check_signature_order"), None)
    if order_result and order_result.status == "fail":
        return (
            "结论：签名前参数排序不符合文档要求。"
            "请按字母序重建签名前字符串，重新生成签名后重试。"
            "本次排查只使用脱敏摘要和受控工具结果，未记录 appsecret。"
        )
    return "结论：未发现确定性排序错误。建议进入人工复核或继续补充客户端签名前字符串。"
