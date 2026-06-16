from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
SKILLS_DIR = ROOT_DIR / "skills"

LLM_WIKI_API_INFRA_DIR = Path(
    os.getenv(
        "AGENT_DEMO_LLM_WIKI_DIR",
        r"D:\zuhaowan-ai\llm-wiki\projects\api-infra",
    )
)

REMOTE_LLM_WIKI_SEARCH_INDEX_URL = os.getenv(
    "AGENT_DEMO_REMOTE_WIKI_INDEX_URL",
    "https://raw.githubusercontent.com/huakaiwuyeshu/llm-wiki/main/"
    "projects/api-infra/exports/agent-demo/search_index.json",
)
