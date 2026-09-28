"""Local Home Assistant WebSocket answering the history backfill (Phase 4)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from threading import Event, Thread
from zoneinfo import ZoneInfo

from aiohttp import WSMsgType, web

PARIS = ZoneInfo("Europe/Paris")
ENTITY = "sensor.ohana_host_utilisation_disque_racine"


class HomeAssistantHistory:
    """Entity registry and hourly statistics of the INFRA-01 disk sensor."""

    def __init__(self, daily_maximum: dict[str, float], token: str) -> None:
        self.daily_maximum = daily_maximum
        self.token = token
        self.requests: list[str] = []
        self.url: str | None = None
        self._loop = asyncio.new_event_loop()
        self._started = Event()
        self._runner: web.AppRunner | None = None
        self._thread = Thread(target=self._serve, daemon=True)

    def start(self) -> None:
        self._thread.start()
        if not self._started.wait(10):
            raise RuntimeError("Home Assistant simulé non démarré")

    def stop(self) -> None:
        if self._runner is not None:
            asyncio.run_coroutine_threadsafe(self._runner.cleanup(), self._loop).result(
                10
            )
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(10)

    def _serve(self) -> None:
        asyncio.set_event_loop(self._loop)
        application = web.Application()
        application.router.add_get("/api/websocket", self._websocket)
        self._runner = web.AppRunner(application)
        self._loop.run_until_complete(self._runner.setup())
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        self._loop.run_until_complete(site.start())
        port = site._server.sockets[0].getsockname()[1]  # noqa: SLF001
        self.url = f"http://127.0.0.1:{port}"
        self._started.set()
        self._loop.run_forever()

    async def _websocket(self, request: web.Request) -> web.WebSocketResponse:
        socket = web.WebSocketResponse()
        await socket.prepare(request)
        await socket.send_json({"type": "auth_required"})
        async for message in socket:
            if message.type != WSMsgType.TEXT:
                break
            payload = json.loads(message.data)
            self.requests.append(payload["type"])
            await socket.send_json(self._answer(payload))
        return socket

    def _answer(self, payload: dict) -> dict:
        if payload["type"] == "auth":
            ok = payload.get("access_token") == self.token
            return {"type": "auth_ok" if ok else "auth_invalid"}
        if payload["type"] == "config/entity_registry/list":
            return {
                "id": payload["id"],
                "type": "result",
                "success": True,
                "result": [
                    {"entity_id": "sensor.other", "platform": "mqtt", "unique_id": "x"},
                    {
                        "entity_id": ENTITY,
                        "platform": "mqtt",
                        "unique_id": "ohana_host_disk_usage",
                    },
                ],
            }
        if payload["type"] == "recorder/statistics_during_period":
            start = datetime.fromisoformat(payload["start_time"])
            end = datetime.fromisoformat(payload["end_time"])
            rows = []
            at = start
            while at < end:
                local = at.astimezone(PARIS)
                peak = self.daily_maximum.get(local.date().isoformat())
                if peak is not None:
                    value = peak if local.hour == 14 else peak - 0.6
                    rows.append(
                        {
                            "start": at.astimezone(UTC).timestamp() * 1000,
                            "min": value - 0.1,
                            "max": value,
                            "mean": value - 0.05,
                        }
                    )
                at += timedelta(hours=1)
            return {
                "id": payload["id"],
                "type": "result",
                "success": True,
                "result": {ENTITY: rows},
            }
        return {
            "id": payload.get("id"),
            "type": "result",
            "success": False,
            "error": {"code": "unknown_command"},
        }
