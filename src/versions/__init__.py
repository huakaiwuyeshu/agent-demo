from __future__ import annotations

from collections.abc import Callable

from src.common.entities import RunResult, Scenario

from . import v0_chat, v1_intent_schema, v2_validator_clarify
from . import v3_skill_router, v4_rag, v5_tools, v6_agent_loop, v7_guardrails


Runner = Callable[[Scenario], RunResult]

VERSION_ORDER = ["v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7"]

_RUNNERS: dict[str, Runner] = {
    "v0": v0_chat.run,
    "v1": v1_intent_schema.run,
    "v2": v2_validator_clarify.run,
    "v3": v3_skill_router.run,
    "v4": v4_rag.run,
    "v5": v5_tools.run,
    "v6": v6_agent_loop.run,
    "v7": v7_guardrails.run,
}


def get_runner(version: str) -> Runner:
    return _RUNNERS[version]
