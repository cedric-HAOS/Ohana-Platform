"""Isolated process hosting the real Katsuyu registration and polling cycle."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from time import sleep


def main() -> None:
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.path.insert(0, config["checkout"])
    from ohana_katsuyu.ai import AiInferenceHandler
    from ohana_katsuyu.handlers import LogsHealthCheckHandler, LogsInvestigateHandler
    from ohana_katsuyu.status import StatusStore
    from ohana_katsuyu.worker import AgentClient, KatsuyuWorker

    logging.basicConfig(level=logging.INFO)
    client = AgentClient(
        config["url"],
        Path(config["token_file"]).read_text(encoding="utf-8"),
        ca_certificate_file=Path(config["ca"]),
    )
    worker = KatsuyuWorker(
        client=client,
        worker_id="sandbox-network-worker",
        heartbeat_seconds=0.5,
        status_store=StatusStore(Path(config["status_file"])),
        handlers={
            "logs.health_check": LogsHealthCheckHandler(client.read_log_source),
            "logs.investigate": LogsInvestigateHandler(client.read_log_source),
            "ai.inference": AiInferenceHandler(
                runtime=Path(config["runtime"]),
                model=Path(config["model"]),
                model_id=config["model_id"],
                model_sha256=config["sha256"],
                context_size=config["context_size"],
            ),
        },
        # No power action or production update check in the laboratory process.
        shutdown_requester=None,
    )
    worker.register()
    stop_file = Path(config["stop_file"])
    while not stop_file.exists():
        processed = worker.run_once()
        if worker.shutdown_requested:
            raise RuntimeError("Unexpected shutdown instruction in local sandbox")
        if not processed:
            sleep(0.2)


if __name__ == "__main__":
    main()
