from __future__ import annotations

from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.rag import format_evidence, search_knowledge
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    evidence = search_knowledge(draft.task_type, scenario.message)

    if not validation.executable:
        final_output = build_clarification(draft, validation)
    else:
        final_output = (
            "根据文档依据，优先检查参数排序、UTF-8 编码、URL 编码时机、timestamp 时间偏差，"
            "并确认 appsecret 没有进入普通对话或日志。"
        )

    return RunResult(
        version="v4",
        name="文档检索 / RAG",
        added_capability="回答前先检索 API 文档和错误码说明，减少无依据猜测。",
        scenario=scenario,
        steps=[
            Step(title="识别任务", content=f"task_type={draft.task_type}"),
            Step(title="检索到的依据", content=format_evidence(evidence)),
        ],
        final_output=final_output,
        artifacts={"evidence": evidence},
    )
