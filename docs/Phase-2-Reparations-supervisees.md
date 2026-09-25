# Phase 2 — Cycle complet incident → réparation supervisée

## Cadre initial — 25 septembre 2026

Phase démarrée après la clôture de la Phase 1 (10/10). Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.120, Agent 1.31.0,
Vision 1.23.0, Shizune 0.3.0.

Les validations de la Phase 1 ne sont pas rejouées. Elles ne se rouvrent que
sur une nouvelle preuve contradictoire.

## État des critères de sortie — 25 septembre 2026

**3 critères sur 10 démontrés en réel.**

| Critère | État | Preuve |
| --- | --- | --- |
| Première réparation de référence de bout en bout | ouvert | dnsmasq (`dnsmasq.restart`) couvert par les tests, pas encore exercé sur Konoha |
| Deuxième réparation différente, même mécanisme | **acquis** | Mosquitto, 25 septembre (ci-dessous) |
| Cycle sans état ambigu | partiel | chemin nominal réel ; `expired`, `refused` et `unverified` couverts par les tests seulement |
| Action non autorisée non exécutable | partiel | tests (proposition expirée, incident résolu, refus) ; pas d'essai réel |
| Refus ou report conservé | ouvert | à exercer depuis Vision ou Shizune |
| Vérification réelle par Shikamaru | **acquis** | aller-retour MQTT observé après le redémarrage |
| Échec explicite et exploitable | ouvert | refus Supervisor et `unverified` testés, pas d'échec réel |
| Pas de répétition automatique après échec | partiel | tests ; à confirmer avec un échec réel |
| Vision ou Shizune rendent l'action compréhensible | **acquis** | proposition, risque, conséquences et résultat lus et autorisés dans Vision |
| Tsunade propriétaire de la décision finale | partiel | Tsunade propose et vérifie ; à confirmer sur refus et échec |

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

## Prochaines validations

1. Réparation de référence dnsmasq en réel : arrêt contrôlé de dnsmasq sur
   INFRA-01, en tenant compte de l'interruption du DHCP pendant l'essai.
2. Refus, puis report, d'une réparation proposée, depuis Vision et depuis
   Shizune : l'état reste `refused` ou en attente, et rien n'est exécuté.
3. Échec réel : réparation refusée par le Supervisor, ou non confirmée par
   Shikamaru, pour démontrer un état explicite (`failed` ou `unverified`) et
   l'absence de nouvelle proposition automatique.
