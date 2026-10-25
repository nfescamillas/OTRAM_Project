from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .agent import HeadlessAgent
from .alerts import PrometheusAlertsClient
from .config import Config
from .state import AlertState
from .worker import Worker


def build_worker(config: Config) -> Worker:
    return Worker(
        client=PrometheusAlertsClient(
            config.alerts_url, config.alerts_token, config.request_timeout_seconds
        ),
        agent=HeadlessAgent(
            config.agent_command,
            config.repository,
            config.agent_timeout_seconds,
            config.runs_directory,
        ),
        state=AlertState(config.state_file),
        poll_seconds=config.poll_seconds,
        max_concurrent_agents=config.max_concurrent_agents,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll firing alerts and run bounded Codex triage")
    parser.add_argument("--once", action="store_true", help="poll once and exit")
    parser.add_argument(
        "--base-directory",
        type=Path,
        default=Path.cwd(),
        help="base for relative repository, state, and run paths",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = Config.from_environment(args.base_directory)
    worker = build_worker(config)
    if args.once:
        worker.poll_once()
    else:
        worker.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
