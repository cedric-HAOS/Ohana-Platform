# Phase 4 — Maintenance préventive

## Cadre — 28 septembre 2026

Phase démarrée après la clôture de la Phase 3. Référence :
[roadmap commune](../ROADMAP.md).

Objectif : signaler quelques dérives réellement utiles avant qu'elles ne
deviennent des incidents, avec des règles simples et explicables, sans jamais
réparer.

### Choix de conception

- **Les règles vivent dans Tsunade (Agent).** Vision ne conserve que 2 jours
  d'observations : trop court pour une tendance sur une semaine. Tsunade reçoit
  déjà la santé de l'hôte (`HostHealthObserved`) et possède l'historique des
  incidents.
- **Historique compact.** Une ligne par jour de Paris, nœud et mesure
  (`tsunade_trend_daily` : minimum, maximum, dernière valeur, nombre
  d'échantillons), écrite toutes les 15 minutes et non à chaque échantillon,
  à cause de la carte SD d'INFRA-01. Les démarrages et redémarrages sont des
  événements datés (`tsunade_trend_events`). Purge au-delà de 90 jours.
- **Aucune action.** La maintenance préventive n'ouvre pas d'incident, ne crée
  ni proposition ni demande, et ne déclenche aucune réparation.
- **Sans Katsuyu ni IA.** Les trois règles sont évaluées à la lecture, en
  quelques requêtes SQLite. Katsuyu ne sert qu'au rattrapage de l'historique
  (lot 3), jamais à l'évaluation.

### Les trois tendances (fenêtre de 7 jours)

| Règle | Données | Seuil |
| --- | --- | --- |
| Croissance du disque | maximum journalier de `disk_percent` (santé de l'hôte) | au moins 4 jours mesurés ; hausse **médiane** d'au moins 0,5 point par jour ; au moins 3 hausses d'un jour sur l'autre ; et occupation ≥ 70 % ou 90 % atteint sous 30 jours. Intervention à prévoir si 90 % est atteint sous 7 jours. |
| Redémarrages répétés | démarrages de l'hôte (déduits de `host_uptime_seconds`) et redémarrages automatiques de l'Agent (hausse de `NRestarts` systemd) | au moins 2 sur 7 jours. Un redémarrage demandé (mise à jour, `systemctl restart`) n'est pas compté. |
| Interruptions réseau répétées | incidents `network.reachable` de Tsunade | au moins 3 pour le même équipement sur 7 jours |

La médiane plutôt qu'une pente : une mise à jour apt ou un gros fichier est un
saut unique, qui ne déplace pas la médiane des variations journalières.
Constat de conception : avec une droite des moindres carrés, la série
71,0 → 71,1 → 71,2 → 74,5 → 74,6 → 74,6 → 74,7 % donnait +0,7 point/jour et
était signalée à tort.

Moins de 4 jours de mesures : « Historique insuffisant », jamais un « stable »
deviné.

### Synthèse

`GET /v1/preventive` (opération `preventive.read`), relayé par Vision sur
`/api/administration/tsunade/preventive` :

```text
Konoha est stable.

À surveiller :
- INFRA-01 : espace disque en hausse depuis 5 jours.

Aucune intervention nécessaire.
```

Le titre devient « N incident(s) en cours, suivi(s) par Tsunade. » quand des
incidents sont actifs : la maintenance préventive ne prétend pas que Konoha est
stable pendant un incident.

- **Vision** (page Tsunade, section « Maintenance préventive ») : la synthèse,
  le détail de chaque dérive, et les règles appliquées avec leur état (Normal,
  À surveiller, Historique insuffisant) et les faits par nœud.
- **Shizune** (carte « Prévention » de l'essentiel) : uniquement les titres à
  surveiller et la conclusion, via le résumé compagnon existant.

## Lots

- **Lot 1 — règles et synthèse (Agent).** Agent 6ef15a7, 9136d93, 154611f,
  78e60f3.
- **Lot 2 — Vision et Shizune.** Vision 4bbf4e8, carte Shizune.
- **Lot 3 — rattrapage de l'historique par Katsuyu.** Agent 6373ab0,
  Katsuyu add0330 et 45d1551, Vision 023eaf3 (choix de l'utilisateur du
  28 septembre).

Sandbox : `preventive-trends` (semaine normale, trois dérives, redémarrage de
l'Agent, lectures sans effet), `preventive-backfill` (vrai gestionnaire
Katsuyu, Home Assistant simulé) et `--full-stack` (section Vision, carte
Shizune, rattrapage demandé depuis Vision et exécuté par le vrai worker
Katsuyu en HTTPS contre un Home Assistant WebSocket local).

### Lot 3 — rattrapage de l'historique

La règle du disque demande 4 jours mesurés ; l'Agent ne mesure que depuis son
déploiement. Home Assistant (HA-01) conserve les statistiques horaires à long
terme du capteur MQTT `ohana_host_disk_usage` (`state_class: measurement`),
publié par l'Agent depuis des mois : ce sont des données déjà disponibles.

- Travail Katsuyu `trends.history_backfill` : descripteur lié au travail
  (`GET /v1/jobs/{id}/history-source/ha-01`, même cible HAOS et même jeton
  que les sources de journaux), registre des entités pour retrouver
  l'`entity_id` à partir de l'`unique_id`, puis jusqu'à 31 jours de
  statistiques horaires (`recorder/statistics_during_period`). Les lignes
  horaires restent sur le PC ; seul un jour de Paris par ligne revient
  (minimum, maximum, dernière moyenne, heures).
- Tsunade enregistre ces jours avec la source `home_assistant` par
  `INSERT OR IGNORE` : un jour mesuré par l'Agent et le jour en cours ne sont
  jamais remplacés.
- Déclenchement : tâche toutes les 6 h (5 min après le démarrage), seulement
  si un jour passé de la fenêtre de 7 jours manque et si aucune demande n'a
  eu lieu depuis 24 h ; bouton « Rattraper l'historique avec Katsuyu » dans
  Vision (`POST /v1/preventive/backfill`).
- Katsuyu absent ou endormi : le travail attend jusqu'à 12 h ; les contrôles
  simples répondent avec ce que l'Agent a mesuré (« Historique insuffisant »
  tant qu'il manque des jours).
- Compatibilité : un Agent refuse l'enregistrement complet d'un worker qui
  déclare un type inconnu. Katsuyu se réenregistre désormais sans les types
  que l'Agent nomme ; déployer l'Agent avant Katsuyu reste l'ordre normal.

## Critères de sortie

| Critère | Sandbox | Réel (Konoha) |
| --- | --- | --- |
| Au moins trois tendances simples détectées de manière reproductible | `preventive-trends` : disque, redémarrages, réseau ; même verdict après redémarrage de l'Agent | à valider après déploiement |
| Une évolution normale n'est pas transformée en anomalie | hausse lente, saut unique au-dessus de 70 % | à valider |
| Règles ou seuils explicables | chaque règle est énoncée avec son seuil et ses preuves | à valider |
| Données déjà disponibles privilégiées | santé de l'hôte et incidents existants | acquis par conception |
| Traitement historique lourd déportable vers Katsuyu | `preventive-backfill`, `--full-stack` : 31 jours de statistiques horaires lus et agrégés par Katsuyu | à valider (HA-01 réel) |
| Indisponibilité de Katsuyu sans effet sur les contrôles simples | Agent sans file Katsuyu ; travail de rattrapage en attente | à valider |
| Synthèse courte dans Shizune | carte « Prévention » (`--full-stack`) | à valider |
| Détail dans Vision | section « Maintenance préventive » (`--full-stack`) | à valider |
| Situation stable : « aucune intervention nécessaire » | semaine normale | à valider |
| Aucune réparation déclenchée par la seule maintenance préventive | aucune ligne d'incident, de réparation ou de demande créée | à valider |

### Données réelles au démarrage

Lecture seule du 28 septembre (historique des incidents) : sur les 7 derniers
jours, aucun équipement n'atteint 3 interruptions réseau (SUN-01 : 1,
SHE-04 : 2). ESP-02 aurait été signalé début septembre (3 interruptions du
5 au 7 septembre). L'Agent ne mesure le disque que depuis son déploiement ;
le rattrapage Katsuyu doit reconstruire les jours précédents depuis HA-01 au
premier passage du worker, sans attendre 4 jours.
