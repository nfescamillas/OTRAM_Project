from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from .agent import HeadlessAgent
from .alerts import Alert, PrometheusAlertsClient
from .state import AlertState


LOGGER = logging.getLogger(__name__)


class Worker:
    def __init__(
        self,
        client: PrometheusAlertsClient,
        agent: HeadlessAgent,
        state: AlertState,
        poll_seconds: float,
        max_concurrent_agents: int = 2,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client
        self.agent = agent
        self.state = state
        self.poll_seconds = poll_seconds
        self.max_concurrent_agents = max_concurrent_agents
        self.sleep = sleep
        self.monotonic = monotonic

    def _new_firing_alerts(self) -> list[Alert]:
        alerts = self.client.fetch_firing()
        previously_active = self.state.load()
        currently_active = {alert.fingerprint for alert in alerts}
        new_alerts: list[Alert] = []
        observed: set[str] = set()
        for alert in alerts:
            if alert.fingerprint not in previously_active and alert.fingerprint not in observed:
                new_alerts.append(alert)
            observed.add(alert.fingerprint)

        # Save the observed set before dispatch. A worker crash cannot fan out the same alert twice.
        # Failed agent runs are retained as artifacts for explicit human retry.
        self.state.save(currently_active)
        return new_alerts

    def _dispatch(self, alert: Alert) -> None:
        try:
            LOGGER.info(
                "dispatching alert %s",
                json.dumps(
                    {
                        "fingerprint": alert.fingerprint,
                        "alertname": alert.labels.get("alertname", ""),
                        "severity": alert.labels.get("severity", ""),
                    },
                    sort_keys=True,
                ),
            )
            result = self.agent.run(alert)
            if result.succeeded:
                LOGGER.info("agent completed for alert %s", alert.fingerprint)
            else:
                LOGGER.error(
                    "agent failed for alert %s with exit code %s%s",
                    alert.fingerprint,
                    result.return_code,
                    " (timeout)" if result.timed_out else "",
                )
        except Exception:
            LOGGER.exception("unexpected agent failure for alert %s", alert.fingerprint)

    def poll_once(self) -> int:
        new_alerts = self._new_firing_alerts()
        for alert in new_alerts:
            self._dispatch(alert)
        return len(new_alerts)

    def run_forever(self) -> None:
        with ThreadPoolExecutor(
            max_workers=self.max_concurrent_agents, thread_name_prefix="alert-agent"
        ) as executor:
            while True:
                started = self.monotonic()
                try:
                    for alert in self._new_firing_alerts():
                        executor.submit(self._dispatch, alert)
                except Exception:
                    LOGGER.exception("alert poll failed")
                elapsed = self.monotonic() - started
                self.sleep(max(0.0, self.poll_seconds - elapsed))
