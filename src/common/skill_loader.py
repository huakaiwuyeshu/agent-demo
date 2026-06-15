from __future__ import annotations

from .paths import SKILLS_DIR
from .schemas import skill_name


def route_skill(task_type: str) -> str | None:
    return skill_name(task_type)


def load_skill(skill: str) -> str:
    path = SKILLS_DIR / skill / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill 不存在：{path}")
    return path.read_text(encoding="utf-8")


def summarize_skill(skill_text: str) -> str:
    lines = [line.strip() for line in skill_text.splitlines() if line.strip()]
    return "\n".join(lines[:12])
