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

## Déploiement et premiers constats réels — 28 septembre 2026

Publiées le 28 septembre à la demande de l'utilisateur : Agent 1.39.0,
Vision 1.30.0, Katsuyu 0.9.0, Shizune 0.4.0, Platform 1.0.132. Agent démarré
à 15:05:02 sur INFRA-01.

| Étape | Heure |
| --- | --- |
| Katsuyu 0.9.0 enregistré avec `trends.history_backfill` | 15:09:33 |
| Rattrapage demandé automatiquement (tâche 5 min après le démarrage) | 15:10:29 |
| Rattrapage terminé par Katsuyu (Bubule) | 15:10:30 |

- Katsuyu a lu dans HA-01 **720 lignes horaires sur 30 jours** (29 août →
  28 septembre) et renvoyé 30 jours. Le capteur réel est
  `sensor.ohana_host_utilisation_disque_racine` et non
  `sensor.ohana_host_disk_usage` : la recherche par `unique_id` dans le
  registre des entités était nécessaire.
- 6 jours reconstruits dans la fenêtre, le jour en cours mesuré par l'Agent.
  Disque d'INFRA-01 entre 24,2 et 25,6 % sur 30 jours, légère baisse le 26 :
  médiane 0 point par jour, règle « Normal ». Aucun redémarrage sur 7 jours ;
  SHE-04 : 2 interruptions réseau (seuil 3).
- Synthèse réelle : « 4 incidents en cours, suivis par Tsunade. / Aucune
  dérive détectée. / Aucune intervention nécessaire. » Les 4 incidents sont
  les contrôles de journaux déjà ouverts (ZWAVE-01, INFRA-01, HA-01,
  LINKY-01) ; la maintenance préventive n'en a créé aucun.
- Vision : section, règles, faits par nœud et état du rattrapage conformes.
  Journal de l'Agent sans erreur ni échec de livraison vers Vision.
- Défaut mineur constaté : le pied de page de Vision affichait encore
  Shizune v0.3.0 (cache du navigateur) alors que 0.4.0 est servie. Corrigé
  localement (Vision b366997), pour la prochaine publication.

### Dérive réelle provoquée et Katsuyu arrêté — 28 septembre

SHE-04 avait 2 interruptions réseau sur 7 jours (22 septembre). Une coupure
contrôlée (prise débranchée par l'utilisateur) devait faire passer la règle à
« À surveiller ».

| Étape | Heure |
| --- | --- |
| SHE-04 débranché ; premier contrôle en échec (1/3, contrôle toutes les 6 min) | 15:37:22 |
| Incident `network.reachable` ouvert (3/3) | 15:49:23 |
| Synthèse : « À surveiller : SHE-04 : 3 interruptions réseau en 7 jours. » | 15:49 |
| Katsuyu arrêté sur Bubule ; worker indisponible (dernier contact) | 15:50:36 |
| Rattrapage demandé depuis Vision : travail en attente de Katsuyu | 15:51:27 |
| Synthèse recalculée sans Katsuyu, SHE-04 toujours signalé | 15:52:27 |
| Katsuyu redémarré : rattrapage exécuté seul (30 jours lus) | 15:53:27 |
| SHE-04 rebranché, incident résolu | 15:55:22 |

- La synthèse est restée « Aucune intervention nécessaire. » ; aucune
  réparation proposée sur l'incident SHE-04, aucune demande créée.
- Vision : « en attente de Katsuyu », bouton désactivé pendant l'attente,
  détail « la plus longue 1 h 06, une toujours en cours » puis sans « en
  cours » après la résolution. Aucun réveil Wake-on-LAN tenté.
- Le second rattrapage n'a rien remplacé : 6 jours reconstruits, 7 jours
  lus par la règle du disque, comme après le premier.
- Shizune : carte « Prévention » affichée sur l'iPhone de l'utilisateur.

## Critères de sortie

| Critère | Sandbox | Réel (Konoha) |
| --- | --- | --- |
| Au moins trois tendances simples détectées de manière reproductible | `preventive-trends` : disque, redémarrages, réseau ; même verdict après redémarrage de l'Agent | **partiel** : interruptions réseau détectées en réel (SHE-04, 15:49) ; disque et redémarrages démontrés en Sandbox seulement |
| Une évolution normale n'est pas transformée en anomalie | hausse lente, saut unique au-dessus de 70 % | **acquis** : 30 jours réels de disque (baisse du 26 incluse) « Normal » |
| Règles ou seuils explicables | chaque règle est énoncée avec son seuil et ses preuves | **acquis** : règles et faits par nœud affichés dans Vision |
| Données déjà disponibles privilégiées | santé de l'hôte et incidents existants | **acquis** : santé de l'hôte, incidents, statistiques HA-01 existantes |
| Traitement historique lourd déportable vers Katsuyu | `preventive-backfill`, `--full-stack` : 31 jours de statistiques horaires lus et agrégés par Katsuyu | **acquis** : 720 lignes de HA-01 agrégées par Katsuyu à 15:10 |
| Indisponibilité de Katsuyu sans effet sur les contrôles simples | Agent sans file Katsuyu ; travail de rattrapage en attente | **acquis** : Katsuyu arrêté, synthèse et SHE-04 toujours fournis, travail repris au retour |
| Synthèse courte dans Shizune | carte « Prévention » (`--full-stack`) | **acquis** : carte vue sur l'iPhone |
| Détail dans Vision | section « Maintenance préventive » (`--full-stack`) | **acquis** |
| Situation stable : « aucune intervention nécessaire » | semaine normale | **acquis** |
| Aucune réparation déclenchée par la seule maintenance préventive | aucune ligne d'incident, de réparation ou de demande créée | **acquis** : SHE-04 « À surveiller » sans réparation ni demande |

### Données réelles au démarrage

Lecture seule du 28 septembre (historique des incidents) : sur les 7 derniers
jours, aucun équipement n'atteint 3 interruptions réseau (SUN-01 : 1,
SHE-04 : 2). ESP-02 aurait été signalé début septembre (3 interruptions du
5 au 7 septembre). L'Agent ne mesure le disque que depuis son déploiement ;
le rattrapage Katsuyu doit reconstruire les jours précédents depuis HA-01 au
premier passage du worker, sans attendre 4 jours.
