from __future__ import annotations

from src.common.clarify import build_clarification
from src.common.entities import RunResult, Scenario, Step
from src.common.mock_llm import extract_task
from src.common.render import pretty_json
from src.common.validator import validate_task


def run(scenario: Scenario) -> RunResult:
    draft = extract_task(scenario.message)
    validation = validate_task(draft)
    final_output = (
        "字段已满足最小执行条件，可以进入下一步。"
        if validation.executable
        else build_clarification(draft, validation)
    )

    return RunResult(
        version="v2",
        name="Schema 校验 + 追问策略",
        added_capability="LLM 负责抽取，代码负责判断缺什么；只追问阻塞项。",
        scenario=scenario,
        steps=[
            Step(title="结构化草稿", content=pretty_json(draft)),
            Step(title="Schema 校验结果", content=pretty_json(validation)),
        ],
        final_output=final_output,
    )
