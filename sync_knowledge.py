from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path(r"D:\zuhaowan-ai\llm-wiki\projects\api-infra\exports\agent-demo")
KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"
WEB_KNOWLEDGE_FILE = ROOT_DIR / "web" / "knowledge.js"
FILES = ("manifest.json", "api_docs.json", "faq.json", "error_codes.json", "sops.json")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"未找到 llm-wiki 导出目录：{SOURCE_DIR}")

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    for file_name in FILES:
        source = SOURCE_DIR / file_name
        if not source.exists():
            raise SystemExit(f"导出目录缺少文件：{source}")
        shutil.copy2(source, KNOWLEDGE_DIR / file_name)

    package = {
        "manifest": _read_json("manifest.json"),
        "api_docs": _read_json("api_docs.json"),
        "faq": _read_json("faq.json"),
        "error_codes": _read_json("error_codes.json"),
        "sops": _read_json("sops.json"),
    }
    WEB_KNOWLEDGE_FILE.write_text(
        "window.AGENT_DEMO_KNOWLEDGE = "
        + json.dumps(package, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )

    print(f"已同步知识包：{KNOWLEDGE_DIR}")
    print(f"已更新网页内置知识：{WEB_KNOWLEDGE_FILE}")


def _read_json(file_name: str) -> object:
    return json.loads((KNOWLEDGE_DIR / file_name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
