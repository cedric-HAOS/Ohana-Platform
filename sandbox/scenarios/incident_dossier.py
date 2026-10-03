"""Phase 8: real Agent/Vision HTTP with replayed, non-production incidents.

Supervisor and observations are simulated. AI payload is a recorded-contract
fixture, not a model invocation. --serve keeps the local UI open for review.
"""

from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

from ohana_agent.api.http import AdministrationHTTPServer
from ohana_agent.observation import ObservationStatus
from ohana_agent.tsunade.local_time import paris_now

from scenarios.catalogue_repair_cycle import TELEINFO, Konoha, _lab
from scenarios.incident_history import _host
from scenarios.katsuyu_shizune_vitals import ADMIN_TOKEN
from scenarios.ohana_self_supervision import _http, _serve_vision


def run(*, serve: bool = False) -> dict:
    output = (
        Path(__file__).resolve().parents[1]
        / "runs"
        / (paris_now().strftime("%Y%m%d-%H%M%S") + "-incident-dossier")
    )
    output.mkdir(parents=True)
    checks = []
    metrics = {}
    konoha = Konoha(addons=[{"addon": TELEINFO, "state": "stopped"}])
    with _lab(konoha) as lab:
        _, teleinfo = lab.diagnose("tic-linky")
        lab.authorize(teleinfo)
        teleinfo = lab.verify("tic-linky", teleinfo)
        checks.append(
            (
                "Téléinformation réparée et vérifiée",
                (
                    teleinfo.state == "resolved"
                    and teleinfo.repairs[0].status == "succeeded"
                ),
            )
        )
        host = lab.incidents.process(
            _host(paris_now(), ObservationStatus.UNHEALTHY, ["disk_critical"])
        )
        lab.incidents.append_record(
            host.incident_id,
            {
                "kind": "investigation",
                "summary": "Lecture du disque interrompue",
                "payload": {
                    "operation": "host.health",
                    "status": "TIMEOUT",
                    "error": "Délai dépassé",
                    "result": {},
                },
            },
        )
        lab.incidents.append_record(
            host.incident_id,
            {
                "kind": "diagnostic",
                "summary": "Analyse insuffisante",
                "payload": {
                    "decision": "investigate",
                    "decision_source": "deterministic",
                    "facts": ["Disque signalé critique par l’observation"],
                    "confirmation_gap": ["Répartition de l’espace indisponible"],
                    "failed_investigations": ["host.health"],
                },
            },
        )
        lab.incidents.append_record(
            host.incident_id,
            {
                "kind": "action",
                "summary": "Libérer de l’espace après inspection",
                "payload": {"proposals": ["Inspecter les fichiers volumineux"]},
            },
        )
        lab.incidents.process(
            _host(paris_now() + timedelta(seconds=1), ObservationStatus.HEALTHY, [])
        )
        _, ai = lab.diagnose("zwave")
        lab.incidents.append_record(
            ai.incident_id,
            {
                "kind": "diagnostic",
                "summary": "Contexte insuffisant pour conclure",
                "payload": {
                    "decision": "investigate",
                    "decision_source": "katsuyu_ai",
                    "origin": "katsuyu_ai",
                    "epistemic_status": "hypothesis",
                    "verdict": "INSUFFICIENT_CONTEXT",
                    "cycle_status": "ai_completed",
                    "confirmation_gap": ["État radio non mesuré"],
                    "missing_context": ["Journaux complets du pilote"],
                    "collection_facts": {
                        "source": "investigation.followup",
                        "matched_lines": 73,
                        "anomaly_count": 0,
                        "truncated": True,
                    },
                    "hypotheses": [
                        {
                            "statement": "Interruption radio possible",
                            "confidence": 0.5,
                            "supporting_evidence": ["Communication interrompue"],
                            "contradicting_evidence": ["Pilote actif"],
                        }
                    ],
                },
            },
        )
        # Keep the pilot episode intact; a second episode exercises the API's
        # 1000-event bound without hiding the first episode's proposal.
        long_host = lab.incidents.process(
            _host(
                paris_now() + timedelta(seconds=2),
                ObservationStatus.UNHEALTHY,
                ["disk_critical"],
            )
        )
        for index in range(1000):
            lab.incidents.append_record(
                long_host.incident_id,
                {
                    "kind": "investigation",
                    "summary": f"Mesure historique {index}",
                    "payload": {
                        "operation": "host.health",
                        "status": "OK",
                        "result": {"disk_percent": 90},
                    },
                },
            )
        administration = AdministrationHTTPServer(
            service=lab.service, token=ADMIN_TOKEN, worker_token="w" * 32, port=0
        )
        administration.start()
        address, port = administration.address
        context, server, thread, listener, base = _serve_vision(
            output, f"http://{address}:{port}", f"http://{address}:{port}"
        )
        try:
            documents = []
            for label, incident in [
                ("teleinformation", teleinfo),
                ("host", host),
                ("ai", ai),
                ("long_host", long_host),
            ]:
                samples = []
                for _ in range(20):
                    document, elapsed = _http(
                        base,
                        "/api/administration/tsunade/incidents/"
                        + str(incident.incident_id),
                    )
                    samples.append(elapsed)
                documents.append(document)
                metrics[label] = {
                    "median_ms": round(statistics.median(samples), 2),
                    "p95_ms": round(sorted(samples)[18], 2),
                    "bytes": len(json.dumps(document).encode()),
                }
                checks.append(
                    (f"API {label} p95 < 1000 ms", sorted(samples)[18] < 1000)
                )
            checks.append(
                ("Hôte : aucune réparation exécutée", not documents[1]["repairs"])
            )
            checks.append(
                (
                    "Hôte : proposition et limites conservées",
                    any(e["kind"] == "action" for e in documents[1]["events"])
                    and any(
                        e["payload"].get("failed_investigations")
                        for e in documents[1]["events"]
                    ),
                )
            )
            checks.append(
                (
                    "Dossier long : borne API de 1000 événements",
                    len(documents[3]["events"]) == 1000,
                )
            )
            fixtures = output / "incidents.json"
            fixtures.write_text(
                json.dumps(documents, ensure_ascii=False), encoding="utf-8"
            )
            node = shutil.which("node")
            if not node:
                raise RuntimeError("Node requis pour mesurer le rendu")
            benchmark = (
                Path(__file__).resolve().parents[1] / "integration/dossier_render.cjs"
            )
            completed = subprocess.run(
                [node, str(benchmark), str(fixtures)],
                capture_output=True,
                text=True,
                check=True,
            )
            metrics["render"] = json.loads(completed.stdout)
            checks.append(
                (
                    "Rendu JS des dossiers p95 < 100 ms",
                    all(item["p95_ms"] < 100 for item in metrics["render"]),
                )
            )
            result = {
                "passed": all(value for _, value in checks),
                "checks": checks,
                "details": {
                    "metrics": metrics,
                    "url": base + "/ui/#incidents",
                    "captures": str(output),
                    "scope": "Rejeu local, aucun accès production ni inférence IA",
                },
            }
            (output / "report.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if serve:
                print(json.dumps(result, ensure_ascii=False), flush=True)
                while True:
                    time.sleep(1)
            return result
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            administration.stop()
            context.observation_store.close()
            context.incident_store.close()


if __name__ == "__main__":
    run(serve="--serve" in sys.argv)
