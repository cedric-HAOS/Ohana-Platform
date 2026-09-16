# Phase 1 — Stabilisation de Tsunade

## État au 15 septembre 2026

Phase démarrée, validation opérationnelle encore partielle. Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.100, Agent 1.29.0, Katsuyu 0.8.7.

Première campagne : tests locaux et consultation SSH en lecture seule sur INFRA-01
à partir de 13 h 58, heure Europe/Paris. Les bases SQLite ont été ouvertes avec
`mode=ro` et `PRAGMA query_only=ON`. Aucun incident provoqué, job relancé,
service redémarré ou changement déployé pendant cette campagne.

## Conclusion et priorités

### Rejeu local des corrélations et reprise — 16 septembre 2026

Un test utilise les sources et dates des deux corrélations du contrôle réel
`11dcefd0-d7cc-45db-8b64-f8013c66c75a` : INFRA-01 / ZWAVE-01,
15 septembre à 18:23:05.518642Z et 18:23:05.642184Z. Le libellé et les
anomalies sont synthétiques ; aucun journal brut ni secret n'est conservé.
Les horodatages ci-dessus sont les valeurs source utilisées pour le rejeu.

Le vrai moteur de décision est exercé avec un dispatcher simulé, sans inference
IA réelle. La base des incidents est fermée puis rouverte à chaque collecte :
première corrélation → analyse ; répétition et réception en double → aucune
analyse supplémentaire ; nouvelle date → nouvelle analyse.

Le test a aussi révélé un défaut : lorsqu'aucun job IA ne pouvait être créé,
les corrélations étaient malgré tout marquées comme examinées. Correction locale :
leurs empreintes ne sont pas acquittées dans ce cas, afin de permettre la reprise
au prochain contrôle. Cela concerne l'absence de job, pas un worker simplement
éteint alors qu'un job est déjà en attente.

**53 tests ciblés réussis**, Ruff et contrôle de diff propres. Le correctif est
local, non publié et non déployé. Les marqueurs éventuellement enregistrés par
les versions précédentes ne sont pas réécrits. La déduplication sur corrélation
répétée reste validée en rejeu local, et non par un nouveau cycle de production.

### Contrôle Agent 1.29.5 / Katsuyu 0.8.8 — 15 septembre, 20:42–20:43

Versions confirmées en SSH. Contrôle
`1dfda66a-de85-4efb-a8cf-44f826359297`, créé à 20:42:46 Europe/Paris,
dernier résultat à 20:43:55. Quatre jobs réussis et traités ; aucun restant.

- INFRA-01 conserve l'incident `dea74d31-6a14-4a17-83c8-f48ef94928e0`, désormais
  attribué à `system-journal` : migration d'attribution confirmée.
- Son verdict KO intermédiaire présente explicitement des pistes à vérifier,
  sans confirmer une panne ni sa cause. Sa réévaluation finit en surveillance
  avec contexte insuffisant, zéro correspondance, zéro anomalie reconnue et
  collecte non tronquée correctement restituée.
- HA-01 : surveillance déterministe ; LINKY-01 et ZWAVE-01 : stables.
  Aucun nouveau job IA pour ces trois sources.
- Aucun segment de session caméra non masqué dans les paramètres et résultats
  des quatre jobs, selon le contrôle ciblé `/stok=…/`.

Les marqueurs de corrélations examinées sont présents pour les quatre incidents.
Cette collecte ne contient aucune corrélation : elle confirme l'enregistrement
des marqueurs, mais ne valide pas encore en production le rejet d'une corrélation
identique répétée. Ce cas reste couvert par les tests locaux.

Aucune modification de production ni nouveau job pendant cette vérification.

### Conclusions IA et constats — correction locale

Les verdicts IA OK/KO utilisaient directement l'interprétation libre du modèle
comme conclusion Tsunade. Les nouveaux résultats emploient désormais une
conclusion explicite : pistes à vérifier pour KO ; absence de proposition
d'investigation pour OK, sans présumer un retour à l'état sain.

La synthèse commune applique également cette distinction aux anciens diagnostics
identifiés comme issus de Katsuyu. L'interprétation reste disponible dans le
champ `hypothesis` et dans l'historique. Les paramètres de session caméra sont
masqués dans ce nouveau champ de synthèse. Aucun événement historique n'est
réécrit et aucun incident n'est résolu sur la seule foi d'un verdict IA.

Validation : **64 tests ciblés réussis**, couvrant les verdicts OK/KO nouveaux
et hérités, les incidents, leurs cycles et le compagnon. Ruff et diff propres.
Les synthèses structurées sont testées ; le rendu visuel Vision/Shizune n'a
pas été contrôlé dans cette passe. Aucun déploiement ni publication.

### Attribution INFRA-01 et répétition des corrélations — corrections locales

Le code attribuait tous les incidents de journaux à `home-assistant`, y compris
le journal système INFRA-01. Il utilise désormais `system-journal` pour cette
source. Au prochain contrôle, l'incident actif hérité conserve son identifiant,
sa date d'ouverture et ses événements ; les anciens textes IA ne sont pas réécrits.

La politique déclenchait aussi une investigation dès qu'une corrélation était
présente, sans mémoire des corrélations déjà examinées. Chaque contrôle terminé
conserve désormais leurs empreintes dans son événement de réévaluation. Une
corrélation identique, même avec les sources dans un autre ordre, ne suffit plus
à relancer l'IA. Une nouvelle date reste une information nouvelle. Les preuves
conservent toutes les corrélations ; seul le critère de déclenchement est filtré.
Les changements significatifs et anomalies critiques gardent leurs règles.

Les événements hérités sans empreinte ne sont pas reconstruits : une première
réévaluation peut donc encore examiner une ancienne corrélation après mise à jour.
La qualité des conclusions KO reste un sujet distinct, non résolu par ce changement.

Validation locale : **55 tests ciblés réussis**. Tests de migration d'un incident
persisté après réouverture, réception répétée et résolution ; tests d'escalade
avec corrélation initiale, répétée et nouvelle. Ruff et contrôle de diff propres.
Aucune release publiée, aucun déploiement effectué.

### Contrôle Agent 1.29.4 / Katsuyu 0.8.8 — 15 septembre, 20:24–20:26

Versions confirmées en SSH. Contrôle manuel
`11dcefd0-d7cc-45db-8b64-f8013c66c75a`, démarré à 20:24:13 Europe/Paris ;
dernier résultat à 20:26:17. Les sept jobs du cycle sont réussis et traités,
aucun job en attente lors du relevé.

**Masquage des segments de session confirmé sur ce cycle :** deux segments
dans les paramètres du contrôle, tous masqués ; quatre dans son résultat,
tous masqués. Aucun segment non masqué dans les paramètres ou résultats des
sept jobs examinés, y compris la baseline. Cela valide le défaut ciblé,
pas l'absence de toutes les formes possibles de secrets ni le nettoyage historique.

- HA-01 : surveillance déterministe, sans nouvelle IA.
- LINKY-01 : stable, sans nouvelle IA.
- ZWAVE-01 : suivi IA terminé en surveillance ; 239 lignes correspondantes,
  zéro anomalie, collecte non tronquée correctement restituée.
- INFRA-01 : suivi IA terminé en `investigate`, malgré une recherche ciblée
  sans correspondance. Cette recherche ne prouve pas la résolution globale,
  mais la conclusion continue de parler de Home Assistant sur INFRA-01 et
  de dégradation sans distinguer suffisamment l'historique de l'état actuel.

Le contrôle général compte trois anomalies nouvelles et une aggravation ;
INFRA-01 porte deux nouveautés et une aggravation. ZWAVE-01 ne présente ni
nouveauté ni aggravation dans ses groupes : le motif précis de sa nouvelle
escalade reste à examiner (corrélations et politique), sans déduire une boucle
du seul nombre de jobs. Le cycle est bien borné lors du relevé.

Prochaine priorité : attribution des journaux INFRA-01, justification des
escalades et fidélité des conclusions KO à la fraîcheur des preuves.
Aucun changement de production ou nouvelle publication pendant cette vérification.

### Baseline historique filtrée avant envoi — correction locale

Le reliquat observé à 20:10 provenait du champ `baseline` du contrôle général.
Agent masque désormais les paramètres de session dans chaque signature avant
de créer le job. La règle est partagée avec le filtrage des preuves IA pour
éviter des comportements divergents. Les sources et compteurs sont conservés ;
Katsuyu 0.8.8 sait déjà regrouper les signatures masquées identiques.

Validation : **90 tests ciblés réussis**, Ruff et `git diff --check` propres.
Un test part d'une référence historique contenant deux sessions fictives,
crée le contrôle, relit le job avec une nouvelle connexion SQLite puis le
récupère par le parcours worker. Les paramètres sont masqués à chaque étape,
les compteurs conservés et l'objet historique d'origine inchangé.

Correction non publiée et non déployée. Elle concerne les contrôles créés après
mise à jour ; les paramètres des anciens jobs ne sont pas réécrits. La validation
du prochain contrôle réel devra donc porter sur son nouveau champ `baseline`,
en plus des prompts IA et résultats déjà vérifiés.

### Contrôle Agent 1.29.3 / Katsuyu 0.8.8 — 15 septembre, 20:10–20:12

Versions vérifiées en SSH : Agent 1.29.3 et worker 0.8.8. Le contrôle manuel
`e29dca79-6c1b-4f5b-8547-e86118917d3f` et ses neuf jobs complémentaires ont
réussi ; dernier résultat à 20:12:46 Europe/Paris, aucun job en attente au relevé.

- LINKY-01 : décision déterministe `stable`, sans nouveau cycle IA.
- INFRA-01 : recherche ciblée sans correspondance ni anomalie ; décision `watch`.
- ZWAVE-01 : 239 lignes correspondantes, aucune anomalie reconnue ; décision `watch`.
- HA-01 : 372 lignes correspondantes, huit groupes d'anomalies ; décision
  `investigate`. La qualification de persistance actuelle reste à confronter
  aux dates des anomalies, particulièrement aux fragments non datés.

Les trois collectes ciblées indiquent `truncated=false`. Les motifs Tsunade
INFRA-01 et ZWAVE-01 restituent correctement les compteurs et « Collecte non
tronquée », sans reprendre une troncature inventée par l'IA. Le correctif du motif
est donc confirmé sur ce cycle réel.

Audit ciblé des segments `/stok=…/`, sans export de leurs valeurs : aucun segment
non masqué dans les nouveaux résultats de ces dix jobs ni dans les paramètres
des six analyses IA. En revanche, quatre segments historiques non masqués sont
encore présents dans les paramètres du contrôle général. Le filtrage de sortie
fonctionne mais le trajet complet des données n'est pas encore validé : les
références historiques doivent être filtrées avant persistance et envoi du job.
Cet audit ne constitue pas une recherche exhaustive de toutes les formes de secrets.

Aucune modification de production, publication ou relance pendant ce contrôle.

### Confidentialité et fraîcheur HA-01 — travaux locaux sans release

La lecture des synthèses du cycle de 14:54 a révélé des paramètres de session
caméra conservés dans certains chemins URL. Aucune valeur n'est recopiée ici.
Le critère « secrets exclus des preuves » reste donc non validé en production.

Corrections locales : Katsuyu masque les segments `/stok=…/` avant calcul des
signatures et extraction des références. La comparaison avec les anciennes
signatures applique le même masquage et regroupe les compteurs, afin de ne pas
confondre une rotation de session avec une nouvelle anomalie. Agent masque aussi
ces segments en reconstruisant les preuves JSON depuis les anciens résultats.
Les bases existantes ne sont pas nettoyées par ces changements ; leurs données
historiques et les anciens diagnostics peuvent donc encore contenir ces valeurs.

La recherche ciblée HA-01 contient dix groupes d'anomalies sans `first_at` ni
`last_at`. Le parseur conserve les lignes non datées : on ne peut pas affirmer
qu'elles appartiennent à la fenêtre de deux heures demandée. La question de
réévaluation précise désormais cette limite. Aucun horodatage n'a été inventé.
Dans la collecte générale, des erreurs Kasa sont datées jusqu'au 15 septembre
à 14:46:05 Europe/Paris ; celles de Tapo jusqu'à 10:48:25 et l'automatisation
caméra jusqu'à 09:46:12. Ces dates proviennent des champs structurés lus en SSH ;
elles décrivent la collecte, pas un contrôle de santé actuel des appareils.

Validation locale : 18 tests de handlers Katsuyu passent, dont les deux parcours
de collecte avec sessions fictives, conservation des références utiles et
comparaison aux signatures anciennes. Le test Agent vérifie le masquage d'une
ancienne preuve sans altérer l'objet historique d'origine. Aucun déploiement,
publication ou nouveau job de production n'a été lancé.

### Motif de décision fondé sur la collecte — correction locale

Le cas INFRA-01 a révélé que le motif `INSUFFICIENT_CONTEXT` reprenait directement
le résumé IA. Correction locale Agent : le motif utilise désormais les compteurs
et le booléen de troncature de `investigation.followup`, enregistrés séparément
dans `collection_facts`. Sans preuve correctement typée, le motif reste neutre.
Le prompt distingue aussi explicitement fenêtre limitée et troncature.

Le résumé IA d'origine est conservé comme hypothèse pour la traçabilité ; il n'est
plus repris comme motif de décision pour ce verdict. Ce changement ne constitue
pas un détecteur général de contradictions et ne modifie pas les verdicts OK/KO.

Validation locale : **45 tests réussis**, Ruff et contrôle de diff propres.
Le cas testé reprend une IA affirmant une troncature face à `truncated=false`,
ainsi que `true`, une valeur inconnue et une chaîne invalide. La réception répétée
du même résultat n'ajoute pas de diagnostic. Les tests des cycles et reprises passent.

Non publié, non déployé. Les diagnostics déjà persistés, dont celui d'INFRA-01,
restent inchangés ; le nouveau motif s'appliquera aux résultats traités après
mise à jour. Aucun job réel n'a été relancé pendant cette correction.

### Validation après déploiement — cycle de 14:54 à 14:56

Version installée vérifiée par SSH : **Agent 1.29.2**, worker **Katsuyu 0.8.7**.
Le commit Agent `de2a8e2` conserve la correction des preuves publiée en 1.29.1.
Analyse manuelle `ce9cf2aa-2002-4d39-a690-785d3469a68a`, fenêtre du 14 septembre
14:54:24 au 15 septembre 14:54:24 (Europe/Paris), terminée à 14:55:10.
Les quatre sources ont été collectées sans troncature.

| Cible | Résultat du nouveau cycle | Conclusion de validation |
| --- | --- | --- |
| LINKY-01 | Décision déterministe `stable`, anomalies connues sans aggravation significative | Pas de nouvelle IA sur ce cycle |
| ZWAVE-01 | Décision déterministe `stable`, anomalies connues sans aggravation significative | Pas de nouvelle IA sur ce cycle |
| HA-01 | Deux analyses IA réussies ; recherche `exception` : 382 lignes, 10 anomalies, sans troncature ; suivi `completed`, décision `investigate` | Le diagnostic identifie Tapo/Kasa et des erreurs d'automatisation ; causes encore hypothétiques |
| INFRA-01 | Deux analyses IA réussies ; recherche `timeout` sur 12:55–14:55 : aucune correspondance ni anomalie, sans troncature ; suivi `incomplete`, décision `watch` | L'absence de preuve actuelle ne devient plus une affirmation de panne persistante |

Les sept jobs de ce cycle (une collecte générale, quatre analyses IA et deux
collectes ciblées) sont `SUCCEEDED` et `completion_processed=1`. Aucun job
`QUEUED` ou `RUNNING` au contrôle. Les deux réévaluations comprennent désormais
`logs.analysis` et `investigation.followup` : la conservation des preuves est
confirmée en production. Aucun échec de schéma IA sur ce cycle.

**Défaut restant confirmé :** l'analyse INFRA-01
`b5a5893c-2042-4de8-ad1c-21e2a2cb0d10` affirme que les résultats sont tronqués,
alors que sa propre preuve `investigation.followup.result.truncated` vaut `false`.
La limite de fenêtre est réelle ; la troncature alléguée est fausse. La qualité
des conclusions n'est donc pas entièrement validée. La décision finale reste
`watch` avec cause non confirmée, sans relance supplémentaire observée.

Prochaine priorité : vérifier la fidélité des limites formulées par l'IA aux
champs structurés, puis analyser les anomalies HA-01 les plus récentes pour
distinguer défaut actif et erreurs historiques. Les quatre incidents de journaux
restent ouverts ; `stable` ne signifie pas résolu. Aucun changement de production
n'a été effectué pendant ce contrôle.

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
