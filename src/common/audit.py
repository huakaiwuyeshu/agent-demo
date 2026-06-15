from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AuditLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "event_type": event_type,
                "payload": _mask_payload(payload),
            }
        )

    def summary(self) -> str:
        lines = []
        for event in self.events:
            lines.append(f"- {event['event_type']}: {event['payload']}")
        return "\n".join(lines)


def mask_sensitive_text(text: str) -> str:
    text = re.sub(
        r"(appsecret\s*[=:：]\s*)\S+",
        r"\1***MASKED***",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(secret\s*[=:：]\s*)\S+",
        r"\1***MASKED***",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _mask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            masked[key] = mask_sensitive_text(value)
        elif isinstance(value, dict):
            masked[key] = _mask_payload(value)
        else:
            masked[key] = value
    return masked
