from __future__ import annotations

from .entities import Scenario


_SCENARIOS: dict[str, Scenario] = {
    "brief": Scenario(
        name="brief",
        title="简短问题：信息不足，需要追问",
        message="你们接口一直签名失败，帮忙看下",
        notes="适合演示 V0-V3：从泛泛回答，到识别任务、校验字段、追问阻塞项。",
    ),
    "complete": Scenario(
        name="complete",
        title="完整问题：可以进入工具检查和 Agent Loop",
        message=(
            "你们 /open/order/create 接口一直签名失败，"
            "appid=app_demo_001，错误码=SIGN_INVALID，"
            "请求时间=2026-06-15 10:20:00，"
            "签名前字符串 order_id=O1001&timestamp=1781490000&amount=10，帮忙看下"
        ),
        notes="适合演示 V4-V7：文档依据、工具调用、循环决策、状态和审计。",
    ),
    "secret": Scenario(
        name="secret",
        title="敏感信息问题：触发安全边界",
        message=(
            "你们 /open/order/create 接口签名失败，appid=app_demo_001，"
            "appsecret=demo-secret-123，帮忙看下"
        ),
        notes="适合演示 V7：appsecret 不进入普通处理链路，不写入普通日志。",
    ),
}


def list_scenarios() -> list[str]:
    return list(_SCENARIOS.keys())


def get_scenario(name: str) -> Scenario:
    try:
        return _SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"未知场景：{name}") from exc
