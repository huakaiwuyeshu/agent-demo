from __future__ import annotations

from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.skill_loader import load_skill, route_skill, summarize_skill
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    skill = route_skill(draft.task_type)

    steps = [
        Step(title="任务类型", content=f"{draft.task_type}"),
        Step(title="Skill 路由", content=skill or "没有命中 Skill，需要人工分流或补充意图。"),
    ]

    if skill:
        skill_text = load_skill(skill)
        steps.append(Step(title="渐进式加载 Skill", content=summarize_skill(skill_text)))

    if not validation.executable:
        final_output = build_clarification(draft, validation)
    elif skill:
        final_output = (
            f"已命中 `{skill}`。我会按这份 SOP 排查，而不是临场发挥。"
            "下一步进入文档依据或工具检查。"
        )
    else:
        final_output = "当前任务没有可用 Skill，建议进入人工处理或补充一个新的 Skill。"

    return RunResult(
        version="v3",
        name="Skill 路由",
        added_capability="根据任务类型加载对应业务 SOP，让模型复用专家经验。",
        scenario=scenario,
        steps=steps,
        final_output=final_output,
    )
