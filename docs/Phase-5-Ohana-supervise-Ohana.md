# Phase 5 — Ohana supervise Ohana

## Cadre — 28 septembre 2026

Phase démarrée après la clôture de la Phase 4. Référence :
[roadmap commune](../ROADMAP.md).

Objectif : faire des composants Ohana des éléments observables de Konoha,
sans construire une introspection complète de chaque processus. Pour chaque
composant, savoir s'il est vivant, s'il répond, s'il travaille encore, quand
il a travaillé pour la dernière fois, et si sa défaillance empêche
l'observation des autres.

### Choix de l'utilisateur (28 septembre)

- **Agent figé : détection seulement.** Aucun watchdog systemd, aucun
  redémarrage automatique. Un composant interne muet est signalé ; un Agent
  entièrement figé est vu de l'extérieur (Vision, disponibilité MQTT dans
  Home Assistant).
- **Panne de Vision vue par l'Agent : incident Tsunade sans réparation.**
  Aucune entrée au catalogue de réparations ; le redémarrage de Vision reste
  une décision manuelle pendant la Phase 5.

### Choix de conception

- **Pas de dépendance circulaire.** L'incident sur Vision reste dans l'Agent.
  Il atteint l'utilisateur par des canaux qui ne passent pas par Vision :
  notification APNs directe vers Shizune, santé de l'hôte publiée par MQTT à
  Home Assistant. Les observations restent dans la file de l'Agent et
  rejoignent Vision à son retour.
- **L'Agent observe même sans Vision.** Constat du 28 septembre : l'Agent ne
  démarrait ni son planificateur ni la santé de l'hôte tant que Vision
  n'avait pas accepté l'infrastructure. Un Agent démarré pendant une panne de
  Vision n'observait donc rien, pas même la panne de Vision. Vision répond 202
  même à une observation qu'il rejette : rien n'obligeait à l'attendre.
- **La santé de l'hôte (`host.health`) porte l'état vital de l'Agent et de
  Vision.** C'est déjà le chemin vers Home Assistant, Vision et Tsunade
  (incident, expertise, notification) : aucun nouveau canal.
- **Diagnostic déterministe, sans IA.** Chaque nouvelle raison a sa procédure
  connue et sa sonde de lecture seule.

## Lots

| Lot | Contenu | État |
| --- | --- | --- |
| 1 — Vitaux de l'Agent | dernière activité utile des composants internes critiques | commis localement : Agent 96773aa, Platform 56538e9 ; non poussé, non publié |
| 2 — L'Agent observe Vision | démarrage sans Vision, sonde HTTP et ingestion, notification d'escalade | en cours, non commis |
| 3 — Vision observe l'Agent | « Agent silencieux » calculé par Vision avec sa propre horloge | à faire |
| 4 — Katsuyu et Shizune | dernier travail réussi et runtime par capacité ; passerelle et dernière synchronisation | à faire |
| 5 — Vision, Sandbox, documentation | section « Ohana » dans Vision, scénarios, validations réelles | à faire |

### Lot 1 — vitaux de l'Agent

`runtime/vitals.py` (`AgentVitals`) : chaque composant déclare une borne de
silence et note un battement quand il accomplit un travail réel. États :
`waiting` (déclaré, pas encore de battement, borne non dépassée), `active`,
`stale` (silence au-delà de la borne, ou jamais de battement).

| Composant | Battement | Borne |
| --- | --- | --- |
| `scheduler` — Planificateur | un tick a exécuté au moins une tâche | 300 s |
| `vision_delivery` — Livraison à Vision | un passage de la file a livré ou l'a vidée | 300 s |
| `tsunade` — Tsunade (incidents) | une observation traitée par le gestionnaire Tsunade | 300 s |
| `administration` — API d'administration | rappel planifié dans la boucle du listener local toutes les 10 s | 60 s |

Le battement de l'API d'administration est émis par sa propre boucle : une
boucle bloquée (cause des pages Vision figées et des 502 de septembre) se tait.

- `host.health` expose `agent_components` (état, dernière activité à l'heure
  de Paris, silence, borne) et `stale_agent_components`. Un composant muet
  ajoute la raison `agent_components_stale` (dégradé, immédiat : la borne
  couvre déjà plusieurs échantillons).
- Tsunade : procédure connue `agent_components` → sonde `agent.vitals`
  (lecture des vitaux), confirmation déterministe sans IA. Aucun redémarrage
  proposé.
- Limite assumée : un Agent dont la boucle principale est entièrement figée
  cesse aussi de publier sa santé ; ce cas relève du lot 3.

Sandbox : `agent-component-stale`. La boucle d'administration cesse de battre,
un incident `host.health` s'ouvre, `agent.vitals` le confirme sans IA, puis il
se résout seul à la reprise. Agent 1.39.0 échoue
(`ModuleNotFoundError: ohana_agent.runtime.vitals`). Validation au moment du
commit : 30/30 scénarios, `--exercise-logs` et `--full-stack` PASS ; suite
Agent 1733 tests.

### Lot 2 — l'Agent observe Vision (en cours)

- **Démarrage découplé (Agent).** Le planificateur et la santé de l'hôte
  démarrent toujours. Un envoi de l'infrastructure refusé par Vision est
  retenté par le chemin de rafraîchissement (toutes les
  `infrastructure_retry_seconds`) sans arrêter les observations, y compris
  lors d'un changement de configuration.
- **Vitaux de Vision (Vision).** `GET /api/runtime/vitals`, sans cache :
  état, démarrage, dernière ingestion et silence d'ingestion en secondes,
  heures de Paris. La dernière ingestion est l'heure de réception par Vision
  et non l'heure de l'observation, qui peut être ancienne lors d'un rejeu de
  la file. Avant toute ingestion, le silence compte depuis le démarrage.
  Vision dépend désormais de `tzdata` (comme l'Agent) pour les heures de
  Paris sous Windows.
- **Sonde (Agent).** `runtime/vision_probe.py` interroge ces vitaux toutes
  les 60 s dans son propre fil (délai 5 s) : une réponse lente de Vision ne
  bloque jamais la boucle principale. Une mesure de plus de 3 intervalles
  est ignorée (état inconnu, aucune raison ajoutée).
- **Raisons `host.health`**, toutes après 3 échantillons, ce qui absorbe un
  redémarrage de déploiement :
  - `vision_http_unavailable` : critique. Vision est aussi la seule porte
    d'entrée de Shizune ; l'utilisateur est aveugle, d'où la notification.
    La livraison bloquée est alors imputée à Vision et non comptée comme
    composant muet de l'Agent.
  - `vision_ingestion_stale` : dégradé ; Vision répond mais n'a rien ingéré
    depuis plus de 5 minutes.
- **Tsunade.** Procédure connue `vision_http` / `vision_ingestion`, placée
  avant les autres → sonde `vision.status` (nouvelle mesure, délai 10 s).
  Aucune réparation au catalogue.
- **Notification d'escalade.** Vision arrêté par systemd ouvre d'abord un
  incident dégradé (`systemd_units_inactive`, immédiat) ; il ne devient
  critique qu'avec le silence HTTP confirmé. Shizune n'était notifié que
  d'un incident ouvert critique : une escalade dégradé → critique notifie
  désormais aussi, une fois.

État au moment de cette mise à jour : suite Vision 910 tests OK ; tests
ciblés Agent (vitaux et sonde, 17 tests) OK. Restent la suite Agent complète,
le lint, un scénario Sandbox (Vision arrêtée au démarrage de l'Agent, puis
retour) et la preuve d'échec sur Agent 1.39.0 / Vision 1.30.0.

## Critères de sortie

| Critère | Sandbox | Réel (Konoha) |
| --- | --- | --- |
| Agent expose un état vital exploitable | `agent-component-stale` (lot 1) | à valider après déploiement |
| Vision expose un état vital exploitable | à venir (lot 2) | à valider |
| Katsuyu expose un état vital exploitable | à venir (lot 4) | à valider |
| Shizune expose un état vital exploitable | à venir (lot 4) | à valider |
| La dernière activité repère un composant silencieusement figé | `agent-component-stale` | à valider |
| Une défaillance Ohana produit une observation exploitable | `agent-component-stale` ; Vision à venir | à valider |
| L'indisponibilité d'un composant n'empêche pas d'observer les autres | démarrage sans Vision (lot 2) | à valider |
| Pas de dépendance circulaire critique | lot 2 | à valider |
| Charge compatible avec INFRA-01 | à mesurer | à mesurer |
