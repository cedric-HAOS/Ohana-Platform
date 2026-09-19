# Phase 1 — Stabilisation de Tsunade

## État au 15 septembre 2026

Phase démarrée, validation opérationnelle encore partielle. Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.100, Agent 1.29.0, Katsuyu 0.8.7.

Première campagne : tests locaux et consultation SSH en lecture seule sur INFRA-01
à partir de 13 h 58, heure Europe/Paris. Les bases SQLite ont été ouvertes avec
`mode=ro` et `PRAGMA query_only=ON`. Aucun incident provoqué, job relancé,
service redémarré ou changement déployé pendant cette campagne.

## Conclusion et priorités

### Inspection Supervisor Z-Wave et sondes HTTP — correction locale du 19 septembre

La poursuite de Phase 1 révèle un défaut de sélection dans l'inspection
Supervisor : seul LINKY-01 avait une sélection spécifique ; ZWAVE-01 héritait
de la recherche Mosquitto/MQTT. Z-Wave JS pouvait être ignoré, ou Z-Wave JS UI
sélectionné accidentellement via son ancien nom `zwavejs2mqtt`. Ce constat
vient du code et des tests, pas d'une nouvelle investigation de production.

**Correction locale Agent :** ZWAVE-01 sélectionne désormais les identifiants
et noms `z-wave js`, `zwavejs` et `zwave_js`. HA-01 et l'inspection MQTT associée
à INFRA-01 conservent Mosquitto/MQTT ; LINKY-01 conserve teleinfo/Linky.
Un champ `addon_selection` distingue liste inaccessible (`unavailable`),
aucune correspondance (`no_match`) et sélection effectuée (`matched`). Ce
dernier statut décrit la sélection, pas la santé de l'add-on. Une absence de
correspondance ne prouve ni arrêt ni absence du service sur la machine.

Les requêtes restent des GET fixes `/addons`, `/hardware/info`, puis
`/addons/{slug}/info`, `/addons/{slug}/stats` et `/core/info`, avec les limites
existantes. Les options Z-Wave libres, dont les clés réseau et S2, ne sont pas
exportées. Aucun changement de configuration ni de contrat de job requis.

**58 tests ciblés réussis** : inspection de configuration, sondes en lecture
seule, investigations et suivis. Le Supervisor simulé couvre les quatre cibles,
Z-Wave JS et JS UI, un Mosquitto présent sur ZWAVE-01 mais ignoré, une liste
inaccessible et une liste sans Z-Wave. Les tests vérifient les routes GET,
l'origine, l'état retourné et l'absence de clés fictives dans les preuves.
Un serveur HTTP local réel vérifie les réponses **302, 401, 403 et 503** :
une unique requête `HEAD /`, aucune redirection suivie, statut conservé sans
le transformer en erreur de transport. Ruff et contrôle de diff propres.

**Non publié et non déployé.** Les anciennes inspections restent inchangées ;
aucun incident ni job n'est relancé par ce correctif. Les cases Supervisor et
DNS/TCP/HTTP restent ouvertes, car ces tests ne remplacent pas une validation
sur les cibles réelles. Prochaine étape après déploiement autorisé : vérifier
une nouvelle inspection ZWAVE-01 (add-on sélectionné, état et ressources), puis
les réponses HTTP effectivement présentes dans une investigation réelle.

### Contrôle Katsuyu 0.8.10 — 19 septembre, 17:30–17:31

Agent **1.29.7** et worker **0.8.10** confirmés en SSH ; présence worker à
17:32:24 Europe/Paris. Commit local Katsuyu `3d65774`, dépôt propre. Contrôle
manuel `3a9a6448-c9d0-4de8-945c-edf989d64ff8`, créé à **17:30:40**, terminé
à **17:31:21** ; dernières décisions à **17:31:23**. Vérification SQLite en
lecture seule, sans nouvelle collecte ou modification de production.

Un seul job, réussi et traité : aucune analyse IA ni recherche complémentaire,
aucun job restant. Les quatre références sont présentes (14 / 21 / 16 / 9
groupes), aucune corrélation et les quatre collectes déclarent `truncated=false`.

| Source | Groupes observés | Décision déterministe |
| --- | --- | --- |
| INFRA-01 | 12 stables, 2 connus | `watch` |
| HA-01 | 20 stables, 1 nouveau | `watch` |
| LINKY-01 | 16 stables | `stable` |
| ZWAVE-01 | 8 stables | `stable` |

**Effet du filtre firmware confirmé sur ce résultat :** Z-Wave passe de neuf
à huit groupes. Le groupe `INFO Z-WAVE: Starting bulk firmware update check
for all nodes` est explicitement dans `disappeared_anomalies`, alors que sa
date précédemment observée (19 septembre à 15:38:32) reste dans la fenêtre
du nouveau contrôle (18 à 17:30:40 → 19 à 17:30:40). Les huit groupes `s6-rc`
restent stables. La disparition d'un finding filtré n'est pas une résolution
d'incident ni une preuve de santé complète.

Les messages INFO de déconnexion et `Backup store started` sont également
absents des findings. Le second était déjà absent du contrôle précédent :
son absence ici ne valide pas à elle seule le filtre sur une occurrence réelle
recollectée. Ce cas et le maintien des erreurs restent couverts par les tests
locaux, sans scénario d'erreur provoqué pendant cette passe.

Le correctif est désormais déployé ; la mention « local, non publié » de la
section historique ci-dessous ne décrit plus son état courant. La Phase 1
reste partielle : qualification des démarrages `s6-rc`, contrôles HTTP/Supervisor,
scénarios de panne et audit exhaustif des secrets encore ouverts.

### Global → INFRA-01 seul → global validé — 19 septembre, 17:13–17:14

Suite demandée par l'opérateur, avec Agent **1.29.7** et Katsuyu **0.8.9**.
Deux contrôles bornés de lecture des journaux ont été lancés par l'API
d'administration authentifiée, sans changement de configuration ni de service.
Le contrôle global de 17:05 sert de référence initiale.

- Partiel `aa183a70-5970-46a2-888e-f044a87aa913` : INFRA-01 seul,
  créé à **17:13:00**, terminé à **17:13:12 Europe/Paris**. Fenêtre de 24 heures,
  plafond de 4 Mio, baseline INFRA-01 issue du contrôle de 17:05. Soumission
  par `/v1/jobs`, car le parcours `/v1/incidents/logs/check` utilise toutes les
  sources configurées. Quatorze groupes stables, décision `stable`, aucune IA.
- Global `f5b76ebf-f944-4bcc-9cd5-c18e66f18923` : lancé à **17:13:47** par
  `/v1/incidents/logs/check`, après traitement du partiel. Collecte terminée
  à **17:14:28**, dernière décision à **17:14:30**.

La comparaison exacte des signatures et compteurs confirme que la baseline
du global combine les **14 groupes INFRA-01 du partiel** et les **21 HA-01,
16 LINKY-01 et 9 ZWAVE-01 du global de 17:05**. La sélection standard d'Agent
conserve donc les références des sources absentes du contrôle intermédiaire.

| Source | Résultat global | Décision |
| --- | --- | --- |
| INFRA-01 | 13 groupes stables, 1 connu | `stable` |
| HA-01 | 19 groupes stables, 1 connu, 1 nouveau | `watch` |
| LINKY-01 | 16 groupes stables | `stable` |
| ZWAVE-01 | 9 groupes stables | `stable` |

Les deux jobs sont `SUCCEEDED`, `completion_processed=1`. Aucune corrélation,
aucune collecte déclarée tronquée, aucun nouveau job IA ni suivi complémentaire.
Aucun job en attente ni résultat à traiter au relevé. Le cas de régression
global → partiel → global est désormais validé en production ; la case sur
les anomalies connues est cochée pour ce périmètre dans la roadmap. `stable`
ne signifie pas que les incidents historiques sont résolus.

### Messages INFO d'activité Z-Wave — correction locale suivante

Les messages exacts `INFO Z-WAVE: Starting bulk firmware update check for all
nodes` et `INFO BACKUP: Backup store started`, observés dans les contrôles
précédents, correspondaient aux mots `starting` / `started` du détecteur.
Leur présence seule n'établit pas une anomalie. Katsuyu les exclut désormais
sur ZWAVE-01 dans les collectes générales et ciblées ; la recherche ciblée
conserve le compteur des lignes correspondantes. Ils ne créent plus seuls de
corrélation avec un timeout simultané sur INFRA-01.

**47 tests handlers/IA réussis**, Ruff, formatage et diff propres. Les tests
couvrent les variantes WARNING/ERROR, les suffixes d'échec ou timeout, un autre
émetteur, un démarrage de driver et les mêmes textes provenant d'INFRA-01 ou
HA-01 : leur détection reste conservée. Les messages `s6-rc` ne sont pas
modifiés : distinguer un démarrage isolé d'une répétition anormale reste à
examiner, notamment avec leurs horodatages absents.

Ce filtre est **local, non publié et non déployé**. Les résultats historiques
restent inchangés. Prochaine validation : vérifier ses effets sur une collecte
après déploiement autorisé. Les scénarios de panne, HTTP/Supervisor et l'audit
exhaustif des secrets restent ouverts ; cette passe ne valide pas toute la Phase 1.

### Contrôle Agent 1.29.7 / Katsuyu 0.8.9 — 19 septembre, 17:05–17:07

Versions vérifiées en SSH après le déploiement signalé par l'opérateur ;
commit local Agent `f9096d8`. Consultation SQLite en lecture seule, sans
création de job ni modification de production pendant cette vérification.

Contrôle manuel `64b1314d-1728-4c16-8508-8848384b4566`, créé à
**17:05:18 Europe/Paris**, collecte terminée à 17:06:07. Les sept jobs du cycle
(une collecte générale, quatre analyses IA, deux recherches ciblées) sont
réussis et traités ; dernier résultat à **17:07:51**, aucun job restant.

La baseline est exactement égale aux signatures et compteurs du contrôle
global précédent : INFRA-01 1 groupe, HA-01 20, LINKY-01 16, ZWAVE-01 9.
Les quatre collectes déclarent `truncated=false` ; aucune corrélation.

| Source | Résultat | Décision / nouvelle IA |
| --- | --- | --- |
| INFRA-01 | 1 groupe connu, 13 nouveaux ; recherche ciblée sans correspondance ni anomalie | `investigate` après deux analyses IA ; pas de preuve de résolution globale |
| HA-01 | 13 groupes stables, 1 connu, 1 en baisse, 6 nouveaux ; recherche ciblée : 380 correspondances, 6 anomalies | `investigate` après deux analyses IA |
| LINKY-01 | 16 groupes stables | `stable`, aucune nouvelle IA |
| ZWAVE-01 | 8 groupes stables, 1 nouveau | `watch` déterministe, aucune nouvelle IA |

Les huit groupes Z-Wave `s6-rc` ont retrouvé une référence et ne sont plus
artificiellement nouveaux. La déconnexion INFO reste absente des findings.
Le nouveau groupe est `INFO Z-WAVE: Starting bulk firmware update check for
all nodes`, le 19 à **15:38:32 Europe/Paris**, une occurrence classée `warning`.
La pertinence de ce classement reste à examiner avec les autres messages INFO
de démarrage ; il n'a pas déclenché d'IA sur ce cycle.

Aucun segment de session caméra `/stok=…/` non masqué détecté dans les
paramètres et résultats des sept jobs. Ce contrôle ciblé ne constitue pas un
audit exhaustif de toutes les formes de secrets.

**Validation partielle du correctif 1.29.7 :** conservation des références
et absence de relance IA LINKY-01 / ZWAVE-01 confirmées sur ce contrôle réel.
Le contrôle précédent était global : cette passe ne reproduit donc pas le
cas global → INFRA-01 seul → global, qui reste validé par les tests locaux
et doit encore être observé en production. Le critère global sur les anomalies
connues reste ouvert dans la roadmap. Le correctif est désormais déployé ;
les mentions « local, non publié » de la section suivante sont historiques.

### Reprise du 19 septembre — Katsuyu 0.8.9 et références par source

Vérification SSH en lecture seule vers 16:37–16:43 Europe/Paris : Agent
**1.29.6**, Katsuyu **0.8.9** (présence worker à 16:38:12), Agent et Vision
actifs. SQLite ouvert avec `mode=ro` et `PRAGMA query_only=ON`.
Aucun job créé, service modifié, incident provoqué ou déploiement effectué.

Les commits locaux de release sont Agent `53a8645` et Katsuyu `07d3c43`.
Les mentions « Non publié » ci-dessous décrivent les passes historiques :
le correctif INFO Z-Wave et la normalisation ISO sont inclus dans le commit
0.8.9. Les assets distants n'ont pas été réaudités pendant cette reprise.
Agent, Katsuyu et House étaient propres ; le rapport Platform comportait déjà
les constats du 16 septembre, conservés ici.

**Effet observé sur Z-Wave :**

| Contrôle | Groupes Z-Wave | Déconnexion INFO classée en anomalie | Corrélations |
| --- | --- | --- | --- |
| 16/09 09:01, `baecd2f5-95d2-4f78-9607-bb680d7e4d3f` (0.8.8 vérifiée lors du contrôle précédent) | 10 | Oui, 96 occurrences | 3 INFRA-01 / ZWAVE-01 |
| 17/09 04:45, `e4dc12d6-d175-4d78-a4b3-2e7ff63eb18e` | 10 | Non | 0 |
| 18/09 10:40, `0411c04f-b19f-4989-a39a-e02683b0b3dc` | 9 | Non | 0 |
| 19/09 04:45, `e81481df-c09d-4b51-8164-14b30faff3ae` | 9 | Non | 0 |

Les trois résultats postérieurs à la release ne contiennent plus la signature
INFO de déconnexion. Le timeout de nœud `ZW0201` reste détecté le 18 septembre
à 07:59:57 Europe/Paris. Cela confirme le comportement attendu sur les résultats
observés ; la version n'est pas persistée individuellement dans chaque job et
les journaux bruts n'ont pas été recollectés pour rejouer à l'identique les
fenêtres. L'absence de corrélation seule ne démontre pas la causalité du filtre
ni une santé Z-Wave entièrement validée.

**Défaut distinct confirmé dans les données persistées :** le contrôle
`6084d9f8-665b-4b22-8e7a-652d94a2300f`, le 18 à 10:48, ne couvre qu'INFRA-01.
Le code choisissait le dernier résultat global comme référence de toutes les
sources. La baseline du 19 ne contient donc que trois groupes INFRA-01 ;
HA-01, LINKY-01 et ZWAVE-01 n'ont plus de référence. Les huit groupes Z-Wave
`s6-rc` déjà stables le 18 deviennent `new` avec `reference_occurrences=null`.
Le neuvième groupe du 19 est `INFO BACKUP: Backup store started` à 02:00.
Ce cycle ne présente aucune corrélation : la nouvelle analyse ne vient donc
pas d'une répétition des trois corrélations du 16.

Le cycle du 19 comprend dix jobs réussis et traités (une collecte générale,
six analyses IA, trois recherches ciblées), terminé à **05:07:27**. INFRA-01
reste `stable`, HA-01 et LINKY-01 finissent en `investigate`, ZWAVE-01 en
`watch` pour contexte insuffisant après une recherche sans correspondance ni
anomalie, non tronquée. Aucun job en attente ni résultat à traiter au relevé.
Deux contrôles du 18 ont expiré ; ils ne sont pas comptés comme validations.

**Correction locale Agent, non publiée et non déployée :** rechercher la
dernière source présente dans un contrôle réussi pour chacune des sources
demandées. Un contrôle partiel ne remplace que sa propre référence ; un résultat
sain sans finding efface bien les anciens groupes de cette source, et un job
échoué ne devient pas une référence. Le masquage avant persistance est conservé.
Les anciens résultats suffisent à la reprise, sans migration ni réécriture.
La même sélection en lecture seule, arrêtée avant le contrôle du 19, retrouve
3 groupes INFRA-01 dans le contrôle de 10:48 et respectivement 12, 16 et 9
groupes HA-01, LINKY-01 et ZWAVE-01 dans celui de 10:40.

Validation locale : **57 tests réussis** (cycle des journaux, rejeu des
corrélations, jobs d'administration et sources). Deux cas couvrent le contrôle
partiel, la reprise par nouvelle connexion SQLite, un job échoué, une source
jamais collectée et une référence saine vide ; le test de masquage reste passant.
Ruff, vérification du formatage et contrôles de diff passent.

Suite prioritaire : valider cette correction après déploiement autorisé sur
un enchaînement contrôle global → INFRA-01 seul → contrôle global. Examiner
ensuite le classement des messages INFO `s6-rc` et `BACKUP` comme anomalies :
le défaut de référence est corrigé localement, leur pertinence reste ouverte.
Les scénarios de panne et l'audit exhaustif des secrets restent non validés.
La roadmap est rapprochée de ces preuves, sans cocher une validation globale
du traitement des anomalies connues tant que cette régression demeure déployée.

### Déconnexion INFO Z-Wave — correction locale ciblée

Le message exact `INFO Z-WAVE-SERVER: Client disconnected`, provenant de
ZWAVE-01, est désormais exclu du classement en anomalie. Sa présence seule
ne démontre pas un défaut de communication. Les variantes WARNING/ERROR,
les messages mentionnant un timeout, les erreurs de nœud et les autres
émetteurs restent soumis au détecteur existant.

Le filtre s'applique à la collecte générale et à la recherche ciblée. Cette
dernière conserve la ligne dans `matched_lines` mais ne produit pas de finding
pour ce seul message. Sans finding, ce message ne participe plus aux
corrélations avec les avertissements INFRA-01.

**35 tests handlers/IA réussis.** Six scénarios vérifient les deux collectes,
les compteurs et les corrélations face à un timeout simultané sur INFRA-01.
La correction de normalisation des dates de la passe précédente est incluse.
Non publié et non déployé ; les anciens résultats ne sont pas modifiés.
Cela ne valide pas à lui seul la santé Z-Wave et ne supprime pas les autres
anomalies ou corrélations présentes.

### Qualité du regroupement et corrélations au démarrage — 16 septembre

La lecture du contrôle de 09:01 montre des avertissements de synchronisation
et de timeout sur INFRA-01, proches d'une ligne INFO « client disconnected »
Z-Wave. Les démarrages Agent/Vision sont datés vers 09:01:09–09:01:38.
La proximité temporelle est réelle ; elle ne démontre ni une causalité ni une
panne Z-Wave. La déconnexion reste classée comme anomalie par le détecteur actuel.

Défaut de regroupement confirmé : `_signature` mettait le texte en minuscules
avant de retirer les horodatages, alors que le séparateur ISO attendu était `T`.
Les synthèses réelles contiennent ainsi un fragment `16t09` dans leur signature.
Un message identique à une autre date pouvait être classé à tort comme nouveau.

Correction locale Katsuyu : retirer les dates avant conversion en minuscules.
Test avec deux lignes journald ayant des dates, heures et PID différents :
signature identique, tendance stable, compteur précédent conservé et date réelle
de la nouvelle observation correctement extraite.

**29 tests handlers/IA réussis**, contrôles de style et diff propres. Non publié,
non déployé. Les anciennes signatures déjà mal normalisées ne sont pas migrées :
une première collecte après mise à jour peut encore provoquer un changement de
référence. La comparaison stabilisée se juge ensuite entre collectes produites
avec cette correction. La pertinence des déconnexions INFO Z-Wave et des
corrélations de démarrage reste un point ouvert distinct.

### Contrôle Agent 1.29.6 / Katsuyu 0.8.8 — 16 septembre, 09:01–09:03

Versions vérifiées en SSH. Contrôle
`baecd2f5-95d2-4f78-9607-bb680d7e4d3f`, créé à 09:01:50 Europe/Paris,
dernier résultat à 09:03:57. Sept jobs réussis et traités ; aucun restant.

Trois corrélations INFRA-01 / ZWAVE-01 sont présentes, à 09:01:43, 09:01:47
et 09:01:49 Europe/Paris. La comparaison des empreintes avec les marqueurs
antérieurs confirme trois nouveautés et aucune répétition déjà traitée pour
chacun des deux incidents. L'escalade IA est donc conforme au critère de nouveauté ;
elle ne constitue pas une preuve de boucle sur les mêmes corrélations.

- HA-01 : surveillance déterministe ; LINKY-01 : stable, sans nouvelle IA.
- INFRA-01 : attribution `system-journal` conservée ; décision `investigate`
  formulée en pistes à vérifier, sans affirmation de panne confirmée.
  Recherche ciblée : zéro correspondance et anomalie, non tronquée.
- ZWAVE-01 : surveillance pour contexte insuffisant ; 239 correspondances,
  aucune anomalie reconnue, collecte non tronquée.
- Aucun segment de session caméra non masqué dans les paramètres et résultats
  des sept jobs examinés, selon l'audit ciblé `/stok=…/`.

Ce contrôle valide la prise en compte de nouvelles corrélations en production.
Il ne teste ni leur répétition identique ni l'impossibilité de créer un job IA ;
ces deux cas restent couverts par le rejeu local. Aucun changement de production
pendant la vérification.

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
