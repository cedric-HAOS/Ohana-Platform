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
| 1 — Vitaux de l'Agent | dernière activité utile des composants internes critiques | commits Agent 96773aa, Platform 56538e9 présents dans les références locales origin/main ; non publié |
| 2 — L'Agent observe Vision | démarrage sans Vision, sonde HTTP et ingestion, notification d'escalade | développé et validé localement le 28 septembre ; non commis, non publié, validation réelle à faire |
| 3 — Vision observe l'Agent | « Agent silencieux » calculé par Vision avec sa propre horloge | développé et validé localement le 28 septembre ; non commis, non publié, validation réelle à faire |
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

### Lot 2 — l'Agent observe Vision (validé localement)

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
  Une réponse JSON qui n'est pas un objet est enregistrée en échec sans
  arrêter le fil ; la mesure suivante peut constater le retour de Vision.
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

Validation locale du 28 septembre 2026 :

- Agent : **1 742 tests PASS, 1 skipped** ; Vision : **910 tests PASS** ;
- lint et format Agent/Vision conformes ; nouveau scénario Sandbox conforme ;
- Sandbox : **31/31 PASS**, `--exercise-logs` PASS ;
- `--full-stack` PASS : worker HTTPS, modèle Ministral réel (525 tokens),
  résultat IA et parcours existants rendus dans Vision desktop/mobile,
  aucune erreur JavaScript ou HTTP serveur. Rapport local :
  `sandbox/runs/20260928-163800-33e2a106/report.json`.

Le nouveau scénario **`vision-startup-recovery`** démarre `ProductionAgent`
avec le port HTTP de Vision indisponible, puis démarre un vrai serveur
Vision local. Il vérifie le planificateur actif, la conservation dans la
file SQLite, l'incident confirmé par `vision.status` sans IA, une seule
notification critique pendant la panne, la synchronisation au retour,
la résolution du même incident et la présence effective dans la base Vision
de toutes les observations produites pendant la panne. Les vitaux HTTP
doivent ensuite indiquer une ingestion récente, datée à Paris.

Limites : métriques de l'hôte et transport APNs simulés, tâche du
planificateur de laboratoire, intervalles raccourcis. Aucun service de
Konoha n'a été arrêté. Le passage systemd dégradé → HTTP critique reste
couvert par le test ciblé de notification d'escalade.

Comparaison avec les tags de référence extraits localement :

- Agent **1.39.0** : le scénario échoue, module `runtime.vision_probe`
  absent. Un contrôle distinct de `ProductionAgent.start()` avec un vrai
  port HTTP indisponible confirme aussi `running=False` sur le tag, contre
  `running=True` avec le code actuel ;
- Vision **1.30.0**, Agent actuel : le scénario échoue sur la résolution et
  les vitaux HTTP, l'endpoint étant absent ; la livraison des observations
  fonctionne indépendamment.

Le développement local du lot 2 est terminé. Restent la publication,
le déploiement coordonné Agent/Vision et la validation réelle sur Konoha
(notification APNs/MQTT comprise). Ces opérations n'ont pas été effectuées.
Un Agent avec cette sonde considère un ancien Vision sans endpoint de
vitaux comme indisponible : prévoir Vision avant Agent au déploiement.

### Lot 3 — Vision observe l'Agent

`runtime/agent_presence.py` mesure le silence avec l'horloge **monotone de
Vision**, indépendamment des dates fournies par l'Agent, de l'horloge du
navigateur et d'une correction NTP. L'état est calculé à la lecture de
`GET /api/runtime/vitals`, dans le nouveau champ `agent` : aucun appel à
l'API Agent, aucune tâche de fond ni écriture SQLite supplémentaire.

- `waiting` : aucune ingestion depuis le démarrage de Vision, délai de
  grâce de 300 secondes ; ce n'est jamais un état sain ;
- `active` : une observation a été traitée depuis moins de 301 secondes ;
- `silent` : plus de 300 secondes sans ingestion, même si l'Agent n'a
  jamais livré d'observation ;
- `unknown` : runtime Vision non opérationnel.

Le champ contient aussi `last_received_at` et `generated_at` à l'heure de
Paris, `silence_seconds`, `max_silence_seconds=300` et `measured_by=vision`.
Une ingestion rejetée par le traitement ou un doublon rejoué prouve encore
une livraison : l'activité reprend, mais cela ne prouve pas que les mesures
contenues dans le message soient récentes, ni que tous les composants de
l'Agent fonctionnent. L'horodatage d'observation reste inchangé.

La remise à zéro des statistiques ne remet pas à zéro cette surveillance.
Au redémarrage de Vision, les observations restaurées de SQLite ne valent
pas nouvelle réception : nouvelle période `waiting`, puis `silent` sans
contact. La dernière réception de l'exécution précédente n'est pas persistée.

**Restitution immédiate, avant la section Ohana du lot 5 :** bandeau global
« Agent silencieux » avec dernière réception, impact sur la fraîcheur de
Konoha et invitation à vérifier l'Agent et sa liaison à Vision. La page Hôte
conserve ses mesures mais affiche « État actuel inconnu » plutôt que son
ancien état sain. Un contrôleur indépendant relit Vision toutes les 15 s,
même sans WebSocket entrant ; retour au premier plan et bouton Actualiser
relancent aussi la lecture. Délai de lecture borné à 5 s. Une erreur de
lecture Vision produit « Surveillance de l'Agent indisponible », jamais une
fausse attribution du silence à l'Agent.

Le bandeau disparaît à la reprise de livraison. Il s'agit d'un constat
extérieur : il ne distingue pas Agent figé, service arrêté ou liaison
interrompue. Aucun incident n'est demandé à Tsunade indisponible, aucun
redémarrage ni notification APNs n'est ajouté par Vision.

Validation du 28 septembre : **914 tests Vision PASS**, lint et format
conformes. Les nouveaux tests couvrent absence initiale, seuil, horodatage
Agent futur, correction de l'horloge civile, remise à zéro des statistiques,
reprise, doublon et redémarrage sur une base existante.

Sandbox **`agent-silent` PASS** : serveur Vision HTTP, SQLite et Chromium
réels, aucune API Agent configurée. Une page déjà ouverte passe de la santé
reçue à l'avertissement sans nouvelle observation ni événement WebSocket,
puis revient à la normale après une livraison. Bandeau global vérifié en
desktop et mobile, sans débordement horizontal ni erreur JavaScript ; erreur
de lecture Vision distincte du silence Agent. Seule l'horloge monotone du
serveur est avancée, le polling navigateur de 15 s est celui de production.
Rapport et captures : `sandbox/runs/20260928-164908-agent-silent/`.

Non-régression : **32/32 scénarios Sandbox PASS** et **full-stack PASS**
(worker HTTPS, inférence Ministral réelle, 551 tokens, parcours Vision et
Shizune existants, rendu desktop/mobile sans erreur JavaScript ou HTTP
serveur). Rapport : `sandbox/runs/20260928-164951-d94e6e46/report.json`.

Publication, déploiement et panne réelle contrôlée sur Konoha restent à faire.

## Critères de sortie

| Critère | Sandbox | Réel (Konoha) |
| --- | --- | --- |
| Agent expose un état vital exploitable | `agent-component-stale` (lot 1) | à valider après déploiement |
| Vision expose un état vital exploitable | `vision-startup-recovery` (lot 2) | à valider |
| Katsuyu expose un état vital exploitable | à venir (lot 4) | à valider |
| Shizune expose un état vital exploitable | à venir (lot 4) | à valider |
| La dernière activité repère un composant silencieusement figé | `agent-component-stale`, `agent-silent` (absence de livraison vue de Vision) | à valider |
| Une défaillance Ohana produit une observation exploitable | `agent-component-stale`, `vision-startup-recovery` | à valider |
| L'indisponibilité d'un composant n'empêche pas d'observer les autres | `vision-startup-recovery` : planificateur et santé actifs sans Vision | à valider |
| Pas de dépendance circulaire critique | `vision-startup-recovery` : incident et notification sans Vision, transport APNs simulé | à valider |
| Charge compatible avec INFRA-01 | à mesurer | à mesurer |
