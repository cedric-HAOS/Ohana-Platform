# Phase 1 — Stabilisation de Tsunade

## État au 15 septembre 2026

Phase démarrée, validation opérationnelle encore partielle. Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.100, Agent 1.29.0, Katsuyu 0.8.7.

Première campagne : tests locaux et consultation SSH en lecture seule sur INFRA-01
à partir de 13 h 58, heure Europe/Paris. Les bases SQLite ont été ouvertes avec
`mode=ro` et `PRAGMA query_only=ON`. Aucun incident provoqué, job relancé,
service redémarré ou changement déployé pendant cette campagne.

## Conclusion et priorités

### Suite de campagne — correction locale du 15 septembre

La vérification suivante précise les premiers constats :

- Le worker annonce **Katsuyu 0.8.7**, dernière présence lue à 14:10:59.
  Cette version contient déjà la régénération unique des sorties IA invalides
  et masque leur contenu dans l'erreur finale. Ses **10 tests IA passent**.
  L'erreur de 05:04 ne démontre donc pas un défaut persistant du runtime actuel ;
  la version exécutant ce job historique n'a pas été établie.
- Les deux réévaluations de 09:22 reçoivent des preuves JSON valides et les
  inspections Supervisor. Aucun tronquage JSON n'a été constaté dans ces cas.
- INFRA-01 : recherche `mqtt`, fenêtre 07:20:59–09:20:59, **58 lignes
  correspondantes, zéro anomalie, résultat OK, non tronqué**.
- LINKY-01 : recherche `serial`, fenêtre 07:21:00–09:21:00, **51 lignes
  correspondantes, zéro anomalie, résultat OK, non tronqué**.
- La construction de la réévaluation remplaçait les anomalies initiales par
  le résultat ciblé. Avec zéro anomalie nouvelle, `logs.analysis` disparaissait ;
  seul le résumé historique de l'incident restait, sans les détails initiaux.

**Correction Agent locale, non publiée et non déployée :** conserver les anomalies
initiales dans `logs.analysis`, séparément de `investigation.followup`. La question
explique que les occurrences historiques ne prouvent pas une persistance actuelle
et que les lignes correspondant au filtre ne sont pas un nombre d'anomalies.
Elle demande de comparer les fenêtres, le périmètre et la troncature éventuelle.

Validation : **41 tests Agent réussis**, couvrant expertise, suivis et cycle des
journaux, dont trois nouveaux cas de réévaluation (aucune correspondance,
correspondances sans anomalie, anomalie avec troncature). Ruff et `git diff --check`
passent. Le contrat de jobs et le nombre de cycles autorisés restent inchangés.

Cette correction s'applique aux nouvelles réévaluations construites après mise
à jour. Les résultats et intentions de réévaluation déjà persistés restent tels
qu'enregistrés ; aucun ancien cycle n'a été rouvert pour cette validation.
L'amélioration des conclusions d'un modèle réel reste à mesurer après déploiement
autorisé, sur une nouvelle observation pertinente. La confusion du libellé
Home Assistant / INFRA-01 reste à examiner séparément.

### Constats initiaux et suites à donner

1. **Fiabiliser la sortie IA de HA-01.** Le job
   `47700034-cb4d-4c8c-a8ff-8f611e751efb`, terminé le 15 septembre à 05:04:26,
   a échoué sur `findings.1.evidence` : dépassement de la limite de 500 caractères.
   Tsunade a conservé une conclusion d'échec et une décision `watch`.
   Le correctif existe déjà dans Katsuyu 0.8.7 et a été retesté ci-dessus ;
   confirmer son comportement lors d'une future exécution réelle.
2. **Vérifier l'exploitation des preuves complémentaires.** Les réévaluations
   INFRA-01 et LINKY-01 de 09:22–09:23 restent en `investigate`, avec un verdict IA
   `KO` et un statut épistémique `hypothesis`. Elles demandent encore des détails
   de journaux malgré les collectes terminées. Examiner le contenu effectivement
   transmis, sa fraîcheur et sa pertinence avant d'ajouter une nouvelle collecte.
3. **Clarifier l'attribution des incidents de journaux.** L'incident INFRA-01 porte
   `service_id=home-assistant` ; la conclusion IA parle donc de Home Assistant sur
   INFRA-01. Vérifier la provenance et le libellé : ce constat ne prouve pas que
   Home Assistant y est hébergé ni qu'il est indisponible.

## Référence observée en production

- Version installée d'Agent confirmée par les métadonnées Python : **1.29.0**.
- Agent et Vision : `active/running` depuis le 15 septembre à 09:17:47 ;
  `NRestarts=0` lors du relevé. Ce compteur ne démontre pas l'absence de tout arrêt passé.
- Quatre incidents actifs `logs.health` : HA-01, INFRA-01, LINKY-01 et ZWAVE-01.
  Dernière observation de ces incidents : 05:03:44, et non l'heure de consultation.
- À 05:03:45, ZWAVE-01 reçoit une décision déterministe `watch`.
- Deux collectes `logs.investigate` et leurs réévaluations IA de 09:20–09:23
  sont `SUCCEEDED`, avec `completion_processed=1` et des suivis `completed`.
- Aucune tâche `QUEUED` ou `RUNNING` lors du relevé. Cela ne suffit pas à
  valider l'absence de relance lors de prochaines observations ou après redémarrage.
- Les observations récentes de `mqtt.roundtrip`, `teleinformation.freshness`
  et `zwave.status` sont `healthy`. Elles ne ferment pas à elles seules un incident
  de journaux, dont la fenêtre et les critères sont différents.

## Preuves des investigations existantes

Sources : événements `tsunade_incident_events` et tables de jobs/suivis dans
`/var/lib/ohana-agent/distributed-jobs.db`. Les journaux et configurations bruts
ne sont pas recopiés dans ce rapport.

| Cible / contrôle | Preuve observée | Limite / prochaine validation |
| --- | --- | --- |
| INFRA-01 | Snapshot du 15/09 à 09:21:39 ; CPU 12,9 %, mémoire 44,3 %, disque 25,4 %, aucune unité failed/inactive | Mesures historiques ; comparer au diagnostic et à une anomalie réelle |
| LINKY-01 | Snapshot à 09:22:00 ; DNS réussi ; Supervisor accessible ; teleinfo2mqtt `started`, version 9.0.6-ohana.2 ; matériel disponible | Fonctionnement série et pertinence du diagnostic encore à vérifier |
| HA-01 / Mosquitto | Inspection associée au suivi INFRA-01 ; Supervisor par GET authentifié ; Mosquitto `started`, version 7.1.1 ; TCP 1883 réussi | Ne valide pas le cycle complet propre à l'incident HA-01 |
| ZWAVE-01 | Résolution DNS et TCP 3000 réussis dans les snapshots ; observation `zwave.status` saine | Investigation Supervisor et scénario de panne encore à valider |
| DNS | Résolution des hôtes configurés et connexion TCP 53 réussies | Un port TCP ouvert ne remplace pas une requête DNS fonctionnelle |
| HTTP | Pas de réponse HTTP dans les deux snapshots examinés | Exercer la sonde HTTP et distinguer 401/403 d'une panne |
| Secrets | Tests locaux de filtrage réussis ; export de cette campagne limité aux champs utiles | Audit complet du trajet preuve → prompt → résultat → erreur → interface restant |

Incidents utilisés :

| Cible | Identifiant |
| --- | --- |
| HA-01 | `c5bf1f49-0b0e-4e4a-985c-24631c0f69a8` |
| INFRA-01 | `dea74d31-6a14-4a17-83c8-f48ef94928e0` |
| LINKY-01 | `a4b953bd-4dde-416e-9e36-df3e4e6f6f29` |
| ZWAVE-01 | `322d0a1f-6940-4136-bbae-b7251ff4ab9e` |

## Tests locaux exécutés

Agent, commit `54c4a2a`, environnement `.venv` du dépôt : **67 tests réussis**.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_tsunade_read_only.py tests/test_tsunade_investigations.py tests/test_tsunade_expertise.py tests/test_tsunade_followups.py tests/test_log_review_cycle.py -q
# 44 passed
.\.venv\Scripts\python.exe -m pytest tests/test_configuration_inspection.py tests/test_host_health.py tests/test_mqtt_check.py tests/test_teleinformation_check.py -q
# 23 passed
```

Couverture ciblée : opérations autorisées et délais, HTTP HEAD sans redirection,
filtrage des identifiants/URL, GET Supervisor fixes, hypothèses IA non décisionnelles,
collecte complémentaire unique, reprise après interruption, journaux stables sans IA
et nouveaux journaux déclenchant l'analyse. Ces résultats ne valident ni l'ensemble
du logiciel ni les scénarios de production ; Katsuyu n'a pas été testé dans cette campagne.

## Protocole pour les prochaines validations

Pour chaque cas, conserver : version réellement installée, incident et jobs associés,
heure Europe/Paris, observation déclenchante, faits datés, hypothèses, informations
manquantes, décision, nombre de collectes/analyses, état final et contrôle de retour sain.

1. Valider sur un nouveau diagnostic réel les corrections locales vérifiées ci-dessus.
2. Vérifier un cycle complet pour chacun des quatre nœuds, dont HTTP et Supervisor.
3. Présenter deux fois les mêmes preuves : aucune nouvelle IA automatique attendue.
4. Ajouter une preuve matériellement nouvelle : réévaluation justifiée et bornée.
5. Vérifier qu'une analyse terminée reste terminée après reprise du runtime.
6. Vérifier qu'`INSUFFICIENT_CONTEXT` entraîne une investigation ciblée autorisée,
   puis une limite explicite si elle reste insuffisante, sans boucle.
7. Examiner les faux positifs MQTT, série et télémétrie en confrontant journaux,
   fréquence attendue, observation fonctionnelle et fraîcheur.

### Scénarios contrôlés à préparer

DNS indisponible, Mosquitto indisponible, perte de teleinfo2mqtt, communication Linky,
Z-Wave JS, Home Assistant, réseau d'un équipement, surcharge INFRA-01, Agent et Vision.

Avant chaque perturbation : définir une seule cible, l'impact attendu, la fenêtre,
la durée maximale, le retour à l'état initial et la vérification Shikamaru.
Obtenir l'autorisation humaine prévue par la roadmap pour toute modification réelle
de l'infrastructure. Aucun de ces scénarios n'est validé par la présente campagne.
