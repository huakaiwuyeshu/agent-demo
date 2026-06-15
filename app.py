from __future__ import annotations

import argparse
from typing import Iterable

from src.common.render import format_result
from src.common.scenarios import get_scenario, list_scenarios
from src.versions import VERSION_ORDER, get_runner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="API 接入 Agent 多版本演进 Demo",
    )
    parser.add_argument(
        "--version",
        default="all",
        help="版本入口：all, v0, v1, v2, v3, v4, v5, v6, v7",
    )
    parser.add_argument(
        "--scenario",
        default="brief",
        choices=list_scenarios(),
        help="内置演示场景",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="自定义用户输入。传入后会覆盖 scenario 中的默认消息。",
    )
    return parser.parse_args()


def selected_versions(version: str) -> Iterable[str]:
    normalized = version.lower().strip()
    if normalized == "all":
        return VERSION_ORDER
    if normalized not in VERSION_ORDER:
        raise SystemExit(f"未知版本：{version}。可选：all, {', '.join(VERSION_ORDER)}")
    return [normalized]


def main() -> None:
    args = parse_args()
    scenario = get_scenario(args.scenario)
    if args.message:
        scenario = scenario.with_message(args.message)

    for version in selected_versions(args.version):
        runner = get_runner(version)
        result = runner(scenario)
        print(format_result(result))


if __name__ == "__main__":
    main()
