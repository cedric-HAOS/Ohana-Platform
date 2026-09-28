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
  quelques requêtes SQLite. Katsuyu reste réservé à un traitement historique
  lourd (lot 3).

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

- **Lot 1 — règles et synthèse (Agent).** Agent 6ef15a7, 9136d93, 154611f.
- **Lot 2 — Vision et Shizune.** Section Vision et carte Shizune.
- **Lot 3 — traitement historique déporté vers Katsuyu.** À définir.

Sandbox : scénario `preventive-trends` (semaine normale, trois dérives,
redémarrage de l'Agent, lectures sans effet) et `--full-stack` (section
Vision dans Chromium, carte Shizune avec le vrai résumé de l'Agent).

## Critères de sortie

| Critère | Sandbox | Réel (Konoha) |
| --- | --- | --- |
| Au moins trois tendances simples détectées de manière reproductible | `preventive-trends` : disque, redémarrages, réseau ; même verdict après redémarrage de l'Agent | à valider après déploiement |
| Une évolution normale n'est pas transformée en anomalie | hausse lente, saut unique au-dessus de 70 % | à valider |
| Règles ou seuils explicables | chaque règle est énoncée avec son seuil et ses preuves | à valider |
| Données déjà disponibles privilégiées | santé de l'hôte et incidents existants | acquis par conception |
| Traitement historique lourd déportable vers Katsuyu | — | lot 3 |
| Indisponibilité de Katsuyu sans effet sur les contrôles simples | Agent sans file Katsuyu | à valider |
| Synthèse courte dans Shizune | carte « Prévention » (`--full-stack`) | à valider |
| Détail dans Vision | section « Maintenance préventive » (`--full-stack`) | à valider |
| Situation stable : « aucune intervention nécessaire » | semaine normale | à valider |
| Aucune réparation déclenchée par la seule maintenance préventive | aucune ligne d'incident, de réparation ou de demande créée | à valider |

### Données réelles au démarrage

Lecture seule du 28 septembre (historique des incidents) : sur les 7 derniers
jours, aucun équipement n'atteint 3 interruptions réseau (SUN-01 : 1,
SHE-04 : 2). ESP-02 aurait été signalé début septembre (3 interruptions du
5 au 7 septembre). L'historique du disque
commence au déploiement : 4 jours sont nécessaires avant la première
évaluation.
