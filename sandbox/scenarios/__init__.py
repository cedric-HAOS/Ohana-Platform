SCENARIOS = {
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
}