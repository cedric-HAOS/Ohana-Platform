"""A real Katsuyu worker process that never finishes its job (killed by the Sandbox).

Usage: python _slow_worker.py URL TOKEN WORKER_ID WORKSPACE KATSUYU_ROOT
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

url, token, worker_id, workspace, katsuyu_root = sys.argv[1:6]
sys.path.insert(0, katsuyu_root)

from ohana_katsuyu.handlers import HandlerContext  # noqa: E402
from ohana_katsuyu.worker import AgentClient, KatsuyuWorker  # noqa: E402


class NeverFinishes:
    def execute(self, _parameters: dict, context: HandlerContext | None = None) -> dict:
        end = time.monotonic() + 300
        while time.monotonic() < end:
            if context is not None:
                context.check()
            time.sleep(0.2)
        raise RuntimeError("killed before finishing")


Path(workspace).mkdir(parents=True, exist_ok=True)
worker = KatsuyuWorker(
    client=AgentClient(url, token),
    worker_id=worker_id,
    handlers={"system.health": NeverFinishes()},
    heartbeat_seconds=0.2,
)
worker.register()
worker.run_once()
