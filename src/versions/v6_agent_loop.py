from __future__ import annotations

from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.rag import format_evidence, search_knowledge
from src.common.skill_loader import route_skill
from src.common.tools import format_tool_results, run_signature_tools
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    steps: list[Step] = []

    steps.append(Step(title="Observe", content=f"收到用户输入：{scenario.message}"))

    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    steps.append(
        Step(
            title="Think",
            content=f"识别为 {draft.task_type}；校验状态 {validation.status}。",
        )
    )

    if not validation.executable:
        clarification = build_clarification(draft, validation)
        steps.append(Step(title="Act", content="信息不足或触发边界，选择追问/阻断，而不是继续工具调用。"))
        steps.append(Step(title="Answer", content=clarification))
        final_output = clarification
    else:
        skill = route_skill(draft.task_type)
        evidence = search_knowledge(draft.task_type, scenario.message)
        steps.append(Step(title="Act", content=f"命中 Skill：{skill}；同时检索文档依据。"))
        steps.append(Step(title="Observe", content=format_evidence(evidence)))

        if draft.task_type == "signature_debug":
            tool_results = run_signature_tools(draft)
            steps.append(Step(title="Act", content="调用签名排查工具。"))
            steps.append(Step(title="Observe", content=format_tool_results(tool_results)))
            final_output = _answer_from_observation(tool_results)
        else:
            final_output = "当前 Loop 已完成识别、校验、Skill 和文档检索，后续交给对应任务工具。"

        steps.append(Step(title="Answer", content=final_output))

    return RunResult(
        version="v6",
        name="Agent Loop",
        added_capability="把识别、校验、Skill、文档和工具串成 Observe -> Think -> Act -> Observe -> Answer。",
        scenario=scenario,
        steps=steps,
        final_output=final_output,
    )


def _answer_from_observation(tool_results) -> str:
    order_result = next((item for item in tool_results if item.name == "check_signature_order"), None)
    if order_result and order_result.status == "fail":
        return (
            "最可能原因是签名前参数排序错误。"
            f"当前顺序是 {order_result.data.get('current_order')}，"
            f"应改为 {order_result.data.get('expected_order')}。"
            "请按正确顺序重建签名前字符串后重新生成 sign。"
        )
    return "这轮工具检查没有定位到确定原因。下一步建议比对客户端和服务端签名前字符串。"
