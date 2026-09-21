# Phase 1 — Stabilisation de Tsunade

## Cadre initial — 15 septembre 2026

Phase démarrée, validation opérationnelle encore partielle. Référence :
[roadmap commune](../ROADMAP.md), Platform 1.0.100, Agent 1.29.0, Katsuyu 0.8.7.

Première campagne : tests locaux et consultation SSH en lecture seule sur INFRA-01
à partir de 13 h 58, heure Europe/Paris. Les bases SQLite ont été ouvertes avec
`mode=ro` et `PRAGMA query_only=ON`. Aucun incident provoqué, job relancé,
service redémarré ou changement déployé pendant cette campagne.

## Conclusion et priorités

### Validation opérationnelle des investigations essentielles — 21 septembre 2026

Les quatre nœuds représentatifs prévus pour la sortie de Phase 1 ont désormais
été exercés sur Konoha : ZWAVE-01, INFRA-01, HA-01 et LINKY-01.

INFRA-01 a été contrôlé avec les huit investigations bornées exposées par
Tsunade :

- `backup.status` : dernier backup distribué `SUCCEEDED`, exécuté par
  `katsuyu-bubule` ;
- `cpu.status` : charge nominale et température normale ;
- `disk.usage` : capacité disponible suffisante ;
- `memory.status` : mémoire et swap sans pression ;
- `service.status` : aucune unité supervisée en échec ou inactive,
  `agent_restarts=0` ;
- `dns.query` : résolution effective via le DNS primaire sur ZWAVE-01 ;
- `mqtt.status` : aller-retour MQTT réel vers HA-01 réussi ;
- `network.ping` : présence réseau de la FreeBox confirmée.

HA-01 a ensuite été exercé directement via le plugin
`home_assistant_telemetry`. L'Agent s'est authentifié auprès de Home Assistant,
a lu une entité réelle et récente et a obtenu un résultat `success=true`,
sans erreur du plugin.

LINKY-01 a été exercé via le plugin `teleinformation` dans son mode cible
`direct_http`. Le contrôle a validé le chemin direct
`teleinfo2mqtt → Ohana-Agent`, sans passage par Home Assistant :

- source `rpi-linky` ;
- puissance apparente `SINSTS` reçue ;
- tarif `NTARF` interprété ;
- période Tempo courante déterminée ;
- index actif identifié ;
- six index `EASF01` à `EASF06` disponibles ;
- données âgées d'environ deux secondes au moment du test ;
- aucune erreur.

La campagne opérationnelle confirme donc que Tsunade dispose de preuves
déterministes exploitables sur les quatre nœuds représentatifs de la Phase 1.

### Déploiement Agent 1.29.15 — 21 septembre 2026

La version qualifiée localement a été publiée puis déployée sur INFRA-01.

La recette post-déploiement en lecture seule est entièrement réussie :

- connexion INFRA-01 : PASS ;
- version Ohana-Agent 1.29.15 : PASS ;
- service `ohana-agent` actif : PASS ;
- aucun redémarrage automatique (`NRestarts=0`) ;
- API d'administration sur le port 8765 accessible ;
- base des jobs accessible ;
- aucun job actif restant ;
- aucun résultat terminal non traité ;
- journal Agent accessible ;
- aucune erreur Agent récente.

Le service observé avait démarré le 21 septembre 2026 à 17:55:38 CEST.

Un contrôle réel des journaux a ensuite été déclenché avec :

powershell
.\sandbox\run.ps1 post-deploy agent 1.29.15 --exercise-logs

Résultat :
- worker katsuyu-bubule disponible ;
- job logs.health_check créé :
  a174c66d-fba0-4e1f-9c25-ca54c1a729e1 ;
- job terminé SUCCEEDED ;
- résultat terminal traité par Tsunade ;
- completion_processed=1 ;
- aucun contrôle logs.health_check résiduel ;
- aucun autre résultat terminal en attente ;
- aucune erreur Agent récente.
Cette validation confirme que le code Agent 1.29.15 qualifié localement est
effectivement déployé et que le cycle réel
Agent → Katsuyu → résultat → Tsunade fonctionne après déploiement.


### Audit de sûreté des preuves — 21 septembre 2026

L'audit élargi de la chaîne de preuves Tsunade est terminé.

Une sanitation centralisée protège désormais les données techniques avant leur
utilisation ou leur exposition lorsque celles-ci peuvent contenir des secrets.

Les chemins couverts comprennent notamment :

- messages et métadonnées des observations Shikamaru ;
- résultats des investigations déterministes ;
- erreurs de jobs distribués lorsqu'elles deviennent une preuve Tsunade ;
- contexte et événements persistés dans les incidents ;
- données transmises à Katsuyu pour `ai.inference` ;
- résultats et hypothèses retournés par Katsuyu ;
- erreurs d'inférence ;
- collectes complémentaires et follow-up ;
- expériences mémorisées ;
- résultats finaux ;
- projections destinées à Vision et Shizune.

La protection traite notamment :

- credentials inclus dans une URL ;
- tokens génériques et variantes `*_token` ;
- API keys ;
- mots de passe ;
- secrets ;
- en-têtes Authorization/Bearer ;
- chemins de session caméra `/stok=.../`.

La sanitation conserve autant que possible la structure diagnostique utile.
Le test historique des chemins caméra vérifie par exemple que :

/stok=<secret>/ds
devient :
/stok=[redacted]/ds

et non une preuve entièrement supprimée.
Une seconde barrière protège également la relecture de données anciennes déjà
présentes en SQLite. Il n'est donc pas nécessaire de réécrire ou migrer les
anciens dossiers uniquement pour appliquer les règles de confidentialité
actuelles.
Validation finale :
Ohana-Agent
1557 passed, 1 skipped

Ohana Sandbox
9/9 scénarios PASS

Full-stack
PASS

Le full-stack confirme après ces modifications que la chaîne complète reste
fonctionnelle :

Vision
  ↓
Tsunade
  ↓
Katsuyu HTTPS
  ↓
llama.cpp / Ministral
  ↓
Tsunade
  ↓
Vision

Le dernier passage full-stack propre a généré 628 tokens et validé le rendu
desktop/mobile, sans erreur JavaScript ni réponse HTTP serveur en erreur.

Le teardown Vision sous Windows a également été corrigé : l'arrêt réveille
désormais proprement l'accept() du socket avant sa fermeture. Le scénario se
termine sans `WinError 995` ni exception asyncio non récupérée.

Le critère de sortie « Preuves suffisamment sûres » est donc acquis.
La sanitation globale de toutes les données internes du protocole générique des
jobs distribués reste un sujet de durcissement possible. Elle n'est pas requise
pour la Phase 1 : toute donnée provenant de ce protocole qui entre dans le
dossier de preuve Tsunade passe désormais par la frontière de sanitation.


### Où nous en sommes réellement

Le développement de stabilisation locale nécessaire à la Phase 1 est désormais
terminé.

Les validations locales sont vertes :

- 1557 tests Agent PASS, 1 skipped ;
- 9/9 scénarios Sandbox PASS ;
- full-stack réel PASS avec worker HTTPS, llama.cpp, Ministral et Vision ;
- teardown du laboratoire propre sous Windows.

Six critères de sortie sur dix sont acquis.

Les quatre critères encore ouverts nécessitent maintenant principalement une
validation opérationnelle sur Konoha :

1. exercer suffisamment INFRA-01, HA-01 et LINKY-01 ;
2. vérifier réellement le mode dégradé sans Katsuyu ;
3. exercer trois pannes contrôlées appartenant à plusieurs familles ;
4. démontrer la valeur de Katsuyu sur un incident Konoha réellement ambigu.

### État consolidé après validation full-stack — 21 septembre 2026

La validation de Phase 1 dispose désormais de trois niveaux complémentaires :

1. les scénarios Sandbox déterministes et reproductibles avec bases temporaires ;
2. la recette post-déploiement d'Agent sur INFRA-01 ;
3. un laboratoire full-stack local exerçant réellement Agent, Katsuyu, le runtime
   IA et Vision.

Le scénario suivant a été exécuté avec succès :

powershell
.\sandbox\run.ps1 run --full-stack
Résultat final : PASS.
Ce parcours exerce une chaîne d'intégration nettement plus complète que les
scénarios simulés précédents :
- démarrage d'un worker Katsuyu réel ;
- communication worker en HTTPS avec certificat local vérifié ;
- enregistrement du worker auprès d'Agent ;
- demande de contrôle des journaux depuis Vision ;
- collecte et analyse logs.health_check ;
- transmission d'une demande explicite de diagnostic à Tsunade ;
- création d'un vrai job ai.inference ;
- exécution d'une inférence locale réelle via llama.cpp ;
- utilisation du modèle Ministral-3-14B-Reasoning-2512-Q4_K_M.gguf ;
- validation de l'empreinte du modèle ;
- génération effective de tokens par le modèle ;
- réception et traitement du résultat IA par Tsunade ;
- projection de l'analyse Katsuyu dans le dossier d'incident ;
- affichage du résumé IA dans Vision ;
- contrôle du rendu Vision dans Chromium en desktop et mobile ;
- absence de débordement horizontal dans les deux formats ;
- absence d'erreur JavaScript ou de réponse HTTP serveur en erreur pendant le
  parcours ;
- vérification du cycle réseau worker
  register → next → source → heartbeat → complete.

Lors de l'exécution finale, le modèle a généré 628 tokens.
Cette validation démontre donc réellement le chemin :

```text brut
Vision
  ↓
Tsunade
  ↓
Katsuyu
  ↓
llama.cpp / Ministral
  ↓
Katsuyu
  ↓
Tsunade
  ↓
Vision
```
Elle démontre également que le dossier constitué par Tsunade est suffisamment
structuré pour être consommé par le worker réel, que la réponse IA peut être
acceptée et réintégrée sans court-circuiter Tsunade, et que le résultat est
effectivement exploitable dans Vision.
Le test reste toutefois un laboratoire local contrôlé :
- les bases Agent et Vision sont temporaires ;
- le journal déclencheur est synthétique ;
- l'infrastructure décrite au laboratoire est locale ;
- aucune panne de Konoha n'est provoquée ;
- la qualité opérationnelle de l'hypothèse produite sur un incident réellement
  ambigu n'est pas démontrée par ce seul PASS.
La valeur technique de la chaîne IA est donc validée, mais le critère de valeur
ajoutée de Katsuyu reste ouvert tant qu'un incident réel ambigu de Konoha n'a pas
bénéficié de manière identifiable de cette expertise.

Le teardown du laboratoire Vision sous Windows est désormais propre. La
fermeture du serveur ne provoque plus l'exception asyncio `WinError 995`
précédemment observée.

À ce stade, les principaux critères encore ouverts pour la sortie de Phase 1
sont donc opérationnels :
- exercer suffisamment INFRA-01, HA-01 et LINKY-01 ;
- réaliser trois pannes contrôlées représentatives dans plusieurs familles ;
- vérifier réellement la continuité de Shikamaru/Konoha sans Katsuyu ;
- démontrer la valeur de Katsuyu sur un incident réel ambigu ;

La frontière technique Tsunade ↔ Katsuyu et l'exploitation du résultat dans
Vision ne constituent plus des inconnues fondamentales.

### Cycle de collecte et réévaluation bornée — 21 septembre 2026

Le scénario `followup-evidence-cycle` porte la suite à **9 scénarios sur 9**.
Ses **57 vérifications** couvrent trois variantes : zéro ligne correspondante,
239 lignes sans anomalie reconnue, et 239 lignes sans anomalie avec collecte
tronquée. Chaque variante utilise les services Agent et des bases SQLite
temporaires, avec réponses de collecte et d'IA simulées.

Le parcours commence par une demande de contexte supplémentaire, attend
l'autorisation simulée de l'opérateur, exécute la collecte complémentaire puis
sa réévaluation. Les contrôles démontrent que :

- les anomalies initiales restent dans `logs.analysis`, séparées de
  `investigation.followup`, sans dates inventées ;
- la cible, la fenêtre de collecte et l'observation de référence restent
  présentes dans le dossier transmis ;
- `matched_lines` reste distinct du nombre d'anomalies ;
- pour `INSUFFICIENT_CONTEXT`, le motif de décision reprend la troncature
  factuelle même si le résumé IA simulé affirme le contraire ;
- une recherche vide ne résout pas l'incident : il reste actif avec décision
  `watch`, suivi `incomplete` et projection `investigation_exhausted` ;
- le cycle reste limité à deux jobs IA et une collecte, sans nouvelle demande
  d'autorisation ni résultat non traité ;
- recevoir à nouveau les deux résultats puis reconstruire les services depuis
  SQLite conserve les événements et la projection, sans créer de nouveau travail.

Validation locale : suite complète réussie, Ruff sur le nouveau scénario et
le registre, contrôle du diff sur les fichiers de ce lot. Aucun changement du
runtime Agent n'a été nécessaire. Ces résultats valident le contrat et l'arrêt
du cycle ; ils ne démontrent ni la qualité d'un modèle réel, ni la valeur ajoutée
de Katsuyu sur un incident ambigu, ni le rendu dans Vision. Aucun accès à la
production, publication ou déploiement pendant ce lot.

### Reprise et diagnostic local sans worker — 21 septembre 2026

Deux scénarios supplémentaires prolongent les six validations initiales :

| Scénario | Propriété vérifiée localement |
| --- | --- |
| `followup-restart` | Reconstruction des services depuis les deux bases SQLite, expiration pendant l'arrêt ou échec déjà traité avant l'arrêt ; conservation exacte des événements historiques, suivi `failed`, interruption visible, aucune conclusion équipement inventée ni relance après une seconde reprise. |
| `local-diagnosis-worker-unavailable` | Avec Katsuyu `UNAVAILABLE` et une collecte `WAITING_WORKER`, Tsunade exécute deux sondes simulées, confirme le défaut DNS sans IA supplémentaire, expose `action_required` puis résout le même incident sur observation saine. L'incident de journaux et sa collecte restent distincts et en attente. |

Validation consolidée : **8 scénarios sur 8**, dont **33 vérifications** dans
les deux nouveaux scénarios. Le lanceur PowerShell active également le mode
UTF-8 pour éviter une erreur d'encodage des symboles PASS/FAIL sous Windows.

Ce lot ne modifie pas le runtime Agent. Il vérifie sa logique existante depuis
les checkouts locaux, sans accès à Konoha, publication ou déploiement. La reprise
est une fermeture/réouverture des bases et une reconstruction des services,
pas un test d'arrêt brutal au milieu d'une transaction. Les sondes et observations
sont simulées ; l'horloge accélérée concerne la file de jobs, tandis que les
décisions et les nouvelles observations locales utilisent l'heure système.

Les critères de sortie opérationnels restent ouverts : continuité réelle de
Shikamaru, pannes contrôlées, valeur ajoutée IA sur un cas ambigu et rendu Vision.

### Validation Ohana Sandbox — 21 septembre 2026

Un premier bac à sable d'intégration a été ajouté à `Ohana-Platform` afin de
valider les comportements multi-composants directement depuis les checkouts
locaux, sans publication de release, sans déploiement sur INFRA-01 et sans
perturbation de Konoha.

Le Sandbox utilise un environnement Python isolé, les sources locales
d'Ohana-Agent en mode editable, des bases SQLite temporaires et une horloge
contrôlée. Les scénarios n'accèdent à aucune sonde, aucun worker ni aucun
équipement réel sauf mention explicite contraire.

Validation consolidée : **6 scénarios réussis sur 6**.

| Scénario | Résultat | Propriété démontrée |
| --- | --- | --- |
| `probe-confirmed-failure` | PASS | Une sonde exécutée avec succès peut confirmer un défaut réel sans confondre les autres contrôles : `dns.query` mesure l'échec, `network.ping` reste sain, Tsunade produit `CONFIRMED` / `action_required` sans IA puis le même incident est résolu par une observation saine. |
| `diagnostic-levels` | PASS | Le contrat transversal `CONFIRMED` / `PROBABLE` / `INSUFFICIENT_CONTEXT` est conservé jusqu'à la projection utilisateur. `PROBABLE` reste une hypothèse, expose son `confirmation_gap` et ne peut pas devenir `action_required`. |
| `terminal-jobs-over-16` | PASS | Une consultation réconcilie plus d'un lot SQL de résultats terminaux ; 17 échecs sont traités, le suivi devient `failed`, l'incident expose `Investigation interrompue`, aucune relance n'est créée et une seconde consultation est idempotente. |
| `katsuyu-unavailable` | PASS | Sans nouveau polling Katsuyu, le worker devient `UNAVAILABLE`, le job passe `WAITING_WORKER` puis `TIMEOUT`, Tsunade reste consultable, l'incident reste actif, le suivi termine explicitement en échec et aucun travail n'est relancé. |
| `probe-timeout` | PASS | Un `TIMEOUT` de sonde reste une limite de collecte. Il ne produit jamais `confirmed_by_probe` ; Tsunade termine en `INSUFFICIENT_CONTEXT`, décision `watch`, avec justification et prochaine action exploitables. |
| `probe-error` | PASS | Une exception réelle dans `InvestigationExecutor` produit `KO` sans confirmer la panne. Seul le type d'exception est conservé ; le message contenant URL, identifiant, mot de passe et token fictifs n'est pas persisté dans l'incident. |

Le deuxième lot Sandbox introduit explicitement les trois niveaux de diagnostic
prévus par la roadmap.

- `CONFIRMED` exige une preuve déterministe effectivement obtenue et directement
  reliée au défaut ;
- `PROBABLE` conserve une hypothèse suffisamment étayée pour justifier une
  investigation, tout en indiquant explicitement ce qui manque encore pour la
  confirmer ;
- `INSUFFICIENT_CONTEXT` signifie que les preuves disponibles ne permettent pas
  de retenir une cause et constitue une terminaison valide en surveillance.

Le niveau de diagnostic est désormais persisté avec la décision et propagé
jusqu'à la projection d'incident. Un résultat Katsuyu `KO` accompagné
d'hypothèses peut produire `PROBABLE`, mais l'origine reste
`epistemic_status=hypothesis` et aucune intervention n'est autorisée sur cette
seule base.

Le scénario `probe-confirmed-failure` valide également fonctionnellement qu'un
incident simple peut rester entièrement chez Tsunade : observation, contrôles
déterministes, confirmation de la panne, décision et retour sain sont réalisés
sans création d'un job IA Katsuyu.

Le défaut selon lequel un job pouvait expirer alors que son suivi restait affiché
« en cours » est donc couvert par un scénario de régression dépassant
volontairement la limite interne de 16 résultats terminaux. La correction vide
tous les lots disponibles lors de la consultation sans dépendre d'un nouveau
passage de Katsuyu.

Les deux scénarios de sondes confirment également la frontière épistémique
attendue : une impossibilité d'exécuter une mesure (`KO` ou `TIMEOUT`) décrit
l'indisponibilité de la preuve, pas l'état de la cible. Seule une investigation
effectivement exécutée peut contribuer à une conclusion déterministe confirmée.

Le scénario d'indisponibilité Katsuyu valide localement le comportement de
Tsunade lorsque le worker disparaît : attente explicite, expiration bornée,
absence de conclusion artificielle, absence de relance et conservation de
l'incident. Il ne démontre toutefois pas encore que Shikamaru continue réellement
ses observations sur Konoha pendant une indisponibilité opérationnelle de Bubule
ou Katsuyu.

Ces validations sont **locales et reproductibles**, mais ne sont pas assimilées
à une validation de production. Elles ne remplacent ni un contrôle après
déploiement, ni les scénarios de panne contrôlée réellement exercés, ni la
validation du rendu Vision.

Le lot Agent correspondant n'est pas considéré comme validé en production par
ces seuls PASS. Le Sandbox permet désormais de regrouper les corrections et
d'effectuer une seule validation opérationnelle ciblée après publication, plutôt
que de publier une release pour chaque cas intermédiaire.

### Contrôle post-déploiement Agent 1.29.14 — 21 septembre 2026

Le développement dispose aussi d'un parcours indépendant du déploiement :
`sandbox/run.ps1 run all --exercise-logs`. Il exerce les sources locales
Agent/Katsuyu, le traitement Tsunade et la projection destinée à Vision sur
des journaux locaux, avec des bases temporaires. Validation locale du
21 septembre : neuf scénarios existants PASS et 25 contrôles de l'exercice
des journaux PASS (sain, anomalie, troncature, doublons, reprise).
Le rejeu d'un journal historique synthétique filtre correctement la fenêtre
de 24 heures ; les dates sans fuseau et les arguments incomplets sont refusés.
Le rendu Vision, le transport réseau du worker et l'inférence IA ne sont pas
couverts par ce parcours `--exercise-logs` lui-même. Ils sont désormais couverts
séparément par le laboratoire `run --full-stack`, décrit dans l'état consolidé
ci-dessus. Aucune release ni aucun déploiement n'est nécessaire pour exécuter
ce laboratoire local. Voir `sandbox/README.md` pour les commandes de rejeu.

Agent 1.29.14 publié et déployé sur INFRA-01. Le nouveau contrôle automatisé
`.\sandbox\run.ps1 post-deploy agent 1.29.14` a été exécuté depuis le poste de
développement.

Le contrôle se connecte explicitement à INFRA-01 par SSH et limite ses accès aux
lectures nécessaires à la recette. Les données de jobs sont consultées en SQLite
avec `mode=ro` et `PRAGMA query_only=ON`. Les lectures nécessitant les droits du
service sont exécutées sous le compte `ohana-agent` via une élévation `sudo`
bornée déjà autorisée ; aucune permission de production n'a été élargie.

Résultat : **10 contrôles sur 10 réussis**.

- version déployée : Agent `1.29.14` ;
- service `ohana-agent` : `active/running` ;
- `NRestarts=0` depuis le démarrage du service à 14:07:22 CEST ;
- port d'administration local `8765` accessible ;
- base des jobs accessible en lecture seule ;
- aucun job `QUEUED`, `WAITING_WORKER` ou `RUNNING` au relevé ;
- aucun résultat terminal avec `completion_processed=0` ;
- journal Agent accessible ;
- aucune erreur de niveau `err..alert` dans la fenêtre contrôlée ;
- les cinq derniers jobs visibles sont terminaux et traités, dont les contrôles
  `logs.health_check` précédemment validés.

Ce contrôle constitue la première recette post-déploiement automatisée du
Sandbox. Il valide l'intégration opérationnelle d'Agent 1.29.14 après
déploiement. Cette exécution sans `--exercise-logs` n'a provoqué aucune panne
et n'a lancé aucun nouveau contrôle de journaux. Les scénarios de panne
contrôlée et de mode dégradé réel restent donc distincts.

### Exercice réel des journaux depuis le Sandbox

Le Sandbox peut également déclencher et suivre un contrôle de journaux après
la recette du déploiement, depuis la racine d'Ohana-Platform :

```powershell
.\sandbox\run.ps1 post-deploy agent 1.29.14 --exercise-logs
```

`1.29.14` désigne la version Agent attendue et doit être adaptée au déploiement
contrôlé. L'option `--exercise-timeout 300`, par exemple, porte le délai de suivi
à 300 secondes au lieu des 180 secondes par défaut.

Le parcours utilise SSH vers INFRA-01 et l'API d'administration locale sous le
compte `ohana-agent`. Il vérifie qu'un worker Katsuyu est `AVAILABLE` et annonce
`logs.health_check`, puis appelle `POST /v1/incidents/logs/check`. Sans worker
compatible disponible, l'exercice est signalé non réalisé et le contrôle échoue.

Après la demande, il suit le job retourné et ajoute les vérifications suivantes
à la recette de base :

- worker disponible pour l'exercice ;
- job `logs.health_check` terminé en `SUCCEEDED` ;
- résultat traité par Agent (`completion_processed=1`) ;
- aucun `logs.health_check` en `QUEUED`, `WAITING_WORKER` ou `RUNNING`.

L'identifiant du job, son statut et son worker sont affichés. La vérification
SQLite reste en lecture seule (`mode=ro`, `PRAGMA query_only=ON`), mais
**l'exercice lui-même déclenche un travail réel** susceptible d'alimenter les
incidents et décisions Tsunade. Le dépassement du délai de suivi ne supprime
ni n'annule le job demandé.

Un PASS signifie que le contrôle des journaux a réussi et que son résultat a
été traité. Il ne signifie pas que les journaux sont exempts d'anomalies, que
toutes les conclusions sont correctes ou que les éventuelles analyses IA et
collectes complémentaires sont terminées : le contrôle résiduel porte seulement
sur les jobs `logs.health_check`.

Cette section décrit la capacité disponible, vérifiée dans le code du Sandbox.
Elle n'ajoute pas de résultat d'exécution à la recette historique de **10/10**
ci-dessus, réalisée sans cette option. Aucun exercice distant n'a été lancé
pour cette mise à jour documentaire.

### Contrôle Agent 1.29.13 / Katsuyu 0.8.15 — 21 septembre, 09:34–09:35

Versions confirmées en SSH après déploiement opérateur ; worker vu à **09:36:02
Europe/Paris**. Contrôle `fd36c235-2d87-4571-8469-ff1ef0e22e00`, créé à
**09:34:17**, collecte terminée à **09:34:59**. Un seul job, `SUCCEEDED` et
`completion_processed=1`. Quatre décisions déterministes `watch` de **09:35:00
à 09:35:11**, aucune expertise IA, aucune collecte complémentaire et aucun job
`QUEUED`/`RUNNING` au relevé. SQLite consulté avec `mode=ro` et `query_only=ON`.

| Source | Groupes avant → après | Collecte actuelle |
| --- | --- | --- |
| INFRA-01 | 14 → 16 | 10 000 lignes, tous les groupes datés, tronquée |
| HA-01 | 21 → 21 | 5 079 lignes, 14 groupes non datés, tronquée |
| LINKY-01 | 16 → 8 | 9 385 lignes, 8 groupes non datés, tronquée |
| ZWAVE-01 | 9 → 1 | 6 119 lignes, groupe restant daté, tronquée |

**Effet attendu du filtre s6 confirmé sur les résultats réels :** par comparaison
exacte avec le contrôle de 09:11, les huit groupes retirés de LINKY-01 et les huit
retirés de ZWAVE-01 sont exclusivement `s6-rc`. Aucun autre groupe n'est ajouté
ou retiré sur ces deux sources ; les signatures conservées ont exactement les
mêmes compteurs et criticités. Les trois groupes d'erreur série LINKY-01 restent
présents. HA-01 conserve ses signatures et criticités ; ses compteurs évoluent.
Les journaux bruts n'ont pas été recollectés à l'identique : les cas de répétition
et de démarrage incomplet restent couverts localement, sans panne provoquée ici.

Les quatre incidents de journaux restent actifs : le filtre n'a pas entraîné
de clôture. La troncature reste visible. Aucun segment `/stok` non masqué dans
les paramètres et le résultat du nouveau contrôle ; audit ciblé uniquement.

Deux groupes d'erreur INFRA-01 sont présents à **09:21:57–09:21:58** : un groupe
Vision nouveau et un groupe Agent classé en diminution. Une lecture journald
bornée à **09:21:55–09:22:01** identifie une trace `BrokenPipeError` Agent à
**09:21:59**. Seuls classe d'exception et indicateurs ont été exportés. Cette
proximité temporelle ne suffit pas à expliquer les deux groupes ni à conclure
à une panne persistante ; aucune correction supplémentaire n'est déduite de
ces seuls éléments.

Le lot s6 est désormais déployé et son effet ciblé observé. Les mentions locales
ci-dessous restent historiques. **Aucun nouveau déploiement requis par cette
vérification.** Les étapes restantes sont les validations représentatives de
phase 1 : mode dégradé réel, sondes indisponibles, pannes contrôlées autorisées,
valeur ajoutée IA et exploitation dans Vision. Aucun job, arrêt de service,
changement de configuration ou scénario de panne n'a été lancé ici.

### Contrôle Agent 1.29.13 / Katsuyu 0.8.14 — 21 septembre, 09:11

Versions confirmées en SSH après déploiement et contrôle manuel par l'opérateur.
Agent et Vision sont `active/running`, `NRestarts=0` au relevé ; ce compteur ne
prouve pas l'absence de tout arrêt antérieur. Worker 0.8.14 vu à **09:14:06
Europe/Paris**. Consultation SQLite avec `mode=ro` et `PRAGMA query_only=ON`.
Aucun job lancé ni modification de production pendant cette vérification.

Contrôle `a268ca57-5fd5-4f5e-af8d-2922768b351d`, créé à **09:11:04** et terminé
à **09:11:48**, fenêtre de 24 heures depuis le 20 septembre à 09:11:04.
**Un seul job, réussi et traité (`completion_processed=1`)**, aucune expertise
IA ni collecte complémentaire. Quatre décisions déterministes `watch` entre
**09:11:49 et 09:11:50** ; aucun job `QUEUED`/`RUNNING` au relevé.

| Source | Collecte | Décision |
| --- | --- | --- |
| INFRA-01 | 10 000 lignes, 14 groupes datés, tronquée | Surveillance d'une évolution |
| HA-01 | 5 058 lignes, 21 groupes dont 14 non datés, tronquée | Surveillance d'une évolution |
| LINKY-01 | 9 385 lignes, 16 groupes non datés, tronquée | Surveillance avec limite de complétude explicite |
| ZWAVE-01 | 6 187 lignes, 9 groupes dont 8 non datés, tronquée | Surveillance d'une évolution |

Ce cycle confirme une collecte déterministe Katsuyu suivie de décisions Tsunade
sans expertise IA, ainsi qu'un aboutissement explicite en surveillance sans job
bloqué. La situation représentative correspondante et la distinction traitement
déterministe / expertise IA sont cochées dans la roadmap. Cela ne valide pas le
cycle de vie global ni un diagnostic causal suffisamment approfondi sans IA.

Aucun groupe critique dans cette collecte, contrairement au faux positif HTTP
du 20 septembre. La ligne historique n'a pas été recollectée à l'identique et
INFRA-01 est tronqué : son absence seule ne démontre pas l'effet du filtre HTTP
sur cette occurrence précise. La version du worker contenant le filtre est
confirmée. Aucun segment `/stok` non masqué dans les paramètres ou le résultat
du nouveau contrôle ; contrôle ciblé, sans audit exhaustif des secrets.

**Limite de validation de 1.29.13 :** ce cycle n'exerce ni sonde KO/TIMEOUT ni
absence de worker compatible. Les corrections du lot précédent sont déployées,
mais leur validation opérationnelle spécifique reste ouverte. Les quatre
surveillances ne signifient pas que les incidents historiques sont résolus.

### Qualification locale des démarrages s6-rc — 21 septembre

Dans le contrôle réel, LINKY-01 et ZWAVE-01 ont chacun huit groupes `s6-rc` :
quatre `starting` et quatre `successfully started`, une occurrence par groupe,
sans date, stables et classés `warning`. La syntaxe INFO exacte a été vérifiée
par comparaison de modèles, sans exporter les noms de services ni les messages
bruts. Ces messages seuls ne démontrent pas une panne actuelle.

**Correction Katsuyu locale :** sur HA-01, LINKY-01 et ZWAVE-01, retirer du
classement en anomalie seulement une paire unique, ordonnée, de messages INFO
exacts « démarrage puis succès » du même service. Le rapprochement est fait dans
la source et le budget analysé, avant le filtre de recherche ciblée. Les lignes
restent comptées dans `analyzed_lines` / `matched_lines` ; les flags de troncature
ne sont pas modifiés. La reconnaissance n'invente aucun horodatage et ne conclut
pas à la santé actuelle du service.

Restent détectés : démarrage isolé, succès isolé, ordre inversé, autre service,
répétitions, WARNING/ERROR, suffixe d'erreur et échec après démarrage réussi.
Une paire partiellement hors fenêtre, aux dates inversées ou dont un seul membre
est daté n'est pas exclue. Le journal INFRA-01 conserve son comportement.
Une paire unique dans un extrait tronqué ne démontre pas l'absence de répétitions
dans les données omises ; la collecte reste incomplète pour Tsunade.

Reproduction : **4 échecs sur les 18 premiers cas** avant correction.
Validation finale : **177 tests Katsuyu réussis (suite complète)**, dont 36 cas
s6 ; **98 tests Agent réussis** sur expertise, suivis, revue, empreintes et
corrélations. Ruff, formatage et contrôle de diff passent. Aucun changement de
schéma de job, configuration, Agent ou Vision. Les anciens résultats, empreintes
et diagnostics ne sont pas réécrits ; leur historique reste conservé.

**Local, non publié et non déployé.** Le prochain déploiement utile pour valider
ce nouveau lot concerne **Katsuyu uniquement** ; Agent 1.29.13 peut être conservé.
Après publication/déploiement opérateur, comparer un nouveau contrôle : paires
INFO effectivement reconnues, vraies erreurs conservées, limites visibles,
nombre de jobs et décisions finales. Ne pas assimiler disparition d'un groupe
filtré et résolution de l'incident. Les scénarios contrôlés, le mode dégradé réel,
la valeur ajoutée d'une expertise IA et le rendu Vision restent à exercer ;
ils ne sont pas déclarés acquis par ces tests. La qualification des répétitions
s6 et leur fraîcheur restent du durcissement continu.

### Reprise locale — sondes indisponibles et mode dégradé, 21 septembre

Reprise à partir de la roadmap recentrée et du présent rapport. Agent est en
1.29.12 dans le checkout. Katsuyu contient déjà le commit local de release
0.8.14 (`73fc30a`), incluant le correctif HTTP : la mention « non publié » du
20 septembre ci-dessous décrit l'état de cette passe historique. Les assets
distants et la version actuellement exécutée n'ont pas été vérifiés ici.
Les modifications préexistantes de la roadmap et de ce rapport sont conservées.

**Défaut bloquant reproduit localement :** une exception ou un dépassement du
délai de l'exécuteur était interprété comme une panne déterministe confirmée.
Une lecture mémoire indisponible pouvait ainsi produire une conclusion de
pression mémoire avec `confirmed_by_probe`. Huit cas DNS, MQTT, mémoire et
systemd reproduisent ce défaut ; un neuvième montre qu'une sauvegarde simplement
désactivée était présentée comme un échec. Aucun de ces défauts n'est affirmé
comme observé dans un incident de production pendant cette reprise.

Corrections Agent locales :

- Seule une investigation exécutée (`status=OK`) peut fournir une mesure
  confirmant un défaut. Un résultat métier `success=false`, une unité en échec
  ou un seuil système dépassé restent exploités. `KO`/`TIMEOUT` de l'exécuteur
  restent des limites de collecte, conservées dans les preuves.
- `enabled=false` seul ne confirme plus un échec de sauvegarde ; un véritable
  statut `FAILED` reste reconnu, même si le plugin est maintenant désactivé.
- Sans mise en file IA possible, la décision devient `watch` avec
  `INSUFFICIENT_CONTEXT`, conclusion, justification, prochaine action et date
  de l'observation examinée. L'incident reste actif ; aucune action corrective
  n'est autorisée. Les synthèses détail/liste conservent ces champs après reprise.
- Une exception de sonde n'exporte plus son texte brut : le type suffit à
  signaler l'indisponibilité. Un test reproduisait la fuite d'identifiants fictifs
  dans la réponse et le journal applicatif. Ce filtrage ciblé ne constitue pas
  un audit complet de confidentialité.

**Validation : 171 tests Agent réussis**, couvrant expertise, investigations,
incidents, suivis, déduplication, corrélations, revue de journaux, jobs, compagnon
et démarrage. Parmi les nouveaux cas : sept défauts métier confirmés sans worker,
réouverture SQLite, retour sain par une nouvelle observation, sondes KO/TIMEOUT,
transmission de leur limite à une IA simulée et exception avec secrets fictifs.
Ruff et formatage passent sur les quatre fichiers Python modifiés.
Les sondes et le dispatcher sont simulés dans les tests de diagnostic ; cela
ne démontre ni une panne exercée sur Konoha ni la valeur d'un modèle IA réel.

**Local, non publié et non déployé.** Aucun nouveau schéma, paramètre de
configuration, handler Katsuyu ou changement Vision. Les anciens diagnostics
persistés ne sont pas réécrits ni rétroactivement requalifiés ; une nouvelle
investigation après mise à jour est nécessaire pour remplacer une conclusion
historique. Les erreurs déjà stockées ne sont pas nettoyées par ce correctif.

### Prochain point de passage opérationnel

Les corrections Agent relatives aux sondes indisponibles, au mode dégradé et à
la réconciliation des jobs terminaux sont désormais couvertes par les tests
locaux et par le Ohana Sandbox. Elles restent à publier puis à vérifier après
déploiement avant d'être considérées comme validées opérationnellement.

La prochaine publication utile peut regrouper ce lot : il n'est plus nécessaire
de publier une release intermédiaire pour chaque scénario déjà reproductible dans
le Sandbox. Après déploiement, effectuer un contrôle de fumée borné sur les
versions installées, le cycle des jobs, la projection des incidents et l'absence
de régression générale.

Les scénarios perturbant réellement Konoha restent soumis à autorisation
explicite. Une validation Sandbox ne constitue pas à elle seule un scénario de
panne contrôlée réellement exercé.

Ordre proposé après mise à jour, sans incident provoqué automatiquement :

1. Relever les versions installées et un nouveau contrôle manuel lancé par
   l'opérateur ; vérifier le classement HTTP, les preuves nouvelles, les limites
   de collecte et le nombre de jobs. Ne pas réutiliser un résultat historique
   comme validation du nouveau code.
2. Sur un diagnostic pertinent, vérifier qu'un échec d'exécution de sonde reste
   une information manquante ; relier une éventuelle conclusion confirmée à un
   résultat métier effectivement reçu. Examiner la synthèse rendue dans Vision.
3. Exercer les scénarios autorisés ci-dessous, un à la fois, puis conserver
   preuves datées, état final, nombre de jobs et contrôle de retour sain.

| Scénario candidat | Préparation et borne avant autorisation | Preuve attendue / retour initial |
| --- | --- | --- |
| Katsuyu indisponible (système / Ohana) | Relever les jobs actifs ; choisir une fenêtre sans sauvegarde, arrêter temporairement le worker uniquement après autorisation, fixer la durée et son redémarrage | Shikamaru continue ses observations ; Tsunade conserve les incidents et ses contrôles locaux ; distinguer absence de worker compatible, job réellement en attente et expiration ; redémarrer le worker et vérifier présence et jobs restants |
| Échec TCP d'une cible de test (réseau) | Choisir un endpoint de test isolé et réellement déclaré ; relever sa santé et prévoir retrait de la perturbation, durée maximale et accès de secours | Échec de connexion mesuré, incident et décision reliés à la cible ; rétablir l'endpoint et attendre une observation saine, sans déduire la résolution du seul succès IA |
| Service supervisé indisponible (service) | Choisir un service non critique pour l'accès d'administration ; relever l'état initial, l'impact utilisateur, la commande de retour et la durée maximale avant accord | État du service et contrôle fonctionnel concordants ; restauration à l'état initial et retour sain observé ; aucune réparation automatique ajoutée |

Ces trois scénarios sont **préparés, non exercés**. Les cibles précises et les
durées doivent être fixées avec l'opérateur avant toute perturbation. Ils ne
cochent aucune case de sortie de phase. Le cas ambigu apportant une valeur IA
réelle, les investigations représentatives restantes et le rendu Vision
restent aussi à démontrer sur de nouvelles preuves opérationnelles.

### Contrôle Agent 1.29.12 / Katsuyu 0.8.13 — 20 septembre, 17:35–17:37

Versions confirmées en SSH. Contrôle manuel
`d9132b7b-86d9-48e3-8421-2134c6f22a2d`, créé à **17:35:34 Europe/Paris**,
collecte terminée à **17:36:22**. Quatre jobs réussis et traités : le contrôle
général, deux expertises IA INFRA-01 et une recherche ciblée INFRA-01.
Dernier job terminé à **17:37:14**, décision à **17:37:14** ; aucun job en attente
au relevé. Consultation en lecture seule (`mode=ro`, `query_only=ON`).

| Source | Collecte générale | Décision finale |
| --- | --- | --- |
| INFRA-01 | 10 000 lignes, 18 groupes datés, tronquée | `investigate`, verdict KO conservé comme hypothèse |
| HA-01 | 5 535 lignes, 26 groupes dont 14 non datés, tronquée | `watch`, preuves déjà prises en compte, aucune nouvelle IA |
| LINKY-01 | 9 385 lignes, 16 groupes non datés, tronquée | `watch`, aucune nouvelle IA |
| ZWAVE-01 | 6 497 lignes, 8 groupes non datés, tronquée | `watch`, aucune nouvelle IA |

**Déduplication HA-01 confirmée en production** à **17:36:23** : la décision
déterministe explicite que les groupes ont déjà été pris en compte lors d'une
demande d'expertise. Les groupes restent présents et la troncature reste visible.
Le déploiement n'a pas provoqué une nouvelle expertise sur ces mêmes preuves.
La comparaison de fenêtres de durées différentes et l'interruption en plein cycle
restent des validations locales, non des scénarios exercés ici.

L'escalade INFRA-01 porte notamment sur deux nouveaux groupes : un groupe
critique associé aux journaux Vision à **17:35:10**, et un groupe d'erreur Agent
de catégorie Z-Wave à **17:11:14**. La recherche ciblée retourne zéro correspondance,
zéro groupe et `truncated=false` ; cela ne prouve pas la résolution générale.
Les deux retours IA sont KO, avec statut d'hypothèse ; Tsunade conserve la décision.

**Faux positif critique confirmé.** Une lecture journald bornée à vingt secondes
sur `ohana-vision.service` qualifie la ligne de 17:35:10 : niveau INFO (priorité 6),
accès GET, réponse **HTTP 200**, mot `critical` uniquement dans la cible HTTP.
Le détecteur interprétait un mot de l'URL comme une criticité du service. L'URL
et le journal brut n'ont pas été exportés ; seuls méthode, code et booléens de
qualification ont été affichés. Ce constat ne qualifie pas l'autre erreur Agent.

### Correction locale Katsuyu — qualification des journaux d'accès HTTP

Pour le format d'accès HTTP reconnu (`INFO: client - "METHOD cible HTTP/…" code`),
les mots contenus dans la cible ne déterminent plus l'anomalie, la catégorie ni
la criticité. Le niveau du journal et les messages hors cible restent examinés.
Les réponses **5xx sont reconnues comme erreurs**, y compris sans mot d'erreur
explicite ; une URL contenant `critical` ne transforme plus une erreur 500 en
anomalie critique. Une réponse 2xx/3xx/401 ne constitue pas à elle seule un incident
parce que son chemin contient `error`, `restart` ou `fatal`.

Le même traitement s'applique aux collectes générales et ciblées. Les recherches
ciblées conservent le nombre de correspondances. Le format non reconnu conserve
la détection existante ; les erreurs explicites et les suffixes critiques restent
détectés. Les cibles longues sont retirées de l'échantillon de classement avant
sa réduction, pour ne pas perdre le code HTTP et recréer une fausse criticité.

Reproduction initiale : **14 échecs sur les 20 cas HTTP ajoutés**. Après correction
et ajout des cas d'URL longue : **141 tests Katsuyu réussis**, suite complète,
dont 22 cas HTTP. Ruff, formatage et diff propres. **Local, non publié et non déployé.**
Agent n'a pas été modifié dans cette reprise. Aucun schéma de job ni configuration
modifié. Les anciens groupes et diagnostics persistés ne sont pas réécrits :
la correction s'appliquera aux nouvelles collectes, sans clôture automatique
fondée uniquement sur l'exclusion de ce message.

### Alignement de la roadmap — état vérifié le 20 septembre

Les cases sont alignées sur les preuves et limites du rapport. Les validations
cochées sont bornées au périmètre explicitement cité ; les critères globaux ne
sont pas déduits de la seule réussite d'un cycle.

| Domaine | État retenu dans la roadmap |
| --- | --- |
| Investigations ZWAVE-01 et métriques INFRA-01 | Validations bornées déjà acquises ; pannes toujours ouvertes |
| DNS/TCP/HTTP | Partiel : HTTP 405 réel et sa qualification sont acquis, contrairement à l'ancienne mention ; scénarios de panne restants |
| Absence de relance sur mêmes groupes | Acquis pour les expertises de journaux HA-01 sous Agent 1.29.12 ; reprise et interruption complétées par tests locaux |
| Arrivée de nouvelles observations | Validation antérieure conservée ; nouvelles données admises dans ce cycle, qualité du classement distincte |
| Hypothèses et retours structurés | Acquis sur les cycles de journaux examinés : types de jobs distincts, résultats traités, KO identifié comme hypothèse |
| Cycle de vie complet, confiance et responsabilité globale | Validation partielle ; aucune case générale cochée sur la seule base des cycles de journaux |
| Provenance, fraîcheur et secrets | Partiel : champs et `/stok` contrôlés, groupes sans date et audit exhaustif ouverts |
| Faux positifs et scénarios de panne | Ouverts : correction HTTP locale, `s6-rc` sans date et pannes contrôlées restant à exercer |
| Sortie de phase 1 | Non acquise ; seul le critère borné de non-relance d'un dossier de journaux inchangé est désormais coché |

### Prochaine validation nécessaire pour ce correctif

Après publication et déploiement **Katsuyu** par l'opérateur, conserver Agent
1.29.12 et lancer un nouveau contrôle manuel autorisé. Vérifier l'absence du faux
groupe critique d'accès Vision dans la nouvelle collecte (tant que la ligne est
encore dans la fenêtre), la conservation des vraies erreurs et le nombre de jobs
justifiés par de nouvelles preuves. Les anciennes conclusions restent historiques.
La validation réelle du nouveau classement nécessite cette mise à jour du worker.

Les sections suivantes décrivent les étapes antérieures : leurs mentions
« local / non déployé » sont datées et ne remplacent pas l'état courant ci-dessus.

### Contrôle Agent 1.29.11 / Katsuyu 0.8.13 — 20 septembre, 17:04–17:05

Versions confirmées en SSH après le déploiement opérateur. Le contrôle manuel
`9bb9ad2f-8a32-490a-a0bf-b06c7a98e331`, créé à **17:04:02 Europe/Paris**,
termine sa collecte à **17:04:39**. Ses quatre jobs (collecte générale, deux
analyses IA HA-01 et une recherche ciblée) sont réussis et traités.
Dernier job terminé à **17:05:36**, décision HA-01 à **17:05:37** ; aucun job
en attente au relevé. Base consultée avec `mode=ro` et `query_only=ON`.

| Source | Collecte générale | Décision finale |
| --- | --- | --- |
| INFRA-01 | 10 000 lignes, 14 groupes datés, tronquée | `watch`, sans nouvelle IA |
| HA-01 | 5 554 lignes, 26 groupes dont 14 non datés, tronquée | `investigate`, KO IA conservé comme hypothèse |
| LINKY-01 | 9 385 lignes, 16 groupes non datés, tronquée | `watch`, sans nouvelle IA |
| ZWAVE-01 | 6 567 lignes, 8 groupes non datés, tronquée | `watch`, sans nouvelle IA |

La recherche ciblée HA-01 rapporte **343 correspondances, 8 groupes et
`truncated=true`**. Aucun des quatre incidents n'est clôturé. Il n'y a pas de
corrélation temporelle dans ce contrôle. Le signalement de troncature est bien
présent ; le détail de chaque plafond Supervisor n'a pas été reconstitué ici.

Le snapshot transmis contient **HTTP 405 / `method_not_allowed`** : la
qualification du refus de HEAD est confirmée dans la preuve réellement envoyée.
Les **10 blocs structurés sont du JSON valide**, avec **2 réductions explicites** ;
un bloc supplémentaire est la note textuelle attendue `diagnostics.configuration`.
Aucun segment `/stok` non masqué dans les paramètres et résultats des nouveaux
jobs examinés. Ce contrôle ciblé ne constitue pas un audit exhaustif des secrets,
ni une preuve que tous les groupes critiques sont conservés dans tous les volumes.

**Défaut de relance confirmé :** le contrôle précédent
`23788e70-c9a2-4d55-a847-59885e2792a9`, lancé à **16:41:21**, avait déjà conduit
à deux analyses HA-01 et à la même recherche ciblée. Les **six groupes déclencheurs**
de 17:04 sont inchangés par rapport à cette collecte : même signature, criticité,
catégorie, compteur et dernière date ; cinq restent marqués `new`.
Les deux collectes sont tronquées et ne remplacent donc pas la baseline complète.
L'évolution d'autres groupes et le déplacement de fenêtre ne justifient pas à eux
seuls une nouvelle expertise de ces mêmes éléments. Les signatures brutes n'ont
pas été exportées ; l'égalité a été vérifiée sur le serveur et seuls les compteurs
ont été affichés.

### Correctifs locaux Agent après ce contrôle — 20 septembre

1. **Mémoire des preuves déjà prises en compte.** Les groupes ayant conduit à
   une demande d'expertise reçoivent une empreinte persistée, indépendante du
   libellé, de l'ordre, de la baseline et du déplacement de début de fenêtre.
   Signature filtrée, criticité, catégorie, compteur et dernière date identifient
   la preuve ; deux représentations du même instant sont équivalentes.
   Une répétition reste en surveillance avec une raison explicite, sans nouvelle IA.
   Les preuves et hypothèses restent conservées ; cela ne clôture pas l'incident
   et ne signifie pas que le LLM a examiné individuellement tous les groupes
   d'un extrait borné. L'absence de worker ne marque pas les preuves comme traitées.
2. **Reprise et historique existant.** L'empreinte est enregistrée dès le diagnostic
   de mise en file : une interruption avant la fin de revue ne suffit pas à relancer
   l'expertise. Les empreintes restent consultables au-delà des 1 000 événements
   affichés. Les anciens cycles reconnaissables dans l'historique récent sont
   exploités sans réécriture ; leurs empreintes réutilisées deviennent durables
   lors de la prochaine revue. Un ancien cycle hors de cet historique et dépourvu
   d'empreinte n'est pas garanti dédupliqué rétroactivement.
3. **Durées de comparaison compatibles.** La baseline vient de la dernière
   collecte complète de même durée réelle. Une collecte de deux heures ne sert
   plus de référence à une fenêtre de vingt-quatre heures. Sans référence compatible,
   aucune baseline n'est inventée. Les tests incluent le changement d'heure
   Europe/Paris. Une durée identique ne garantit pas la même activité ni la fraîcheur
   des groupes non datés, et ne corrige pas un ancien flag de complétude erroné.

**166 tests Agent réussis** : rejeux, historique antérieur, interruption après
mise en file, limite de 1 000 événements, nouvelles occurrences/dates/signatures/
criticités/corrélations, diagnostic opérateur, indisponibilité du worker,
sélection de durée, incidents, investigations, suivis et jobs. Ruff, formatage
et contrôle de diff propres. Aucun schéma de job ni paramètre de configuration
modifié. **Corrections locales Agent uniquement, non publiées et non déployées.**
Katsuyu n'a pas été modifié dans cette reprise.

### Validation du correctif de relance — désormais confirmée sur HA-01

Le contrôle Agent 1.29.12 de 17:35 décrit plus haut confirme HA-01 sans nouvelle
IA, avec raison explicite et troncature visible. Les preuves nouvelles restent
admissibles selon la politique ; leur qualification fait l'objet du correctif
HTTP local suivant. Le diagnostic explicitement demandé et les cas d'interruption
restent couverts par les tests décrits dans le lot précédent.

Les messages `s6-rc` sans date, la comparabilité effective des contenus collectés,
l'audit exhaustif des secrets et les scénarios de panne contrôlée restent ouverts.
Leurs cases de roadmap ne sont pas déclarées validées par ces tests.

### Reprise locale — priorité des anomalies critiques dans Katsuyu, 20 septembre

Le lot de stabilisation ci-dessous est déjà présent dans les dépôts à la reprise.
Un défaut complémentaire a été reproduit dans les deux parcours Katsuyu :
64 groupes fréquents pouvaient évincer un groupe critique rare avant même
la réduction du dossier IA par Agent. Les deux tests de reproduction échouaient.

Les collectes générales et ciblées sélectionnent désormais les groupes critiques
en priorité, puis conservent l'ordre par fréquence au sein de chaque priorité.
Les messages `CRITICAL` et `FATAL` seuls sont également reconnus : auparavant,
un autre mot tel que `failure` était nécessaire pour les détecter.
Le plafond de 64 groupes et `truncated=true` restent appliqués ; les occurrences,
les correspondances ciblées et les dates inconnues ne sont pas modifiées.
Au-delà de 64 groupes critiques, l'extrait reste nécessairement incomplet.

Validation locale : **119 tests Katsuyu réussis** (suite complète), dont quatre
cas de groupe critique rare pour les deux collectes et les deux niveaux.
Les **98 tests Agent** des investigations, preuves, suivis, cycles de journaux
et rejeux de corrélations passent également sur le lot existant.
Ruff, formatage et contrôle de diff validés sur les fichiers modifiés.
Les anciens résultats persistés restent inchangés. **Non publié, non déployé.**

Ce correctif complète le lot Agent/Katsuyu à déployer ensemble pour la prochaine
validation réelle décrite ci-dessous. La qualification `s6-rc`, la comparabilité
des fenêtres, l'audit exhaustif des secrets et les pannes contrôlées restent ouverts ;
cette reprise ne les déclare ni résolus ni bloqués techniquement par le déploiement.

### Lot de stabilisation avant prochaine release — 20 septembre

Développement local demandé après le contrôle Agent 1.29.10. Les changements
concernent **Agent et Katsuyu**, sans nouveau champ de configuration ni changement
de schéma des jobs. Les ajouts de métadonnées restent dans le JSON des preuves.
Publication et déploiement sont laissés à l'opérateur.

| Défaut / limite | Changement local | Validation représentative |
| --- | --- | --- |
| Journald plafonné silencieusement à 10 000 lignes | Demande de 10 001 lignes, conservation des 10 000 dernières et troncature explicite en cas de dépassement | 9 999 / 10 000 / 10 001 lignes et plafond d'octets |
| Limites Supervisor masquées ou ambiguës | Ligne témoin par journal ; dépassement d'octets distingué d'un volume exactement égal au plafond | Limites de lignes et d'octets, collecte Core/add-on |
| Repli Core après échec Supervisor | Résultat déclaré incomplet ; exception limitée à son type, sans message brut | Erreur contenant des identifiants fictifs, absents des preuves |
| Collecte tronquée considérée stable | Décision déterministe `watch` avec limite explicite ; une preuve critique reste admissible à l'investigation | Anomalies connues, source tronquée et anomalie critique |
| Collecte vide incomplète clôturant un incident | Clôture seulement avec `truncated=false` booléen ; maintien de l'incident et de l'historique séparé | Reprise SQLite, rejeu idempotent, collectes incomplètes successives puis collecte complète |
| Preuve IA coupée au milieu du JSON | Réduction structurelle sous 8 000 caractères, marqueur `_evidence_truncated`, compteurs d'origine préservés | 64 groupes longs, caractères Unicode, secrets fictifs, objets/listes/chaînes volumineux |
| Contexte temporel perdu dans le dossier IA | Conservation des dates/fenêtres, comptage des groupes sans date et distinction historique / collecte actuelle | Nouvelle collecte et réévaluation, sans dater artificiellement les lignes |
| Anomalie critique omise car placée en fin de liste | Priorité aux groupes critiques puis aux évolutions dans l'extrait borné | Finding critique placé en 64e position, conservé après réduction |
| HEAD 405 ambigu et sondes saturées | Qualification explicite du 405 ; retour immédiat `busy` pour les opérations non démarrées | Serveur HTTP local, erreurs DNS/TCP/TLS simulées et saturation du sémaphore |

Les preuves déjà persistées ne sont pas réécrites. Les anciens `truncated=false`
incorrects ne deviennent pas fiables rétroactivement ; le contrôle de 1.29.10
ci-dessous en fournit un exemple. Aucune ancienne clôture n'est rouverte
automatiquement. La conservation des références repose encore sur les flags
historiques disponibles, dont cette limite doit être connue.

La qualification détaillée des messages `s6-rc` sans date, les fenêtres de
comparaison différentes et l'audit exhaustif de toutes les formes de secrets
restent ouverts. Les tests de panne locaux ne valent pas scénario de panne
validé sur Konoha. La phase 1 n'est pas déclarée terminée.

### Contrôle Agent 1.29.10 / Katsuyu 0.8.11 — 20 septembre, 12:16–12:20

Versions confirmées en SSH. Contrôle manuel
`14823dee-b33f-404a-8ec3-d02cb85b4734`, créé à **12:16:14 Europe/Paris**,
collecte terminée à **12:18:35**, dernier job à **12:20:20**, dernière décision
à **12:20:22**. Sept jobs réussis et traités : une collecte générale, quatre
analyses IA, deux recherches ciblées. Aucun job en attente au relevé.
Consultation SQLite en lecture seule (`mode=ro`, `query_only=ON`), sans nouveau job.

**HTTP exercé en production :** les snapshots INFRA-01 à **12:19:25** et HA-01
à **12:19:44** sélectionnent `supervisor-http:ha-01`, port **8123**, origine
`backup.targets.url`. DNS et TCP réussissent, **HEAD / répond 405**. Les deux
preuves sont transmises aux réévaluations. Cela confirme sélection, exécution et
transmission ; le refus de HEAD ne prouve ni panne ni santé applicative complète.
Six sondes sont présentes, cinq cibles sont explicitement omises par le plafond.

**Références conformes :** comparaison exacte signatures/compteurs avec les
dernières collectes déclarées complètes : INFRA-01 **17**, HA-01 **26**, LINKY-01
**16**, ZWAVE-01 **9** groupes. Ce cycle n'intercale pas de contrôle déclaré
tronqué ; l'exclusion de tels contrôles reste couverte par les tests locaux.

| Source | Résultat | Décision finale |
| --- | --- | --- |
| INFRA-01 | 16 groupes, 3 en hausse ; recherche ciblée vide | `watch`, `INSUFFICIENT_CONTEXT` |
| HA-01 | 26 groupes, 1 nouveau, 12 non datés ; 348 correspondances et 6 groupes ciblés | `investigate`, KO IA conservé comme hypothèse |
| LINKY-01 | 16 groupes stables, tous non datés | `stable`, sans nouvelle IA |
| ZWAVE-01 | 9 groupes stables, dont 8 non datés | `stable`, sans nouvelle IA |

Trois corrélations temporelles, sans preuve de causalité. Les résultats généraux
et ciblés déclarent `truncated=false`, **mais cette déclaration est infirmée pour
la collecte générale INFRA-01** : une seconde lecture bornée de la même fenêtre,
avec seulement les compteurs affichés, retourne **10 001 lignes / 1 716 298 octets**.
La fenêtre dépassait le plafond journald de 10 000 lignes, silencieux dans 1.29.10.
Les compteurs exacts de contenu peuvent évoluer avec la rétention ; la présence
d'au moins 10 001 lignes démontre le dépassement lors de cette vérification.
Le correctif local décrit ci-dessus couvre ce défaut ; aucune modification de
production n'a été effectuée pendant ce contrôle.

### Protocole du lot précédent — contrôles complémentaires restant à exercer

1. Le lot Agent 1.29.11 / Katsuyu 0.8.13 est désormais déployé et le contrôle
   de 17:04 décrit plus haut en valide une partie ; conserver les vérifications
   complémentaires ci-dessous sans les considérer toutes acquises.
2. Vérifier les flags de troncature à chaque étape, particulièrement INFRA-01
   lorsque le journal dépasse 10 000 lignes. Ne pas considérer les anciennes
   références inexactes comme une preuve de complétude historique.
3. Vérifier qu'une collecte vide tronquée maintient l'incident actif, sans perte
   de son historique et sans réévaluation coûteuse automatiquement répétée.
4. Vérifier le 405 HTTP qualifié, les limites DNS/TCP/TLS et les cibles omises
   dans la preuve réellement transmise à Katsuyu.
5. Sur un dossier volumineux, vérifier que tous les contenus sont du JSON valide,
   que la réduction est explicite et que les groupes critiques sont conservés.
6. Exercer séparément les pannes contrôlées prévues par la roadmap, avec cible,
   impact, durée maximale et retour sain définis avant toute perturbation.

### Références après collecte tronquée — développement local du 20 septembre

La poursuite locale révèle un défaut complémentaire à la correction Katsuyu :
Agent prenait le dernier résultat réussi de chaque source comme baseline,
même tronqué. Un résultat tronqué vide effaçait les groupes de référence ; un
résultat tronqué non vide remplaçait leurs compteurs. Les deux cas sont
reproduits avant correction dans le parcours API de création de contrôle.

Agent choisit désormais la dernière collecte réussie avec `truncated=false`
explicitement booléen, source par source. Sans collecte complète connue, aucune
référence n'est créée pour cette source. Une collecte complète vide remplace
toujours son ancienne référence. Aucun résultat historique n'est modifié : la
sélection s'applique aussi aux jobs déjà persistés après mise à jour.

**16 tests de cycle/rejeu réussis**, Ruff, formatage et diff Agent validés.
Les scénarios couvrent contrôle global puis partiel, résultats échoués ignorés,
collectes tronquées vides ou non vides, source sans référence complète et
réouverture SQLite avant création et relecture du prochain job.

**Local, non publié et non déployé**, conformément au choix de l'opérateur de
faire la release et le déploiement ultérieurement. Cette correction protège les
références ; elle ne rend pas les fenêtres temporelles identiques, ne qualifie
pas les messages sans date et ne garantit pas qu'une anomalie nouvelle vue
uniquement dans des collectes tronquées ne sera jamais réexaminée. Le correctif
HTTP local précédent reste également en attente de publication/déploiement.

### HTTP depuis la cible Supervisor configurée — développement local du 20 septembre

Suite au contrôle 1.29.9, le runtime Agent réutilise désormais l'URL de la cible
Supervisor activée dans `backup.targets` pour compléter les candidats HTTP.
La sélection suit celle de l'inspection existante : HA-01 pour INFRA-01, sinon
la cible du nœud demandé. Aucun port ni URL n'est inventé, aucune configuration
de production n'est modifiée et aucun nouveau paramètre de configuration ajouté.

La sonde utilise uniquement hôte, port et schéma HTTP/HTTPS, avec `HEAD /`
sans authentification ni redirection. Les URL mal formées ou avec identifiants
intégrés sont ignorées. Chemins, paramètres et fragments ne rejoignent pas les
preuves. La provenance est `backup.targets.url`, avec une cible
`supervisor-http:<id>`. Déduplication et plafonds existants sont conservés ;
les services du nœud demandé restent prioritaires et peuvent remplir le budget.

**92 tests réussis**, couvrant lecture de configuration, sélection sans service
HTTP dans l'architecture, URL invalides/avec identifiants, absence de secrets,
déduplication, investigations, suivis et démarrage du runtime. Ruff et formatage
validés. Les tests HTTP locaux HEAD 302/401/403/503 sans redirection passent aussi.

**Local, non publié et non déployé.** Après déploiement autorisé, vérifier une
nouvelle investigation : provenance de la cible, résultat HTTP ou erreur de
transport explicite et transmission à Katsuyu. HTTP en production reste ouvert,
comme les journaux sans date, les scénarios de panne et l'audit complet des secrets.

### Contrôle Agent 1.29.9 / Katsuyu 0.8.11 — 20 septembre, 10:42–10:45

Versions confirmées en SSH : Agent **1.29.9**, worker **0.8.11** (présence
à 11:17:36 Europe/Paris). Contrôle manuel
`c10e4bdc-efca-45f2-8899-431e55578e4a`, créé à **10:42:52** : sept jobs
réussis et traités, dernière complétion à **10:45:31**, dernière décision
à **10:45:32**. Aucun job en attente lors du relevé. SQLite consulté avec
`mode=ro` et `PRAGMA query_only=ON` ; aucun job créé ni changement de production.

| Source | Collecte générale | Décision finale |
| --- | --- | --- |
| INFRA-01 | 17 groupes, 1 nouveau, 2 en hausse ; recherche ciblée vide | `watch`, `INSUFFICIENT_CONTEXT`, cause non confirmée |
| HA-01 | 26 groupes, 6 nouveaux ; recherche ciblée : 350 correspondances, 6 groupes | `investigate`, verdict IA KO conservé comme hypothèse |
| LINKY-01 | 16 groupes stables, tous sans date exploitable | `stable`, aucune nouvelle IA |
| ZWAVE-01 | 9 groupes, 1 nouveau, 8 connus dont 8 sans date exploitable | `watch`, aucune nouvelle IA |

Les quatre sources générales et les deux recherches ciblées déclarent
`truncated=false`. Aucun plafond local de 200 000 lignes ou 64 groupes n'est
atteint : ce cycle ne valide donc pas en production le cas de dépassement
corrigé dans Katsuyu. Aucune corrélation ; 38 groupes déclarés disparus, ce qui
ne prouve pas la résolution des incidents. HA-01 comporte 12 groupes non datés.

**Sélection bornée confirmée, HTTP toujours non exercé :** les snapshots
INFRA-01 à **10:44:45** et HA-01 à **10:44:59** contiennent six cibles et
quatre `omitted_targets` avec `reason=probe_limit`. Ils sont transmis aux
réévaluations. DNS et TCP 53/1883/3000 réussissent ; aucun résultat HTTP.
La configuration `/etc/ohana-agent/infrastructure.yaml`, consultée uniquement
sur les types et ports, ne déclare aucun service Home Assistant/HTTP ni port
HTTP ; les endpoints des nœuds ne portent pas de schéma HTTP. La priorité HTTP
ne peut donc sélectionner aucune cible admissible. Le défaut d'ordre corrigé
dans l'exemple ne suffit pas à couvrir cette architecture réelle.

Prochaine étape : préparer une cible HTTP explicitement configurée et sa
validation, sans déduire une URL de l'identité du nœud. Aucun changement de
configuration effectué ici. La qualification des journaux sans date reste
ouverte. Deux anciens contrôles de 04:45 et 06:03 sont `TIMEOUT`, traités ;
leur cause n'a pas été examinée et ne se confond pas avec le cycle manuel réussi.

Les corrections 1.29.9/0.8.11 sont désormais déployées ; les mentions locales
ci-dessous décrivent les passes historiques. Aucun audit des assets de release
n'a été effectué pendant cette vérification.

### Limites d'analyse des journaux — correction locale suivante du 19 septembre

L'examen du code Katsuyu révèle que le contrôle général plafonnait l'analyse
à 200 000 lignes et la restitution à 64 groupes par source sans reporter ces
deux limites dans `truncated`. Le parcours ciblé les signalait déjà. Une
absence dans les groupes rendus pouvait également alimenter
`disappeared_anomalies` malgré une collecte tronquée ou une source non collectée.
Ces défauts sont reproduits localement ; rien dans cette passe ne démontre
qu'un contrôle historique de production a atteint ces plafonds.

Le contrôle général signale maintenant toute troncature par octets, lignes ou
groupes. Les anomalies absentes ne sont déclarées disparues que pour les
sources effectivement collectées et non tronquées. Une disparition reste
l'absence d'un groupe dans cette collecte, pas une résolution de l'incident.
Les seuils, les compteurs et les schémas de jobs restent inchangés.

**57 tests handlers/IA réussis**, dont dix cas de régression : exactement
200 000 lignes / 64 groupes et dépassement, collecte générale et ciblée,
source tronquée et source absente d'un contrôle partiel. Les nouvelles
limites remontent dans les résultats structurés consommés par Agent.

**Local, non publié et non déployé.** Aucun contrôle réel relancé, aucun
résultat historique réécrit. Cette correction ne valide pas la fraîcheur des
messages `s6-rc` sans date, la qualification de leurs démarrages, ni la
comparabilité des compteurs entre fenêtres ou collectes incomplètes. Ces
points restent ouverts, avec HTTP en production et les scénarios de panne.

### Reprise — couverture HTTP des snapshots, correction locale du 19 septembre

La reprise retrouve un test non terminé sur la sélection des sondes. Le défaut
est reproduit avec l'architecture d'exemple : Home Assistant est le huitième
point d'accès, alors que la sélection s'arrêtait dès six cibles avec inspection
de configuration, sept sans. Pour INFRA-01, ZWAVE-01 et LINKY-01, aucun HTTP
n'était alors sélectionné. Cela explique l'absence sur cet exemple ; la
configuration de production n'a pas été relue pendant cette passe.

Agent construit désormais les candidats avant d'appliquer le plafond : services
du nœud demandé d'abord, puis HTTP/HTTPS, puis autres cibles, en conservant
l'ordre de déclaration dans chaque priorité et la déduplication des points
d'accès. Si les services du nœud demandé remplissent le budget, ils restent
prioritaires. `omitted_targets` expose les cibles écartées avec
`reason=probe_limit` ; une cible non testée n'est pas considérée saine.

**68 tests ciblés réussis**, Ruff et formatage validés : quatre nœuds avec et
sans inspection, priorité locale lorsque le budget est rempli, limites de
sondes, HTTP HEAD local 302/401/403/503 sans redirection, inspection Supervisor,
investigations et suivis. Le parcours de réévaluation conserve la liste des
cibles omises dans les preuves transmises à Katsuyu.

**Local, non publié et non déployé.** Aucun job réel lancé ni changement de
production. Les limites de six/sept sondes et dix/six secondes restent
inchangées. Aucun exemple de configuration ni contrat de job modifié ; le
champ ajouté appartient au snapshot JSON des preuves. Les anciens snapshots
restent inchangés. La validation HTTP sur une nouvelle investigation réelle
reste à faire après déploiement autorisé ; qualification des journaux Z-Wave,
scénarios de panne et audit complet des secrets restent ouverts.

### Contrôle Agent 1.29.8 — 19 septembre, 17:50–17:53

Agent **1.29.8** et Katsuyu **0.8.10** confirmés en SSH ; commit local Agent
`d9d3eee`, dépôt propre. Contrôle manuel
`1db9a8e0-6a79-4a23-83a0-432e02247cb0`, créé à **17:50:21 Europe/Paris**.
Sept jobs réussis et traités (collecte générale, quatre analyses IA et deux
recherches ciblées), dernier résultat à **17:53:50**, dernière décision à
**17:53:51**. Aucun job restant. Consultation en lecture seule ; aucun job
supplémentaire ni changement de production pendant cette vérification.

**Sélection Supervisor Z-Wave validée dans le cycle réel :** snapshot à
**17:51:53**, `requested_node=zwave-01`, origine `zwave-01 / Supervisor`,
`addon_selection.status=matched`. L'add-on `a0d7b954_zwavejs2mqtt` est sélectionné,
version **7.7.0**, état **started**, CPU **0,02 %**, mémoire **3,14 %**.
Cette preuve est persistée dans l'événement d'investigation et transmise à
la réévaluation `782e9e0c-1256-45bf-b82e-1f8b29919c29`. DNS et TCP 3000
réussissent depuis Agent. Cela valide la collecte et sa transmission, pas la
santé de chaque nœud Z-Wave ni tous les cas de panne Supervisor.

L'inspection INFRA-01 à 17:51:44 sélectionne toujours Mosquitto sur HA-01 :
`core_mosquitto`, **7.1.1**, `started`, CPU **0,08 %**, mémoire **0,44 %**.
Elle est également transmise à la réévaluation. Les endpoints des deux
snapshots ne contiennent **aucun résultat HTTP** : ce point reste ouvert.

| Source | Collecte générale | Décision finale |
| --- | --- | --- |
| INFRA-01 | 12 groupes connus, 1 en hausse, 1 stable, 2 nouveaux | `investigate`, hypothèses à vérifier ; recherche ciblée sans correspondance ni anomalie |
| HA-01 | 20 stables, 1 nouveau | `watch`, sans IA |
| LINKY-01 | 15 stables, 1 connu | `stable`, sans IA |
| ZWAVE-01 | 8 connus, 38 nouveaux | `watch` après investigation et réévaluation ; recherche ciblée sans correspondance ni anomalie |

Aucune corrélation et collectes déclarées non tronquées. Les 46 groupes Z-Wave
se répartissent en 36 `restart`, 9 `zwave` et 1 `network` ; plusieurs nouveaux
groupes n'ont pas de date exploitable. Ils ne constituent pas 38 pannes
actuelles démontrées. La fraîcheur et la pertinence de ces groupes restent
à examiner ; une recherche ciblée vide ne prouve pas la résolution globale.

Le correctif Supervisor est désormais déployé et confirmé sur ZWAVE-01.
La case des investigations automatiques ZWAVE-01 est cochée pour ce cycle
borné de lecture seule. HTTP, qualification des journaux et scénarios de panne
restent hors de cette validation.

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
