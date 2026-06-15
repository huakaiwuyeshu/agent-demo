from __future__ import annotations

from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.render import pretty_json
from src.common.schemas import task_label


def run(scenario: Scenario) -> RunResult:
    draft = extract_task(scenario.message)
    return RunResult(
        version="v1",
        name="任务识别与结构化",
        added_capability="把自然语言转成 task_type + fields，后续才有机会校验和路由。",
        scenario=scenario,
        steps=[
            Step(
                title="识别任务类型",
                content=f"task_type={draft.task_type}（{task_label(draft.task_type)}），confidence={draft.confidence}",
            ),
            Step(
                title="抽取字段草稿",
                content=pretty_json(draft),
            ),
        ],
        final_output="我先不直接排查，而是把输入整理成结构化任务，交给后续模块判断能不能继续。",
    )
