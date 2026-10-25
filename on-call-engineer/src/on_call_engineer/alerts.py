from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import dataclass
from typing import Any


MAX_FIELD_LENGTH = 8_000


def _string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key)[:256]: str(item)[:MAX_FIELD_LENGTH]
        for key, item in value.items()
        if item is not None
    }


@dataclass(frozen=True)
class Alert:
    fingerprint: str
    state: str
    active_at: str
    value: str
    labels: dict[str, str]
    annotations: dict[str, str]

    @classmethod
    def from_prometheus(cls, value: Any) -> "Alert":
        if not isinstance(value, dict):
            raise ValueError("alert must be an object")
        labels = _string_map(value.get("labels"))
        annotations = _string_map(value.get("annotations"))
        fingerprint = str(value.get("fingerprint") or "").strip()
        if not fingerprint:
            canonical_labels = json.dumps(
                labels, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
            fingerprint = hashlib.sha256(canonical_labels.encode()).hexdigest()
        return cls(
            fingerprint=fingerprint[:256],
            state=str(value.get("state") or "")[:64],
            active_at=str(value.get("activeAt") or "")[:128],
            value=str(value.get("value") or "")[:1_024],
            labels=labels,
            annotations=annotations,
        )

    def to_prompt_data(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "state": self.state,
            "active_at": self.active_at,
            "value": self.value,
            "labels": self.labels,
            "annotations": self.annotations,
        }


class PrometheusAlertsClient:
    def __init__(self, url: str, token: str | None, timeout_seconds: float) -> None:
        self.url = url
        self.token = token
        self.timeout_seconds = timeout_seconds

    def fetch_firing(self) -> list[Alert]:
        headers = {"Accept": "application/json", "User-Agent": "otarm-on-call-engineer/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.url, headers=headers)
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"alerts API returned HTTP {response.status}")
            payload = json.load(response)

        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise ValueError("alerts API did not return a Prometheus success response")
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("alerts"), list):
            raise ValueError("alerts API response is missing data.alerts")

        alerts = [Alert.from_prometheus(item) for item in data["alerts"]]
        return [alert for alert in alerts if alert.state.casefold() == "firing"]
