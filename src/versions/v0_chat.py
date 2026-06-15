from __future__ import annotations

from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import direct_chat_answer


def run(scenario: Scenario) -> RunResult:
    answer = direct_chat_answer(scenario.message)
    return RunResult(
        version="v0",
        name="普通 LLM 问答",
        added_capability="无结构化能力；直接回答用户问题。",
        scenario=scenario,
        steps=[
            Step(
                title="直接把用户输入交给模型",
                content="系统没有任务类型、字段、状态、工具和安全边界的概念。",
            )
        ],
        final_output=answer,
    )
