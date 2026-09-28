SCENARIOS = {
    "teleinformation-supervisor-cycle": (
        "scenarios.teleinformation_supervisor_cycle",
        "Confirmer l'arrêt Téléinformation sans IA, conserver le diagnostic et résoudre l'incident.",
    ),
    "followup-evidence-cycle": (
        "scenarios.followup_evidence_cycle",
        "Conserver les preuves et terminer une réévaluation sans boucle, même après reprise.",
    ),
    "local-diagnosis-worker-unavailable": (
        "scenarios.local_diagnosis_worker_unavailable",
        "Diagnostiquer et résoudre un incident local pendant l'absence de Katsuyu.",
    ),
    "followup-restart": (
        "scenarios.followup_restart",
        "Reprendre les suivis persistés sans perte de preuves ni relance après arrêt.",
    ),
    "terminal-jobs-over-16": (
        "scenarios.terminal_jobs_over_16",
        (
            "Réconcilier plus de 16 échecs terminaux "
            "sans nouveau polling Katsuyu."
        ),
    ),
    "katsuyu-unavailable": (
        "scenarios.katsuyu_unavailable",
        (
            "Vérifier le mode dégradé lorsque "
            "Katsuyu devient indisponible."
        ),
    ),
    "probe-timeout": (
        "scenarios.probe_timeout",
        (
            "Vérifier qu'une sonde en timeout "
            "ne confirme jamais une panne."
        ),
    ),
    "probe-error": (
        "scenarios.probe_error",
        (
            "Vérifier qu'une exception de sonde "
            "reste une limitation de collecte "
            "sans fuite d'information sensible."
        ),
    ),
    "probe-confirmed-failure": (
        "scenarios.probe_confirmed_failure",
        (
            "Vérifier qu'une panne réellement mesurée "
            "produit un diagnostic déterministe confirmé."
        ),
    ),
    "diagnostic-levels": (
        "scenarios.diagnostic_levels",
        (
            "Vérifier le contrat CONFIRMED, PROBABLE "
            "et INSUFFICIENT_CONTEXT."
        ),
    ),
    "tsunade-observation-wiring": (
        "scenarios.tsunade_observation_wiring",
        (
            "Vérifier qu'un nouvel incident sans source de logs "
            "déclenche Tsunade une seule fois, tandis qu'une "
            "source de logs collecte d'abord ses preuves."
        ),
    ),
    "vision-unavailable": (
        "scenarios.vision_unavailable",
        (
            "Ohana-Vision arrêté : host.health ouvre un incident Tsunade, "
            "confirmé par sonde sans IA, résolu au retour du service."
        ),
    ),
    "supervised-repair-cycle": (
        "scenarios.supervised_repair_cycle",
        (
            "Réparation dnsmasq supervisée : proposition, report, refus, "
            "autorisation, vérification, échec, expiration et reprise."
        ),
    ),
    "catalogue-repair-cycle": (
        "scenarios.catalogue_repair_cycle",
        (
            "Réparations teleinfo2mqtt, Z-Wave JS et chrony : cible observée, "
            "autorisation, exécution, vérification, refus et garde-fous."
        ),
    ),
    "repair-verification-probe": (
        "scenarios.repair_verification_probe",
        (
            "Vérifier une réparation chrony par une sonde immédiate, sans "
            "attendre le cycle NTP horaire (bootstrap de production)."
        ),
    ),
    "dns-cascade": (
        "scenarios.dns_cascade",
        (
            "Panne dnsmasq vue d'abord comme échec de résolution Z-Wave : "
            "observation DHCP immédiate, rattachement, aucune réparation aval."
        ),
    ),
    "vision-ingestion-load": (
        "scenarios.vision_ingestion_load",
        (
            "Vision sous la charge de Konoha : 1 observation/s, 2 pages qui "
            "rechargent la chronologie 24 h, latences d'ingestion mesurées."
        ),
    ),
    "home-assistant-restart-grace": (
        "scenarios.home_assistant_restart_grace",
        (
            "Une entité introuvable pendant un redémarrage de Home Assistant "
            "est dégradée, critique seulement après 10 minutes."
        ),
    ),
    "vision-checkpoint-off-ingestion": (
        "scenarios.vision_checkpoint_off_ingestion",
        (
            "Vision ne recopie jamais le WAL SQLite dans vision.db pendant "
            "une requête d'ingestion : la carte SD d'INFRA-01 la bloquait 5 s."
        ),
    ),
    "recurring-log-review": (
        "scenarios.recurring_log_review",
        (
            "Revoir chaque jour les mêmes anomalies HA-01 sans nouvelle "
            "expertise, en heure de Paris, et relancer sur aggravation."
        ),
    ),
    "known-repair-history": (
        "scenarios.known_repair_history",
        (
            "Phase 3 : chaque exécution d'une réparation connue est comptée avec "
            "son résultat ; une réparation désactivée n'est plus proposée."
        ),
    ),
    "manual-resolution": (
        "scenarios.manual_resolution",
        (
            "Phase 3 : action manuelle déclarée, confirmée par Shikamaru, "
            "conservée sur accord comme note jamais exécutable."
        ),
    ),
    "log-noise-triage": (
        "scenarios.log_noise_triage",
        (
            "Les 4 sources du 27 septembre : bruit Ohana, sauvegarde NVM et "
            "avertissements rares sans incident ; erreur acceptée comme connue."
        ),
    ),
    "supervisor-log-window": (
        "scenarios.supervisor_log_window",
        (
            "ZWAVE-01 : plus de 10 000 lignes en 24 h lues par le Supervisor, "
            "fenêtre couverte sans troncature ni erreur de la veille."
        ),
    ),
    "slow-completion-reads": (
        "scenarios.slow_completion_reads",
        (
            "Pages Vision et Shizune lisibles en moins d'une seconde pendant "
            "le traitement lent d'un résultat Katsuyu (502 du 28 septembre)."
        ),
    ),
    "ambiguous-katsuyu-cycle": (
        "scenarios.ambiguous_katsuyu_cycle",
        (
            "Vérifier qu'un incident logs.health ambigu "
            "déclenche Katsuyu, reste PROBABLE et ne "
            "boucle pas sur les mêmes preuves."
        ),
    ),
}
