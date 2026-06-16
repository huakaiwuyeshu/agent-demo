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

    if evidence:
        final_output = "依据文档：\n" + "\n".join(f"- {item.text}" for item in evidence[:3])
    elif not validation.executable:
        final_output = build_clarification(draft, validation)
    else:
        final_output = "当前 demo 知识包和本地 llm-wiki 都没有命中文档依据，需要先补充或重新导出资料。"

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
