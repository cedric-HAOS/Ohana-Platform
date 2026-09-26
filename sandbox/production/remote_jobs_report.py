# -*- coding: utf-8 -*-
"""Read-only distributed jobs report, run on INFRA-01 as ohana-agent.

Counts jobs per Paris day and type, log collections that were truncated per
source, and AI inferences per incident. Only aggregates leave the host: no
parameters, results or log contents are printed.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DATABASE = sys.argv[1]
DAYS = int(sys.argv[2])
PARIS = ZoneInfo("Europe/Paris")


def moment(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(PARIS) if parsed.tzinfo else None


def loads(value: str | None) -> dict:
    try:
        loaded = json.loads(value) if value else {}
    except ValueError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


connection = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True, timeout=5)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")

since = datetime.now(PARIS) - timedelta(days=DAYS)
per_day: dict[str, Counter] = defaultdict(Counter)
sources: dict[str, Counter] = defaultdict(Counter)
source_bytes: dict[str, list[int]] = defaultdict(list)
ai_per_incident: Counter = Counter()
ai_per_day: Counter = Counter()
truncated_per_day: dict[str, Counter] = defaultdict(Counter)
latest: dict[str, dict] = {}
ai_per_day_incident: dict[str, Counter] = defaultdict(Counter)
slow: list[dict] = []

for row in connection.execute(
    """SELECT type, status, created_at, started_at, finished_at, timeout_seconds,
    parameters_json, result_json FROM distributed_jobs
    ORDER BY julianday(created_at)"""
):
    created = moment(row["created_at"])
    if created is None or created < since:
        continue
    day = created.strftime("%Y-%m-%d")
    per_day[day][f"{row['type']} {row['status']}"] += 1
    finished = moment(row["finished_at"])
    if finished is not None:
        duration = (finished - created).total_seconds()
        if duration > max(row["timeout_seconds"] or 0, 600):
            slow.append(
                {
                    "type": row["type"],
                    "status": row["status"],
                    "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
                    "started_at": (
                        moment(row["started_at"]).strftime("%H:%M:%S")
                        if moment(row["started_at"])
                        else None
                    ),
                    "finished_at": finished.strftime("%Y-%m-%d %H:%M:%S"),
                    "minutes": round(duration / 60, 1),
                    "timeout_seconds": row["timeout_seconds"],
                }
            )
    if row["type"] == "logs.health_check" and row["status"] == "SUCCEEDED":
        for source in loads(row["result_json"]).get("sources", []):
            if not isinstance(source, dict):
                continue
            name = str(source.get("source"))
            sources[name]["collectes"] += 1
            truncated_per_day[day][f"{name} collectes"] += 1
            if source.get("truncated") is True:
                sources[name]["tronquées"] += 1
                truncated_per_day[day][f"{name} tronquées"] += 1
            if isinstance(source.get("fetched_bytes"), int):
                source_bytes[name].append(source["fetched_bytes"])
            findings = source.get("findings")
            latest[name] = {
                "le": created.strftime("%Y-%m-%d %H:%M"),
                "tronquée": source.get("truncated"),
                "octets": source.get("fetched_bytes"),
                "lignes analysées": source.get("analyzed_lines"),
                "groupes": len(findings) if isinstance(findings, list) else None,
            }
    if row["type"] == "ai.inference":
        incident = loads(row["parameters_json"]).get("incident_id") or "sans incident"
        ai_per_incident[str(incident)] += 1
        ai_per_day[day] += 1
        ai_per_day_incident[day][str(incident)] += 1

incidents = {}
if ai_per_incident:
    try:
        placeholders = ",".join("?" for _ in ai_per_incident)
        for row in connection.execute(
            f"""SELECT incident_id, node_id, service_id, capability_id, started_at,
            ended_at FROM tsunade_incidents WHERE incident_id IN ({placeholders})""",
            tuple(ai_per_incident),
        ):
            incidents[row["incident_id"]] = {
                "cible": f"{row['node_id']}/{row['service_id']}/{row['capability_id']}",
                "ouvert": (
                    moment(row["started_at"]).strftime("%Y-%m-%d %H:%M")
                    if moment(row["started_at"])
                    else row["started_at"]
                ),
                "clos": row["ended_at"] is not None,
            }
    except sqlite3.Error:
        pass

workers = [
    {
        "worker": row["worker_id"],
        "version": row["worker_version"],
        "vu": (
            moment(row["last_seen_at"]).strftime("%Y-%m-%d %H:%M")
            if moment(row["last_seen_at"])
            else row["last_seen_at"]
        ),
    }
    for row in connection.execute(
        "SELECT worker_id, worker_version, last_seen_at FROM distributed_workers"
    )
]

connection.close()
print(
    json.dumps(
        {
            "days": DAYS,
            "per_day": {day: dict(counts) for day, counts in sorted(per_day.items())},
            "log_sources": {
                name: {
                    **dict(counts),
                    "octets max": max(source_bytes[name], default=0),
                }
                for name, counts in sorted(sources.items())
            },
            "ai_per_day": dict(sorted(ai_per_day.items())),
            "ai_per_incident": [
                {"incident": incident, "inférences": count, **incidents.get(incident, {})}
                for incident, count in ai_per_incident.most_common(15)
            ],
            "slow_jobs": sorted(slow, key=lambda item: item["created_at"])[-15:],
            "truncated_per_day": {
                day: dict(counts) for day, counts in sorted(truncated_per_day.items())
            },
            "ai_per_day_incident": {
                day: {
                    incidents.get(incident, {}).get("cible", incident): count
                    for incident, count in counts.most_common()
                }
                for day, counts in sorted(ai_per_day_incident.items())
            },
            "workers": workers,
            "latest_collections": dict(sorted(latest.items())),
        },
        ensure_ascii=False,
    )
)
