# Phase 2 — Cycle complet incident → réparation supervisée

## Cadre initial — 25 septembre 2026

Phase démarrée après la clôture de la Phase 1 (10/10). Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.120, Agent 1.31.0,
Vision 1.23.0, Shizune 0.3.0.

Les validations de la Phase 1 ne sont pas rejouées. Elles ne se rouvrent que
sur une nouvelle preuve contradictoire.

## État des critères de sortie — 26 septembre 2026

**9 critères sur 10 démontrés en réel ; les 10 démontrés dans Sandbox.**

| Critère | Réel (Konoha) | Sandbox (Agent 1.33.0, Vision 1.24.0) |
| --- | --- | --- |
| Première réparation de référence de bout en bout | **acquis** (dnsmasq, 26 septembre) | **démontré** : dnsmasq proposé, autorisé depuis Vision, exécuté, vérifié, appris |
| Deuxième réparation différente, même mécanisme | **acquis** (Mosquitto, 25 septembre) | — |
| Cycle sans état ambigu | **acquis** : `refused`, report, `unverified`, `succeeded` | **démontré** : `expired`, `refused`, `failed`, `unverified`, reprise SQLite |
| Action non autorisée non exécutable | **acquis** : proposition reportée puis refusée jamais exécutée | **démontré** : proposition inconnue, expirée ou refusée jamais exécutée |
| Refus ou report conservé | **acquis** (refus Mosquitto, report dnsmasq) | **démontré** : report Vision, refus Shizune et Vision |
| Vérification réelle par Shikamaru | **acquis** | — |
| Échec explicite et exploitable | partiel : `unverified` explicite, mais sur une réparation réussie (chrony) | **démontré** : échec d'exécution et vérification non confirmée |
| Pas de répétition automatique après échec | **acquis** : rien de reproposé après `unverified` ni après refus | **démontré** : aucune nouvelle proposition après refus ou échec |
| Vision ou Shizune rendent l'action compréhensible | **acquis** | **démontré** dans Chromium : report, autorisation, refus et états sur la carte |
| Tsunade propriétaire de la décision finale | **acquis** : Tsunade propose, l'utilisateur décide, Shikamaru vérifie | **démontré** : Tsunade propose, l'utilisateur décide, Shikamaru vérifie |

Sandbox ne remplace pas la validation réelle : les critères restent ouverts ou
partiels tant qu'ils n'ont pas été exercés sur Konoha.

## Socle livré — Agent 1.31.0, Vision 1.23.0

- **Catalogue déclaratif** (`tsunade/repair_catalog.py`). Chaque réparation
  déclare le type et l'implémentation du service visé, la sonde qui confirme le
  symptôme, l'action, la cible, le risque, les conséquences et le résultat
  attendu. Tsunade ne propose une réparation qu'après un diagnostic
  `confirmed_by_probe` où cette sonde établit précisément le symptôme.
- **Correction de ciblage.** L'ancienne règle (« dns » dans le message →
  redémarrer dnsmasq) aurait visé le dnsmasq d'INFRA-01, qui assure le DHCP,
  pour une panne des AdGuard Home de ZWAVE-01 ou LINKY-01. Elle est supprimée.
- **Réparations du catalogue :**
  - `dnsmasq.restart` : service `dhcp` implémenté par dnsmasq, sonde
    `dhcp.status` avec `service_active=false`. Un pool DHCP plein ne déclenche
    pas de redémarrage ;
  - `mosquitto.restart` : service `mqtt` implémenté par Mosquitto, aller-retour
    `mqtt.status` en échec. L'add-on `core_mosquitto` est redémarré par le
    Supervisor avec l'accès `ha-01` déjà utilisé pour l'inspection.
- **Sûreté du cycle :**
  - une proposition devient `expired` si son incident est résolu ou si sa
    demande d'autorisation expire ;
  - une réparation exécutée que Shikamaru ne confirme pas dans les 15 minutes
    devient `unverified` ;
  - après un refus, une expiration ou un échec, Tsunade ne repropose pas de
    lui-même.
- **Corrélation entre incidents** (durcissement de la Phase 1). Un service
  déclare ses dépendances dans `metadata.depends_on`, modifiable dans Vision
  (« Dépend de »). Un symptôme dont le service amont a un incident actif y est
  rattaché, avec une décision déterministe `watch`, sans expertise Katsuyu.

## Validations réelles

### Réparation Mosquitto et corrélation — 25 septembre 2026 — VALIDÉE

- famille : Service (« Mosquitto indisponible », rejoué après la panne #3 de la
  Phase 1) ;
- Agent 1.31.0, Vision 1.23.0, Platform 1.0.120, déployés le jour même ;
- préparation : `mesure-puissance-3` (télémétrie de `sun-01`) déclare
  `depends_on: [mqtt]` dans Vision ;
- suivi en lecture seule : SQLite ouvert avec `mode=ro` et
  `PRAGMA query_only=ON`, sous le compte `ohana-agent`.

Déroulé, heure Europe/Paris :

| Heure | Événement |
| --- | --- |
| 14:51:56 | arrêt de l'add-on Mosquitto ; incident `mqtt.roundtrip` `b87ae7a5-1125-424a-9f37-9357f663fdc1` ouvert (`[Errno 111] Connection refused`), un `logs.health_check` pour `ha-01` |
| 14:52:00 | `mqtt.status : exécutée, résultat en échec` et `network.ping : exécutée, résultat sain` ; diagnostic `CONFIRMED` / `confirmed_by_probe`, décision `action_required`, sans IA |
| 14:52:01 | Tsunade propose de lui-même le redémarrage supervisé de l'add-on Mosquitto (`restart_addon` / `core_mosquitto`, risque faible) |
| 14:52:56 | la télémétrie de `sun-01` devient indisponible : incident `home_assistant.telemetry.freshness` `4a529782-fa2a-4782-9974-fd94fa02fec1` ouvert |
| 14:52:57 | rattachement à l'incident MQTT : `correlated_with_upstream`, niveau `PROBABLE`, décision `watch` ; l'incident MQTT reçoit « Symptôme aval rattaché » ; **aucun `ai.inference`** |
| 14:53:11 | autorisation depuis Vision, puis exécution : redémarrage accepté par le Supervisor alors que l'add-on était arrêté ; réparation `verifying` |
| 14:54:11 | `MQTT round trip succeeded for ha-01.ohana.lan in 23.152 ms.` ; réparation `succeeded` (« Shikamaru confirme que la capacité est redevenue saine. ») ; incident MQTT résolu |
| 14:57:57 | observation suivante de la télémétrie : `380.6 W`, incident `sun-01` résolu automatiquement |

Jobs distribués pendant l'essai : deux `logs.health_check` `SUCCEEDED`, aucun
`ai.inference`.

Acquis :

- la chaîne diagnostic → proposition → autorisation → exécution →
  vérification fonctionne en réel pour une réparation distante sur un add-on
  Home Assistant ;
- le jeton `ha-01` a les droits nécessaires et le Supervisor redémarre un
  add-on arrêté ;
- l'expertise IA évitable de la panne #3 (télémétrie `sun-01`) ne se produit
  plus.

Constats de durcissement, non bloquants :

- les événements d'un même incident mélangent UTC (ouverture, proposition,
  autorisation, résolution) et Europe/Paris (investigations, diagnostic,
  rattachement) ;
- « Contrôle des journaux par Katsuyu : KO » s'affiche alors que les deux jobs
  sont `SUCCEEDED` : même ambiguïté entre exécution et résultat que l'ancien
  `mqtt.status: OK` ;
- un second `logs.health_check` est créé au moment de la résolution MQTT ; son
  déclencheur reste à identifier ;
- Vision ne fixe pas `Cache-Control` sur ses fichiers statiques : après la mise
  à jour, le champ « Dépend de » est resté vide jusqu'au vidage du cache du
  navigateur.

### Chrony, refus Mosquitto, dnsmasq — 26 septembre 2026

Platform 1.0.123 (Agent 1.34.0, Vision 1.25.0) et Installer 1.15.0 déployés ;
`.\sandbox\run.ps1 post-deploy agent 1.34.0 --exercise-logs` PASS. Pannes
provoquées par l'utilisateur ; décisions prises dans Vision
(`http://192.168.1.10:8000/ui/`). En production, le plugin NTP observe toutes
les heures et le plugin DHCP toutes les 30 minutes.

**Chrony — chemin nominal, vérification manquée.**

| Heure | Événement |
| --- | --- |
| 16:07:54 | arrêt de `chrony.service` |
| 16:25:42 | cycle NTP : incident ouvert (`timed out`) |
| 16:25:57 | `ntp.status` et `chrony.status` : exécutées, résultat en échec ; diagnostic déterministe, confiance 100 %, sans IA |
| 16:25:58 | Tsunade propose le redémarrage supervisé de chrony (risque faible) |
| 16:28:24 | autorisation depuis Vision, exécution ; `ohana-chrony-restart.service` relance chrony (actif à 16:28:25) |
| 16:43:41 | réparation `unverified` : « Aucune observation Shikamaru n'a confirmé le résultat dans les 15 minutes suivant l'exécution. La réparation n'est pas répétée automatiquement. » |
| 17:25:39 | cycle NTP : incident résolu (décalage 0,068 ms) ; la réparation reste `unverified` |

**Refus depuis Vision — Mosquitto.** Arrêt de l'add-on ; incident
`mqtt.roundtrip` ouvert à 16:53:05, proposition `core_mosquitto` à 16:53:31,
refus confirmé dans Vision par l'utilisateur. État « Refusée, aucune action
exécutée » ; pendant 50 minutes de cycles MQTT (toutes les 2 minutes), rien
n'est exécuté ni reproposé. Seules restent « Actualiser l'analyse » et
« Demander la réparation connue ».

**Réparation de référence — dnsmasq.**

| Heure | Événement |
| --- | --- |
| 17:25:42 | arrêt de `dnsmasq.service` ; incidents DNS et Z-Wave JS « Name or service not known » dans la minute |
| 17:26:03 | cycle DHCP : incident `DHCP service is not active: inactive` |
| 17:26:11 | diagnostic déterministe, confiance 100 % ; proposition du redémarrage supervisé de dnsmasq |
| 17:28:26 | « Plus tard » depuis Vision : reportée jusqu'à 18:28:26, rien n'est exécuté |
| 17:42:24 | autorisation depuis Vision ; dnsmasq actif à 17:42:25 |
| 17:56:03 | cycle DHCP : 8 baux actifs (8 % du pool) ; réparation « Réussie et confirmée par Shikamaru », incident résolu |

L'autorisation a été placée à 17:42 pour que le cycle DHCP suivant tombe dans
le délai de vérification ; DHCP et DNS local ont été coupés 17 minutes.

Acquis :

- première réparation de référence dnsmasq de bout en bout en réel, report
  compris ;
- refus humain conservé, jamais exécuté, sans nouvelle proposition ;
- `unverified` explicite et non répété ; résolution ultérieure sans réécriture
  en succès ;
- `chrony.restart` exécuté en réel par l'assistant de l'Installer.

Défauts constatés :

- **vérification liée à la cadence planifiée.** Shikamaru attend l'observation
  suivante, mais le délai de vérification est plafonné à 30 minutes et vaut
  15 minutes avec une seule observation. Avec un NTP horaire, une réparation
  chrony réussie finit toujours `unverified` ; pour dnsmasq, tout dépend de
  l'heure d'autorisation. Une sonde de vérification immédiate après
  l'exécution est nécessaire ; « Tester maintenant » ne publie pas
  d'observation ;
- **cause amont DNS non rattachée.** L'arrêt de dnsmasq ouvre des incidents DNS,
  Z-Wave JS, MQTT et télémétrie « Name or service not known », rattachés à
  aucun incident amont. dnsmasq n'est identifié qu'au cycle DHCP suivant ;
- la carte d'incident chrony est titrée « timed out » au lieu du service ;
- la page Services affiche Chrony « Sain » pendant l'incident critique ;
- le bandeau « Réparation autorisée ; vérification Shikamaru en attente »
  reste affiché après le passage en `unverified` ;
- le dossier attribue à « Analyse Katsuyu » une conclusion déterministe ;
- `GET /api/administration/tsunade/incidents?state=all` renvoie par moments 502
  via Vision.

## Qualification Sandbox — 25 septembre 2026

Agent 1.33.0 ajoute le refus et le report depuis l'API d'administration ;
Vision 1.24.0 ajoute « Refuser », « Plus tard » et l'état de la dernière
réparation sur la carte d'incident.

- `supervised-repair-cycle` (24 vérifications) : services Agent, bases SQLite
  et exécuteur dnsmasq réels, demande de redémarrage écrite dans un fichier
  temporaire. Parcours : proposition automatique après diagnostic confirmé,
  report depuis Vision, reprise SQLite, autorisation Vision, vérification
  Shikamaru, expérience apprise ; refus depuis Shizune sans nouvelle
  proposition ; échec d'exécution explicite ; vérification non confirmée
  (`unverified`, délai réduit à une seconde) jamais réécrite en succès ;
  proposition expirée à la résolution.
- `--full-stack` : après le cycle IA réel, le navigateur reporte, autorise
  puis refuse des propositions dnsmasq dans Vision, jusqu'à l'API HTTP de
  l'Agent, l'exécuteur dnsmasq et la vérification Shikamaru ; le refus passe
  par la confirmation du navigateur.
- Suite complète : 14 scénarios sur 14, exercice des journaux et
  `--full-stack` PASS.

## Catalogue enrichi — Agent 1.34.0, Installer 1.15.0

Même mécanisme que Mosquitto : proposition par Tsunade après un diagnostic
confirmé, autorisation humaine, vérification par Shikamaru, aucune nouvelle
proposition automatique après un refus ou un échec.

| Réparation | Service | Preuve exigée | Action | Risque |
| --- | --- | --- | --- | --- |
| `teleinfo2mqtt.restart` | `tic-linky` (LINKY-01) | Supervisor : add-on `stopped` ou `error` (`confirmed_by_supervisor`) | redémarrage de l'add-on par le Supervisor | faible |
| `zwave_js.restart` | `zwave` (ZWAVE-01) | sonde `zwave.status` en échec, add-on listé par le Supervisor | redémarrage de l'add-on par le Supervisor | moyen |
| `chrony.restart` | `chrony` (INFRA-01) | sonde `ntp.status` et sonde locale `chrony.status` : chrony inactif | demande écrite à `ohana-chrony-restart.path` | faible |

- La cible d'un add-on est le slug listé par la dernière inspection du
  Supervisor du nœud (`6fc079ce_teleinfo2mqtt_ohana`, `a0d7b954_zwavejs2mqtt`
  sur Konoha) ; sans inspection disponible, rien n'est proposé.
- Un add-on teleinfo2mqtt démarré alors que les trames manquent, ou un chrony
  actif dont les sources amont échouent, ne déclenche aucune réparation.
- L'assistant chrony est une unité de chemin et un service `oneshot` dont la
  seule commande est `systemctl restart chrony.service` ; le contenu de la
  demande n'est pas lu. Sans assistant installé, l'exécution échoue
  explicitement.
- Sandbox : scénario `catalogue-repair-cycle` (15 vérifications, exécuteurs
  Agent réels, Supervisor simulé) ; échoue sur Agent 1.33.0. Suite complète
  16/16, exercice des journaux et `--full-stack` PASS.

## Prochaines validations

1. Corriger la vérification : sonde immédiate de la capacité après
   l'exécution, puis rejouer chrony en réel jusqu'à `succeeded`.
2. Échec réel exploitable : `unverified` sur une réparation réellement
   inefficace, ou `failed` sur une exécution refusée.
3. Réparations `teleinfo2mqtt.restart` et `zwave_js.restart` : arrêt de
   l'add-on dans Home Assistant par l'utilisateur, autorisation depuis Vision.
