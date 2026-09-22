# Roadmap Ohana

## État de référence

Cette roadmap prend **Ohana-Platform 1.0.100** comme baseline fonctionnelle de départ.

Les versions indiquées dans les validations de chaque phase peuvent être ultérieures à cette composition.

Composition de référence :

- Ohana-Agent 1.29.0 ;
- Ohana-Vision 1.22.14 ;
- Ohana-Katsuyu 0.8.7 ;
- Ohana-Shizune 0.3.0 ;
- Ohana-Installer 1.14.3.

L’architecture fonctionnelle actuelle est :

```text
                           OHANA
                             │
                           KONOHA
                             │
              ┌──────────────┴─────────────┐
              │                            │
           INFRA-01                      BUBULE
              │                            │
         OHANA-AGENT                    KATSUYU
        ┌─────┴─────┐                      ▲
        │           │                      │
   SHIKAMARU     TSUNADE ──────────────────┘
        │           │
        │           │
        └─────┬─────┘
              │
        ┌─────┴─────┐
        │           │
      VISION      SHIZUNE
```

Les noms techniques historiques restent stables :

- **Ohana-Agent** : runtime technique hébergeant Shikamaru et Tsunade ;
- **Ohana-Vision** : cockpit technique complet ;
- **Ohana-Katsuyu** : worker lourd exécuté sur Bubule ;
- **Ohana-Shizune** : PWA compagnon personnelle ;
- **Ohana-Installer** : installation, mise à jour et migrations ;
- **Ohana-Platform** : architecture commune, contrats et compositions de releases.

Les noms fonctionnels décrivent les responsabilités :

- **Konoha** : infrastructure gérée ;
- **Shikamaru** : observation, mesure, détection et vérification ;
- **Tsunade** : orchestration des incidents, investigations déterministes, coordination, décisions et réparations supervisées ;
- **Katsuyu** : traitements lourds, analyses avancées, corrélations complexes et IA locale sur Bubule ;
- **Shizune** : interaction personnelle et décisions utilisateur.

---

# Philosophie générale de la roadmap

Une phase établit une **capacité fonctionnelle minimale fiable**.

Elle n’a pas pour objectif d’épuiser tous les cas possibles liés à cette capacité.

Chaque phase distingue désormais trois catégories.

## Critères de sortie

Les quelques propriétés indispensables qui doivent être démontrées avant de considérer la capacité suffisamment stabilisée pour avancer.

## Durcissement continu

Les améliorations de couverture, robustesse, performance, qualité, sécurité ou lisibilité qui doivent continuer à évoluer mais ne bloquent pas automatiquement la phase suivante.

Un élément de durcissement redevient bloquant lorsqu’il révèle une violation d’un invariant fondamental.

## Évolutions futures

Les capacités supplémentaires qui ne répondent pas encore à un besoin opérationnel suffisamment concret.

L’objectif est d’éviter qu’une phase devienne impossible à terminer parce que chaque nouveau cas limite découvert est ajouté à ses conditions de sortie.

---

# Phase 1 — Stabilisation de Tsunade

Suivi : [campagne de validation et premiers constats](docs/Phase-1-Stabilisation-Tsunade.md).

Phase démarrée le 15 septembre 2026.

Le périmètre de cette phase a été recentré le 20 septembre 2026.

L’objectif n’est plus de valider exhaustivement toutes les investigations, tous les protocoles, tous les faux positifs et tous les scénarios de panne possibles avant de poursuivre la roadmap.

La Phase 1 doit établir que **Tsunade possède un socle suffisamment fiable pour diagnostiquer Konoha au quotidien**, sans boucle d’investigation, sans confusion entre faits et hypothèses, sans dépendance critique à Katsuyu et sans décision artificielle lorsque les preuves sont insuffisantes.

Les validations plus fines restent importantes mais deviennent du durcissement continu.

---

## Objectif

Valider que Tsunade peut prendre en charge de manière fiable le cycle de diagnostic d’un incident avant d’étendre ses responsabilités aux réparations supervisées de la Phase 2.

Le comportement cible est :

```text
Shikamaru observe
        │
        ▼
Tsunade ouvre ou met à jour l'incident
        │
        ▼
Investigation déterministe
        │
        ├── preuves suffisantes
        │        │
        │        ▼
        │    diagnostic
        │
        ├── traitement lourd nécessaire
        │        │
        │        ▼
        │     Katsuyu
        │   déterministe
        │        │
        │        ▼
        │      résultat
        │
        ├── expertise réellement nécessaire
        │        │
        │        ▼
        │     Katsuyu
        │        IA
        │        │
        │        ▼
        │     hypothèses
        │
        └── preuves insuffisantes
                 │
                 ▼
        INSUFFICIENT_CONTEXT
```

Dans tous les cas, **Tsunade reste propriétaire de l’incident et de la décision finale**.

Katsuyu fournit une capacité de calcul ou d’expertise.

Il ne devient ni le moteur d’orchestration de l’incident ni la source de vérité sur l’état de Konoha.

---

## Invariants fondamentaux

### 1. Tsunade reste responsable de l’incident

Tsunade doit conserver :

- l’état de l’incident ;
- les observations ayant conduit à son ouverture ;
- les preuves collectées ;
- les investigations réalisées ;
- les éléments encore manquants ;
- les éventuelles contributions de Katsuyu ;
- la décision de poursuivre, surveiller ou arrêter l’investigation.

Une réponse Katsuyu ne modifie jamais directement l’état final d’un incident.

---

### 2. Le déterministe reste prioritaire

Tsunade doit pousser les investigations déterministes aussi loin que raisonnablement possible avant de demander une expertise IA.

Katsuyu peut être utilisé pour :

1. un **traitement déterministe lourd**, lorsque le volume ou le coût du traitement n’est pas adapté à INFRA-01 ;
2. une **expertise IA**, lorsqu’une interprétation complexe ou l’élaboration d’hypothèses apporte réellement une information supplémentaire.

Un appel à Katsuyu ne doit pas impliquer automatiquement l’utilisation du LLM.

Un incident simple doit pouvoir être traité sans réveiller Bubule lorsque Katsuyu n’apporte aucune valeur.

---

### 3. Faits, conclusions et hypothèses restent distincts

Tsunade doit distinguer explicitement :

- l’observation Shikamaru ;
- la preuve collectée ;
- le résultat d’un contrôle déterministe ;
- la conclusion déterministe ;
- les informations manquantes ;
- les hypothèses ;
- les contributions de Katsuyu ;
- les limites du diagnostic.

Une expertise IA ne transforme jamais automatiquement une hypothèse en fait établi.

Une absence de preuve ne constitue jamais une preuve d’absence.

---

### 4. Une investigation doit toujours pouvoir s’arrêter

Chaque nouvelle étape doit être justifiée par :

- une nouvelle observation ;
- une nouvelle preuve ;
- une information manquante identifiable ;
- ou une décision explicite du moteur d’investigation.

Le même dossier ne doit pas provoquer indéfiniment :

```text
investigation
    ↓
Katsuyu
    ↓
réévaluation
    ↓
Katsuyu
    ↓
...
```

Lorsque poursuivre n’apporte plus raisonnablement d’information supplémentaire, Tsunade doit pouvoir terminer en :

- `MONITORING` ;
- `INSUFFICIENT_CONTEXT` ;
- `INVESTIGATION_BLOCKED` ;
- ou dans un autre état terminal explicitement défini.

`INSUFFICIENT_CONTEXT` constitue un résultat valide lorsqu’aucune preuve supplémentaire raisonnable ne peut être obtenue.

---

### 5. Katsuyu reste optionnel pour le fonctionnement essentiel

L’indisponibilité de Bubule ou de Katsuyu ne doit pas empêcher :

- Shikamaru d’observer Konoha ;
- Tsunade de recevoir et suivre les incidents ;
- les investigations déterministes réalisables sur INFRA-01 ;
- la conservation de l’état de l’incident.

Une expertise impossible doit être explicitement en attente, bloquée ou en échec.

Elle ne doit jamais être remplacée par une conclusion artificielle.

---

### 6. Les preuves restent exploitables et sûres

Les preuves utilisées par Tsunade doivent conserver, lorsque l’information existe :

- leur provenance ;
- leur cible ;
- leur fenêtre temporelle ;
- leur horodatage ;
- leur état de complétude ou de troncature ;
- leur relation avec l’incident.

Une preuve ancienne ou incomplète ne doit pas être présentée comme une représentation certaine de l’état actuel.

Les secrets connus et données sensibles techniques ne doivent pas être transmis inutilement dans les dossiers d’investigation ou les demandes Katsuyu.

---

### 7. Le résultat doit être compréhensible

Pour un incident représentatif, Vision doit permettre de comprendre sans consulter directement les bases internes :

1. ce que Shikamaru a observé ;
2. pourquoi l’incident a été ouvert ;
3. ce que Tsunade a testé ;
4. quelles preuves ont été obtenues ;
5. ce qui est établi ;
6. ce qui reste hypothétique ;
7. si Katsuyu a été utilisé ;
8. pourquoi Katsuyu a été utilisé ;
9. quel résultat il a retourné ;
10. pourquoi Tsunade a retenu son état final.

---

## Validation représentative

### Outillage de validation : Ohana Sandbox

Le cycle attendu est développement local → validation Sandbox → release →
déploiement → vérification opérationnelle. Depuis la racine d'Ohana-Platform :

```powershell
# Scénarios locaux, bases temporaires et sondes simulées
.\sandbox\run.ps1 run all

# Journaux : code local Agent/Katsuyu/Tsunade, avant toute release
.\sandbox\run.ps1 run all --exercise-logs

# Full-stack local : worker HTTPS réel, IA locale réelle et Vision dans Chromium
.\sandbox\run.ps1 run --full-stack

# Recette du déploiement réel en lecture seule
.\sandbox\run.ps1 post-deploy agent 1.29.14

# Recette puis déclenchement et suivi d'un contrôle réel des journaux
.\sandbox\run.ps1 post-deploy agent 1.29.14 --exercise-logs
```

La version passée à `post-deploy` est la version Agent attendue sur INFRA-01 ;
elle doit être adaptée au déploiement à vérifier.

`run --exercise-logs` utilise le véritable analyseur Katsuyu local sur des
journaux locaux, puis traite son résultat dans Agent/Tsunade avec des bases
temporaires. `--logs-file` et `--window-end` permettent de rejouer un journal
historique. Ce parcours ne pilote pas à lui seul le navigateur, la boucle réseau
réelle du worker ni le runtime LLM.

Ces dimensions sont désormais couvertes par `run --full-stack`.

Le dernier passage full-stack propre du **22 septembre 2026** exerce un worker
Katsuyu réel par HTTPS avec certificat local vérifié, le cycle réseau

`register → next → source → heartbeat → complete`,

une analyse déterministe réelle des journaux, puis une inférence locale réelle
via llama.cpp avec le modèle Ministral.

Contrairement au parcours précédent, l'expertise IA n'est plus déclenchée par
une demande explicite de l'opérateur. Le journal de laboratoire contient un
incident volontairement ambigu : deux erreurs de template Home Assistant liées
à une valeur `unavailable`.

Agent traite d'abord les journaux, ouvre l'incident `logs.health`, constate que
les éléments déterministes justifient une analyse complémentaire et crée
**automatiquement** un unique job `ai.inference`.

Le vrai modèle Katsuyu :

- classe l'anomalie `KO` ;
- produit au moins une hypothèse ;
- indique explicitement le contexte restant à vérifier ;
- ne transforme pas cette hypothèse en fait établi.

Tsunade conserve le résultat avec :

- `diagnostic_level=PROBABLE` ;
- `epistemic_status=hypothesis` ;
- décision `investigate` ;
- aucune décision `action_required` fondée sur la seule IA.

Une investigation concrète en lecture seule est proposée pour l'entité Home
Assistant concernée.

L'exécution finale a généré **615 tokens**. Vision restitue l'analyse Katsuyu et
le résumé IA dans Chromium, en desktop et mobile, sans débordement horizontal,
erreur JavaScript ni réponse HTTP serveur en erreur.

Les bases, le journal déclencheur et l'infrastructure de ce laboratoire restent
locaux et temporaires. Ce PASS démontre la valeur technique et fonctionnelle du
LLM Katsuyu sur un cas ambigu, mais **ne constitue pas encore un incident ambigu
réellement observé sur Konoha**.

Les bases, le journal déclencheur et l'infrastructure de ce laboratoire restent locaux et temporaires : ce PASS ne constitue pas une panne réellement exercée sur Konoha.

Les **scénarios locaux de la Sandbox** couvrent notamment les niveaux de diagnostic,
les échecs de sondes, l'absence de Katsuyu, la reprise des suivis persistés
et le diagnostic local pendant l'attente d'un worker. Le scénario
`followup-evidence-cycle` couvre aussi une collecte autorisée suivie d'une
réévaluation : preuves initiales conservées, limites factuelles respectées et
terminaison sans relance après livraison répétée des résultats et reprise.
Le scénario `teleinformation-supervisor-cycle` vérifie la confirmation Supervisor
d'un add-on arrêté sans IA, la stabilité sur observations répétées et après
reprise SQLite, l'invalidation lors d'un changement de seuil et la résolution
sur retour de trames fraîches. Observations et Supervisor restent simulés.

La recette distante contrôle la version, le service, le port d'administration,
la file de jobs et les erreurs récentes du journal Agent. L'option
`--exercise-logs` va plus loin : elle exige un worker Katsuyu `AVAILABLE`
compatible, demande un `logs.health_check` via l'API Agent et vérifie son état
`SUCCEEDED`, son traitement (`completion_processed=1`) et l'absence de contrôle
`logs.health_check` encore actif. Le délai de suivi est de 180 secondes par
défaut, configurable avec `--exercise-timeout`.

**Avec `--exercise-logs`, le parcours n'est plus en lecture seule : il déclenche
un travail réel et peut alimenter les incidents et décisions Tsunade.** Son PASS
valide le traitement du contrôle, pas l'absence d'anomalies dans les journaux,
la qualité de chaque diagnostic ni la fin d'éventuels jobs complémentaires.
Cette capacité complète les scénarios locaux sans remplacer les pannes
contrôlées et les autres critères de sortie. Les exécutions observées sont
consignées dans le [bilan de stabilisation](docs/Phase-1-Stabilisation-Tsunade.md).

### Investigations principales

Les quatre nœuds principaux doivent avoir été réellement observés par le moteur :

- [x] INFRA-01 ;
- [x] HA-01 ;
- [x] LINKY-01 ;
- [x] ZWAVE-01.

Une validation complète et exhaustive de tous les protocoles disponibles sur chacun de ces nœuds n’est pas nécessaire pour sortir de Phase 1.

---

### Situations représentatives

- [x] Une situation sans évolution significative peut rester stable ou en surveillance sans déclencher inutilement une expertise IA.
- [x] Une nouvelle observation matériellement différente peut provoquer une nouvelle analyse.
- [x] Le même dossier ou les mêmes preuves ne provoquent pas une nouvelle expertise IA automatique.
- [x] Une conclusion produite par l’IA reste explicitement identifiable comme une hypothèse.
- [x] Au moins un incident représentatif est diagnostiqué suffisamment loin par Tsunade sans expertise IA Katsuyu (Sandbox `probe-confirmed-failure` : observation DNS, deux contrôles déterministes, panne confirmée par `dns.query`, réseau sain, décision `action_required`, aucune IA, puis résolution sur observation saine).
- [ ] Au moins un incident réellement ambigu démontre une valeur ajoutée identifiable de l’expertise IA Katsuyu. **Le scénario `ambiguous-katsuyu-cycle` valide l'escalade automatique, le niveau `PROBABLE`, le `confirmation_gap`, l'absence d'`action_required` et l'absence de boucle sur preuve identique. Le full-stack du 22 septembre reproduit ensuite ce cycle avec le vrai worker Katsuyu, llama.cpp et Ministral : Agent sollicite automatiquement l'IA, le modèle produit une hypothèse exploitable et Tsunade propose une vérification concrète en lecture seule. Il reste à reproduire ce comportement sur un incident ambigu réellement observé dans Konoha.**
- [x] Une indisponibilité de Katsuyu démontre que Tsunade et Shikamaru continuent leurs fonctions essentielles. **Validé réellement sur Konoha le 21 septembre : Katsuyu maintenu `UNAVAILABLE`, investigations locales Tsunade opérationnelles, cycle Shikamaru Téléinformation poursuivi et aucune reconnexion du worker pendant le test.**
- [x] Au moins un incident atteint correctement un état terminal ou de surveillance sans rester silencieusement bloqué (contrôle du 21 septembre à 09:11 : quatre décisions `watch`, job traité, aucun job restant).

---

## Scénarios de panne contrôlée

Avant la sortie de phase, exercer **au moins trois scénarios représentatifs appartenant à au moins deux familles différentes**.

Famille réseau :

- DNS indisponible ;
- problème réseau d’un équipement ;
- échec TCP.

Famille service :

- Mosquitto indisponible ;
- `teleinfo2mqtt` indisponible ;
- Z-Wave JS indisponible ;
- Home Assistant indisponible ;
- Ohana-Vision indisponible.

Famille système / Ohana :

- surcharge INFRA-01 ;
- anomalie Ohana-Agent ;
- indisponibilité Katsuyu ;
- interruption d’un traitement.

Critère :

- [ ] Trois scénarios représentatifs appartenant à plusieurs familles ont été exercés avec retour à l’état initial vérifié.

Pour chaque scénario retenu :

1. observation Shikamaru ;
2. incident ;
3. preuves collectées ;
4. investigation Tsunade ;
5. Katsuyu éventuel ;
6. justification de cette sollicitation ;
7. résultat ;
8. état final ;
9. absence de boucle ;
10. retour sain lorsqu’il est applicable.

---

## Niveaux de diagnostic

Les niveaux restent :

- **CONFIRMED** ;
- **PROBABLE** ;
- **INSUFFICIENT\_CONTEXT**.

Critères :

- [x] Les trois niveaux sont utilisés de manière cohérente sur des incidents représentatifs (Sandbox `diagnostic-levels`).
- [x] `CONFIRMED` peut être relié à ses preuves déterministes : une sonde exécutée avec succès et mesurant réellement le défaut produit `confirmed_by_probe`, sans `confirmation_gap`.
- [x] `PROBABLE` indique ce qui empêche sa confirmation : l'hypothèse reste explicitement non autoritative, la décision reste `investigate` et `confirmation_gap` expose les preuves encore nécessaires.
- [x] `INSUFFICIENT_CONTEXT` peut mettre fin proprement à une investigation : décision `watch`, preuves manquantes explicites et aucune panne artificiellement confirmée.

---

## Frontière Tsunade ↔ Katsuyu

- [x] Tsunade constitue un dossier suffisamment structuré pour permettre à Katsuyu de comprendre la cible, les preuves et la question posée. **Validé par le full-stack du 21 septembre : le dossier est transmis au worker HTTPS réel, une inférence Ministral est exécutée, le résultat est accepté par Tsunade puis exploité dans Vision.**
- [x] Katsuyu retourne un résultat structuré exploitable par Tsunade.
- [x] Une contribution IA reste identifiable comme telle.
- [x] Un traitement déterministe lourd peut être distingué d’une expertise IA (contrôle du 21 septembre : `logs.health_check` Katsuyu réussi, décisions Tsunade déterministes, aucun `ai.inference`).
- [x] Tsunade décide de la suite après réception du résultat (Sandbox `diagnostic-levels` : un résultat Katsuyu `KO` reste une hypothèse, devient `PROBABLE` avec décision `investigate` et ne produit jamais `action_required`).
- [x] L’absence de Katsuyu n’empêche pas Tsunade de poursuivre les investigations réalisables localement. **Validé réellement sur Konoha le 21 septembre : avec Katsuyu `UNAVAILABLE`, `cpu.status`, `memory.status`, `disk.usage`, `service.status`, `dns.query`, `mqtt.status` et `network.ping` restent opérationnels, tandis que Shikamaru poursuit ses observations planifiées.**

---

## Classification des anomalies

### Bloquant Phase 1

Un défaut est bloquant s’il peut :

- provoquer une décision incorrecte ;
- présenter une hypothèse comme un fait ;
- perdre une preuve nécessaire ;
- provoquer une boucle ;
- relancer Katsuyu indéfiniment ;
- exposer un secret connu ;
- fermer incorrectement un incident ;
- laisser un incident silencieusement bloqué ;
- rendre une fonction essentielle dépendante de Katsuyu.

### Durcissement

Relèvent notamment du durcissement :

- formats supplémentaires de journaux ;
- nouveaux cas limites HTTP ;
- optimisation des grosses collectes ;
- amélioration du classement ;
- réduction progressive des faux positifs ;
- amélioration de la fraîcheur ;
- performance ;
- ergonomie.

### Évolution future

Relèvent d’une phase ultérieure :

- nouvelles réparations ;
- nouveaux handlers Katsuyu ;
- maintenance préventive avancée ;
- mémoire opérationnelle avancée ;
- raffinements d’interface non essentiels.

---

## Durcissement continu

Restent notamment à suivre :

- messages `s6-rc` sans date exploitable ;
- faux positifs de journaux ;
- codes HTTP supplémentaires ;
- limites lignes/octets/groupes ;
- grosses fenêtres de journaux ;
- comparaison de fenêtres ;
- audit étendu des secrets ;
- sondes MQTT, Supervisor et `teleinfo2mqtt` ;
- scénarios de panne supplémentaires ;
- reprises rares après interruption ;
- raffinements de présentation Vision ;
- nombre de jobs et réveils Katsuyu ;

---

## Critères de sortie de la Phase 1

- [x] **Cycle de vie fiable** — cycle observation → diagnostic déterministe →
  retour sain validé fonctionnellement en Sandbox ; reprise des suivis expirés
  et déjà traités validée par `followup-restart`, sans perte de preuves ni
  relance ; Agent 1.29.15 contrôlé après déploiement sur INFRA-01 avec recette
  complète PASS, `NRestarts=0`, aucun job actif, aucun résultat terminal non
  traité, puis `logs.health_check` réel exécuté par `katsuyu-bubule`,
  `SUCCEEDED` et traité sans job résiduel.
- [x] **Investigations essentielles** — INFRA-01, HA-01, LINKY-01 et ZWAVE-01 ont été réellement exercés sur Konoha. Les investigations bornées Agent, le chemin MQTT vers HA-01, l'accès API Home Assistant et la Téléinformation directe `teleinfo2mqtt → Agent` ont fourni des preuves déterministes exploitables.
- [x] **Absence de boucle sur dossier inchangé** — également couverte par `followup-evidence-cycle` : deux résultats IA simulés et une collecte autorisée, sans nouveau travail après doublons et reprise SQLite.
- [x] **Réévaluation sur information nouvelle**.
- [x] **Hypothèses maîtrisées**.
- [ ] **Valeur de Katsuyu démontrée** — le cas simple restant entièrement chez Tsunade est acquis ; le full-stack valide également une vraie inférence Ministral, son traitement par Tsunade et son rendu Vision. Il reste à démontrer qu'une expertise Katsuyu apporte une information réellement utile sur un incident ambigu effectivement observé dans Konoha.
- [x] **Mode dégradé démontré** — Katsuyu a été rendu réellement indisponible sur Bubule. Pendant cette absence, les investigations déterministes locales de Tsunade sont restées opérationnelles, Shikamaru a poursuivi ses observations planifiées et le worker est resté `UNAVAILABLE` pendant toute la validation.
- [x] **Preuves suffisamment sûres** — sanitation centralisée validée sur les observations, résultats d'investigation, erreurs distribuées utilisées comme preuves, dossiers envoyés à Katsuyu, résultats IA, follow-up, expériences mémorisées et projections relues depuis SQLite. Les données historiques sont également nettoyées à la lecture sans migration destructive. La campagne Agent atteint 1559 tests PASS (1 skipped), les 9 scénarios Sandbox restent PASS et le full-stack avec inférence Ministral réelle et rendu Vision reste PASS.
- [ ] **Valeur de Katsuyu démontrée** — le routage automatique vers Katsuyu est désormais démontré sur un incident ambigu reproductible. Le scénario `ambiguous-katsuyu-cycle` valide qu'Agent crée lui-même un unique `ai.inference`, conserve le résultat comme hypothèse `PROBABLE`, expose les éléments manquants et ne boucle pas sur les mêmes preuves. Le full-stack du 22 septembre reproduit ce cycle avec le vrai worker HTTPS, llama.cpp et Ministral : verdict `KO`, hypothèse structurée, contexte manquant, décision Tsunade `investigate` et proposition de vérification en lecture seule. Il reste uniquement à démontrer cette valeur sur un incident ambigu effectivement observé dans Konoha.
- [ ] **Pannes représentatives exercées** — la panne contrôlée #1 `teleinfo2mqtt` est validée réellement sur Konoha avec Agent 1.29.18 : détection, incident unique, preuve Supervisor `state=error`, diagnostic `CONFIRMED`, aucune IA inutile et résolution automatique au retour des trames. La panne réseau #2 `SHE-04` a validé son cycle de vie mais révélé l'absence de déclenchement Tsunade pour les équipements sans source de journaux. Le correctif est qualifié localement par 1569 tests Agent, Ruff et le scénario `tsunade-observation-wiring`; un rejeu réel après déploiement de la prochaine release reste nécessaire. La panne #3 est préparée par `ambiguous-katsuyu-cycle` et le full-stack avec vrai LLM, mais doit encore être reproduite sur Konoha. Le critère sera acquis lorsque trois scénarios réels appartenant à au moins deux familles auront été validés avec retour à l'état initial.

La Phase 1 n’exige pas l’absence totale de bugs ou de faux positifs.

Elle exige qu’aucun défaut bloquant connu ne remette en cause les invariants fondamentaux de Tsunade.

---

# Phase 2 — Cycle complet incident → réparation supervisée

## Objectif

Faire évoluer Tsunade d’un moteur de diagnostic fiable vers un coordinateur capable de **proposer une réparation déterministe, demander l’autorisation appropriée, exécuter l’action et vérifier son résultat**.

```text
Shikamaru détecte
        │
        ▼
Tsunade diagnostique
        │
        ▼
Réparation connue possible ?
        │
        ├── non ──────► surveillance / décision humaine
        │
        └── oui
              │
              ▼
      Proposition d'action
              │
              ▼
       Autorisation humaine
              │
              ▼
          Exécution
              │
              ▼
      Vérification Shikamaru
          │           │
       succès       échec
```

---

## Portée de la phase

La Phase 2 n’a pas pour objectif de construire immédiatement un catalogue complet de réparations.

Elle doit démontrer que **le mécanisme lui-même est sûr et reproductible**.

Le redémarrage de `dnsmasq.service` reste le modèle de référence.

Une deuxième réparation suffisamment différente doit compléter cette validation.

Candidats :

- Mosquitto ;
- composant Ohana ;
- add-on Home Assistant ;
- service de télémétrie.

---

## Principes

Toute réparation doit définir :

- symptôme ;
- préconditions ;
- action ;
- cible ;
- risques ;
- conséquences possibles ;
- résultat attendu ;
- délai de vérification ;
- vérification Shikamaru ;
- comportement en cas d’échec.

Toute action modifiant Konoha nécessite une autorisation humaine, hors opérations techniques explicitement préautorisées du cycle worker Katsuyu.

Une réparation refusée ou différée ne peut pas être exécutée.

Une réparation ayant échoué ne doit pas être répétée automatiquement sans nouvelle preuve ou nouvelle décision.

---

## Critères de sortie de la Phase 2

- [ ] Une première réparation supervisée de référence fonctionne de bout en bout.
- [ ] Une deuxième réparation suffisamment différente utilise le même mécanisme.
- [ ] Le cycle `diagnostic → proposition → autorisation → exécution → vérification` ne contient aucun état ambigu.
- [ ] Une action non autorisée ne peut pas être exécutée.
- [ ] Une action refusée ou différée reste explicitement dans cet état.
- [ ] Shikamaru vérifie le résultat réel de la réparation.
- [ ] Un échec laisse l’incident dans un état explicite et exploitable.
- [ ] Une réparation échouée n’est pas répétée automatiquement sans nouvelle décision.
- [ ] Vision et/ou Shizune permettent de comprendre l’action proposée et son résultat.
- [ ] Tsunade reste propriétaire de la décision finale.

---

## Durcissement continu

- enrichissement du catalogue de réparations ;
- rollback lorsque nécessaire ;
- meilleure présentation des risques ;
- politiques spécifiques par type d’action ;
- délais adaptatifs de vérification ;
- réparations Home Assistant supplémentaires ;
- gestion de réparations plus complexes.

---

# Phase 3 — Mémoire opérationnelle de Tsunade

## Objectif

Permettre à Tsunade de **réutiliser une expérience déjà validée**, sans apprentissage autonome et sans transformer une corrélation en causalité.

La mémoire opérationnelle conserve les réparations connues et leurs résultats.

---

## Cas minimal A — réparation connue

Une réparation validée possède :

- symptômes associés ;
- preuves nécessaires ;
- procédure ;
- nombre de tentatives ;
- nombre de réussites ;
- nombre d’échecs ;
- dernière réussite.

Tsunade peut la proposer lorsqu’un nouveau cas suffisamment comparable apparaît.

La politique d’autorisation de Phase 2 reste applicable.

---

## Cas minimal B — résolution manuelle

```text
Incident
   │
   ▼
Action manuelle utilisateur
   │
   ▼
Shikamaru observe un retour sain
   │
   ▼
Tsunade propose :
« Cette action semble avoir participé à la résolution.
Souhaitez-vous la conserver comme piste de réparation connue ? »
```

La proximité temporelle ne constitue pas à elle seule une preuve de causalité.

Aucune commande libre saisie par l’utilisateur ne devient automatiquement une action exécutable.

---

## Critères de sortie de la Phase 3

- [ ] Au moins une réparation connue peut être retrouvée à partir de symptômes et preuves explicites.
- [ ] Tentatives, réussites, échecs et dernière réussite sont historisés.
- [ ] Tsunade peut proposer une réparation connue sans l’exécuter automatiquement.
- [ ] Une résolution manuelle peut être déclarée par l’utilisateur.
- [ ] Shikamaru peut confirmer le retour à l’état sain après cette action.
- [ ] Tsunade demande une confirmation avant de capitaliser cette expérience.
- [ ] La proximité temporelle n’est jamais présentée comme preuve suffisante de causalité.
- [ ] Une commande libre ne devient jamais automatiquement exécutable.
- [ ] Une réparation connue peut être désactivée ou rendue obsolète.
- [ ] La mémoire opérationnelle respecte toujours les autorisations de Phase 2.

---

## Durcissement continu

- statistiques supplémentaires ;
- taux de réussite détaillés ;
- classement des réparations ;
- obsolescence automatique assistée ;
- comparaison plus fine entre incidents ;
- historique avancé dans Vision.

---

# Phase 4 — Maintenance préventive

## Objectif

Permettre à Tsunade de signaler **quelques dérives réellement utiles avant qu’elles ne deviennent des incidents**, sans chercher artificiellement des problèmes.

Shikamaru continue de produire les observations.

Tsunade applique des règles simples et explicables.

Katsuyu n’est utilisé que lorsqu’un traitement historique ou volumineux justifie réellement le déport.

---

## Périmètre initial

Valider seulement quelques familles de tendance.

Exemples retenus :

- croissance anormale du disque INFRA-01 ;
- redémarrages répétés ;
- interruptions réseau répétitives.

D’autres tendances pourront être ajoutées ensuite :

- mémoire ;
- erreurs croissantes ;
- temps de réponse ;
- anomalies récurrentes de journaux.

---

## Synthèse

Exemple :

```text
Konoha est stable.

À surveiller :
- INFRA-01 : espace disque en hausse depuis plusieurs jours.
- ZWAVE-01 : plusieurs interruptions courtes cette semaine.

Aucune intervention nécessaire.
```

Vision fournit le détail.

Shizune fournit l’essentiel.

---

## Critères de sortie de la Phase 4

- [ ] Au moins trois tendances simples peuvent être détectées de manière reproductible.
- [ ] Une évolution normale n’est pas systématiquement transformée en anomalie.
- [ ] Les règles ou seuils utilisés restent explicables.
- [ ] Les données déjà disponibles sont privilégiées.
- [ ] Un traitement historique lourd peut être déporté vers Katsuyu lorsqu’il le justifie.
- [ ] L’indisponibilité de Katsuyu n’empêche pas les contrôles préventifs simples.
- [ ] Une synthèse courte est disponible dans Shizune.
- [ ] Le détail correspondant est disponible dans Vision.
- [ ] Une situation stable peut produire explicitement « aucune intervention nécessaire ».
- [ ] Aucune réparation n’est déclenchée automatiquement par la seule maintenance préventive.

---

## Durcissement continu

- nouvelles tendances ;
- fenêtres adaptatives ;
- détection saisonnière ;
- analyse de journaux longue durée ;
- tendances Home Assistant ;
- corrélations plus complexes ;
- réduction des alertes inutiles.

---

# Phase 5 — Ohana supervise Ohana

## Objectif

Faire des composants Ohana eux-mêmes des éléments observables de Konoha, **sans construire immédiatement une introspection complète de chaque processus interne**.

Le minimum attendu est de savoir :

- si le composant est vivant ;
- s’il répond ;
- s’il travaille encore ;
- quand il a fonctionné pour la dernière fois ;
- et si sa défaillance empêche ou non l’observation des autres.

---

## Agent

Déjà disponible :

- [x] état systemd ;
- [x] uptime ;
- [x] CPU ;
- [x] mémoire ;
- [x] disque ;
- [x] température ;
- [x] erreurs systemd.

Minimum restant :

- [ ] dernière activité utile ;
- [ ] état synthétique des composants internes critiques.

---

## Vision

Déjà disponible :

- [x] supervision du service ;
- [x] base SQLite sauvegardée.

Minimum restant :

- [ ] disponibilité HTTP ;
- [ ] dernière ingestion ou activité utile.

---

## Katsuyu

Déjà disponible :

- [x] présence du worker ;
- [x] dernière connexion ;
- [x] capacités annoncées ;
- [x] Wake-on-LAN ;
- [x] état des jobs.

Minimum restant :

- [ ] dernier job réussi ;
- [ ] disponibilité synthétique du runtime nécessaire au job demandé.

---

## Shizune

Minimum attendu :

- [ ] passerelle disponible ;
- [ ] dernière synchronisation connue.

---

## Critères de sortie de la Phase 5

- [ ] Agent expose un état vital exploitable.
- [ ] Vision expose un état vital exploitable.
- [ ] Katsuyu expose un état vital exploitable.
- [ ] Shizune expose un état vital exploitable.
- [ ] La dernière activité significative d’un composant permet de repérer un composant silencieusement figé.
- [ ] Une défaillance Ohana peut elle-même produire une observation exploitable.
- [ ] L’indisponibilité d’un composant n’empêche pas d’observer les autres composants accessibles.
- [ ] La supervision d’Ohana ne crée pas de dépendance circulaire critique.
- [ ] La charge de cette auto-supervision reste compatible avec INFRA-01.

---

## Durcissement continu

- scheduler ;
- longueurs de files ;
- état du stockage Tsunade ;
- WebSocket Vision ;
- retard d’ingestion ;
- croissance SQLite ;
- rétention ;
- workspace Katsuyu ;
- diagnostic détaillé du runtime IA ;
- version disponible ;
- association Shizune.

---

# Phase 6 — Katsuyu

## Objectif

Conserver Bubule comme **capacité de calcul optionnelle, robuste et non critique**.

Une extinction de Bubule ne doit jamais empêcher les fonctions essentielles de Konoha.

Une indisponibilité du LLM ne doit pas empêcher les traitements déterministes compatibles.

---

## Cycle worker déjà présent

- [x] appairage sécurisé ;
- [x] worker Windows ;
- [x] installation autonome ;
- [x] jobs déterministes ;
- [x] Wake-on-LAN ;
- [x] regroupement des jobs ;
- [x] arrêt après traitement ;
- [x] reprise après interruption ;
- [x] IA locale ;
- [x] vérification du modèle ;
- [x] mise à jour manuelle assistée.

---

## Critères de sortie de la Phase 6

- [ ] Bubule reste optionnel pour les fonctions essentielles de Konoha.
- [ ] Wake-on-LAN fonctionne de manière suffisamment fiable lorsque Katsuyu est réellement nécessaire.
- [ ] Un worker déjà disponible est réutilisé sans réveil inutile.
- [ ] Plusieurs jobs compatibles peuvent partager un même cycle.
- [ ] L’arrêt après traitement respecte les conditions prévues.
- [ ] Bubule n’est pas arrêté lorsqu’un usage utilisateur ou un état bloquant est détecté.
- [ ] Un job interrompu peut être repris ou explicitement échouer.
- [ ] Les traitements déterministes lourds peuvent fonctionner sans runtime IA lorsqu’ils n’en ont pas besoin.
- [ ] Une expertise IA impossible ne produit pas de conclusion artificielle.
- [ ] Vision permet de comprendre au minimum pourquoi Katsuyu a été réveillé et ce qu’il a exécuté.

---

## Durcissement continu

- métriques détaillées de durée et ressources ;
- estimation du gain par rapport à INFRA-01 ;
- intégrité périodique du workspace ;
- diagnostic approfondi du runtime IA ;
- optimisation énergétique ;
- nouveaux handlers uniquement lorsqu’un besoin réel apparaît.

---

# Phase 7 — Shizune

## Objectif

Conserver Shizune comme **interface personnelle simple entre Tsunade et l’utilisateur**.

Shizune ne doit pas devenir un second Vision.

---

## Fonctionnalités déjà présentes

- [x] PWA installable sur iPhone ;
- [x] état général de Konoha ;
- [x] incidents prioritaires ;
- [x] activité récente ;
- [x] décisions Tsunade ;
- [x] association contrôlée ;
- [x] autoriser / refuser / plus tard ;
- [x] demandes de diagnostic ;
- [x] suivi des investigations complémentaires.

---

## Critères de sortie de la Phase 7

- [ ] Shizune reste utilisable comme PWA sans application native obligatoire.
- [ ] L’état général de Konoha est compréhensible sans détails techniques excessifs.
- [ ] Les incidents importants sont clairement identifiés.
- [ ] Une demande de décision Tsunade est compréhensible.
- [ ] L’utilisateur peut autoriser, refuser ou reporter sans ambiguïté.
- [ ] Le résultat de la décision peut être suivi.
- [ ] Les informations viennent des contrats Agent et ne recréent pas une logique métier parallèle.
- [ ] Une perte de synchronisation est explicitement visible.
- [ ] Shizune n’introduit pas d’administration technique directe.
- [ ] Toute nouvelle fonctionnalité répond à un besoin réellement observé dans l’usage quotidien.

---

## Durcissement continu

- ergonomie ;
- informations manquantes constatées à l’usage ;
- meilleure synthèse ;
- notifications uniquement si l’usage le justifie ;
- fonctionnement hors ligne partiel si un besoin concret apparaît.

---

# Phase 8 — Vision

## Objectif

Faire de Vision le cockpit permettant de **comprendre ce qu’Ohana a observé, décidé et exécuté sans ouvrir SQLite ni se connecter en SSH**.

La perfection visuelle ou l’exposition de toutes les données internes ne constitue pas l’objectif de la phase.

---

## Chaîne minimale à rendre lisible

Pour un incident représentatif :

```text
Observation
    ↓
Incident
    ↓
Investigation
    ↓
Preuves
    ↓
Diagnostic
    ↓
Katsuyu éventuel
    ↓
Décision
    ↓
Action éventuelle
    ↓
Vérification
```

Vision doit distinguer clairement :

- faits ;
- preuves ;
- diagnostic ;
- hypothèses ;
- contribution Katsuyu ;
- limites ;
- décision ;
- résultat.

---

## Critères de sortie de la Phase 8

- [ ] L’état actuel d’un incident est compréhensible rapidement.
- [ ] Observation, investigation, diagnostic, décision et résultat sont distincts.
- [ ] Les principales preuves sont accessibles sans consulter directement les bases Agent.
- [ ] Les hypothèses sont visuellement distinguées des faits.
- [ ] Une contribution Katsuyu indique clairement sa nature.
- [ ] Les limites principales d’une analyse sont visibles.
- [ ] Une réparation affiche décision, autorisation, exécution et vérification lorsqu’elles existent.
- [ ] Vision représente les états fournis par Agent au lieu de reconstruire sa propre logique.
- [ ] Les performances restent suffisantes pour l’usage réel.
- [ ] Un incident représentatif peut être compris intégralement depuis Vision.

---

## Durcissement continu

- ergonomie ;
- historique plus riche ;
- filtrage ;
- performances avec très grandes bases ;
- affichage avancé des preuves ;
- comparaisons temporelles ;
- optimisation mobile éventuelle.

---

# Phase 9 — Shikamaru

## Objectif

Continuer à renforcer la **qualité des observations** plutôt que multiplier les capacités.

Shikamaru observe.

Il ne remplace pas Tsunade dans le diagnostic.

---

## Capacités existantes

- [x] DNS ;
- [x] DHCP ;
- [x] NTP ;
- [x] MQTT ;
- [x] présence réseau ;
- [x] Z-Wave ;
- [x] WireGuard ;
- [x] télémétrie Home Assistant ;
- [x] Téléinformation ;
- [x] santé INFRA-01 ;
- [x] surveillance systemd.

---

## Critères de sortie de la Phase 9

- [ ] Les capacités essentielles produisent des observations suffisamment stables pour être exploitées.
- [ ] Les principaux faux positifs connus sont réduits ou documentés.
- [ ] Les états transitoires sont distingués des pannes réelles lorsqu’une règle raisonnable le permet.
- [ ] L’âge d’une observation permet de savoir si elle est encore exploitable.
- [ ] Une panne du collecteur est distinguée autant que possible de la panne de ce qu’il observe.
- [ ] Les dépendances objectives peuvent être représentées sans inventer de causalité.
- [ ] Les changements d’état sont historisés.
- [ ] La charge globale reste adaptée à INFRA-01.
- [ ] Une nouvelle capacité n’est ajoutée que lorsqu’elle garantit une fonction réellement utile de Konoha.

---

## Durcissement continu

- faux positifs résiduels ;
- contexte inter-capacités ;
- groupes de disponibilité ;
- meilleure gestion des états transitoires ;
- enrichissement des métriques existantes.

---

# Phase 10 — Sauvegarde et restauration

## Objectif

Considérer une sauvegarde comme fiable uniquement lorsqu’elle peut **réellement être restaurée**.

L’existence du fichier de sauvegarde n’est pas une validation suffisante.

---

## Déjà livré

- [x] sauvegarde HAOS ;
- [x] sauvegarde INFRA-01 ;
- [x] chiffrement `age` ;
- [x] iCloud ;
- [x] streaming sans stockage permanent sur microSD ;
- [x] traitement lourd déporté vers Katsuyu ;
- [x] restauration INFRA-01 ;
- [x] inventaire des versions.

---

## Critères de sortie de la Phase 10

- [ ] Une sauvegarde HAOS peut être restaurée selon une procédure documentée et réellement vérifiée.
- [ ] Une sauvegarde INFRA-01 peut être restaurée selon une procédure documentée et réellement vérifiée.
- [ ] La date du dernier test de restauration est conservée.
- [ ] L’intégrité d’une archive peut être vérifiée indépendamment de sa création.
- [ ] Une sauvegarde jamais testée est explicitement identifiable.
- [ ] Les versions nécessaires à la restauration sont disponibles.
- [ ] Une restauration échouée ou incomplète produit un état explicite.
- [ ] Le chiffrement reste vérifiable sans exposer les secrets.
- [ ] Une sauvegarde distante n’est déclarée réussie que lorsque l’archive attendue est réellement disponible.
- [ ] L’état sauvegarde/restauration peut être exploité par Tsunade.

---

## Durcissement continu

- validation périodique automatique ;
- contrôle d’anciennes archives ;
- politiques d’ancienneté ;
- alertes sur dernier test trop ancien ;
- simulations régulières ;
- tests plus complets de restauration HAOS ;
- intégration à la maintenance préventive.

---

# Chantiers transverses

Les chantiers suivants ne sont plus considérés comme des phases séquentielles.

Ils évoluent pendant toute la roadmap.

Ils peuvent produire ponctuellement un blocage de release ou de phase lorsqu’une incohérence majeure est découverte, mais ils n’ont pas de date de « fin » propre.

---

# Chantier transverse A — Documentation et cohérence de l’écosystème

## Objectif

Faire correspondre la documentation, les contrats et les compositions de releases avec le logiciel réellement livré.

La documentation doit être une conséquence du comportement réel d’Ohana, et non une architecture théorique parallèle.

---

## Documentation fonctionnelle essentielle

Maintenir à jour :

- `ROADMAP.md` ;
- architecture globale ;
- responsabilités Shikamaru / Tsunade / Katsuyu / Vision / Shizune ;
- frontière Tsunade ↔ Katsuyu ;
- cycle de vie des incidents ;
- politique d’autorisation ;
- comportements essentiels en mode dégradé.

---

## Investigations

Documenter progressivement les investigations réellement utilisées :

- INFRA-01 ;
- HA-01 ;
- LINKY-01 ;
- ZWAVE-01 ;
- DNS ;
- TCP ;
- HTTP ;
- MQTT ;
- `teleinfo2mqtt` ;
- Supervisor ;
- métriques système.

La documentation d’une investigation doit préciser au minimum :

- déclencheur ;
- cible ;
- contrôles exécutés ;
- preuves obtenues ;
- conclusions possibles ;
- principales limites.

Il n’est pas nécessaire de documenter exhaustivement une capacité qui n’est pas encore utilisée.

---

## Réparations supervisées

Toute réparation réellement disponible doit avoir une procédure correspondante précisant :

- symptôme ;
- préconditions ;
- action ;
- autorisation ;
- résultat attendu ;
- vérification ;
- comportement en cas d’échec.

Aucune action modifiant Konoha ne doit exister uniquement dans le code sans documentation minimale correspondante.

---

## Contrat Tsunade ↔ Katsuyu

Le contrat constitue une interface majeure.

Il doit distinguer au minimum :

```text
DETERMINISTIC_HEAVY
AI_EXPERTISE
```

Le dossier Tsunade → Katsuyu doit permettre de transmettre :

- incident ;
- cible ;
- type de traitement ;
- contexte ;
- faits ;
- preuves ;
- provenance ;
- temporalité ;
- éléments manquants ;
- question ou traitement demandé.

Le résultat doit permettre de distinguer :

- statut ;
- type de traitement réalisé ;
- résultats déterministes ;
- hypothèses ;
- limites ;
- erreurs ;
- informations manquantes.

Katsuyu ne modifie pas directement l’état final d’un incident.

---

## Versionnement des contrats

Les contrats partagés critiques doivent progressivement posséder une version identifiable.

Sont notamment concernés :

- observations ;
- incidents ;
- preuves ;
- demandes Katsuyu ;
- résultats Katsuyu ;
- décisions ;
- autorisations ;
- réparations ;
- données Vision ;
- données Shizune.

Une rupture incompatible ne doit pas être introduite silencieusement.

---

## Troubleshooting

Maintenir un guide minimal et réellement testable couvrant :

- Agent ;
- Vision ;
- Katsuyu ;
- Shizune ;
- files et jobs ;
- communications principales ;
- Wake-on-LAN ;
- MQTT ;
- Home Assistant ;
- Téléinformation ;
- incidents Tsunade ;
- versions installées ;
- récupération après mise à jour défaillante.

Les procédures courtes et reproductibles sont préférées aux descriptions historiques.

---

## Cohérence inter-dépôts

Lors d’une évolution importante, vérifier si elle impacte :

- Ohana-Agent ;
- Ohana-Vision ;
- Ohana-Katsuyu ;
- Ohana-Shizune ;
- Ohana-Installer ;
- Ohana-Platform ;
- Ohana-House.

---

## Minimum obligatoire avant release importante

Une release fonctionnelle importante doit vérifier :

- [ ] versions cohérentes ;
- [ ] contrats modifiés identifiés ;
- [ ] migrations nécessaires disponibles ;
- [ ] principaux tests inter-dépôts concernés réussis ;
- [ ] documentation correspondant au comportement livré ;
- [ ] aucun secret ajouté dans la documentation ;
- [ ] composition Platform cohérente.

Le reste du chantier documentaire évolue continuellement et n’empêche pas de poursuivre la roadmap lorsqu’il ne compromet ni sécurité ni compréhension opérationnelle.

---

# Chantier transverse B — Konoha de référence

## Objectif

Faire d’Ohana-House une **photographie fidèle, lisible et maintenable de l’infrastructure réellement déployée**, sans en faire une seconde source de configuration.

Une personne extérieure au développement doit pouvoir comprendre les grandes lignes de Konoha à partir de ce dépôt.

---

## Contenu minimal

Ohana-House doit maintenir :

- les machines principales ;
- leur rôle ;
- les services essentiels ;
- les grandes liaisons réseau ;
- les équipements supervisés ;
- les capacités réellement garanties ;
- les dépendances critiques importantes.

---

## Principes

Ohana-House :

- ne contient pas de secrets ;
- ne duplique pas la configuration dynamique d’Agent ;
- distingue clairement état actuel et éléments historiques ;
- utilise le vocabulaire Konoha actuel ;
- est mis à jour lors d’une évolution importante de l’infrastructure.

---

## Critères permanents

- [ ] Inventaire matériel globalement fidèle.
- [ ] Rôles des machines à jour.
- [ ] Principales liaisons réseau compréhensibles.
- [ ] Services importants identifiables.
- [ ] Capacités garanties cohérentes avec la réalité.
- [ ] Dépendances critiques documentées.
- [ ] Aucun secret inutile.
- [ ] Pas de duplication de la configuration opérationnelle dynamique.
- [ ] Mise à jour après modification significative de Konoha.
- [ ] Cohérence générale avec la roadmap et l’architecture documentée.

Ce chantier n’a pas vocation à être « terminé ».

Il doit rester suffisamment fidèle pour constituer une référence utile.

---

# Hors priorité actuelle

Les sujets suivants ne doivent pas être développés sans besoin concret :

- Docker Compose ;
- Kubernetes ;
- architecture multi-utilisateur ;
- cloud Ohana ;
- exécution de commandes libres par IA ;
- administration directe depuis Katsuyu ;
- administration directe depuis Shizune ;
- remplacement de Vision par Shizune ;
- système générique de plugins externes ;
- SDK public ;
- renommage des dépôts Agent, Vision, Installer ou Platform.

---

# Ordre fonctionnel de la roadmap

```text
Phase 1
Tsunade sait diagnostiquer de manière fiable
        │
        ▼
Phase 2
Tsunade sait coordonner une réparation supervisée
        │
        ▼
Phase 3
Tsunade sait réutiliser une expérience validée
        │
        ▼
Phase 4
Tsunade sait détecter quelques dérives utiles
        │
        ▼
Phase 5
Ohana sait observer ses propres composants
        │
        ▼
Phase 6
Katsuyu est un worker robuste et optionnel
        │
        ▼
Phase 7
Shizune rend Ohana utilisable simplement au quotidien
        │
        ▼
Phase 8
Vision rend Ohana compréhensible techniquement
        │
        ▼
Phase 9
Shikamaru fournit des observations suffisamment fiables
        │
        ▼
Phase 10
Konoha est réellement sauvegardable et restaurable
```

En parallèle :

```text
Toutes les phases
        │
        ├── Documentation / contrats / cohérence
        │
        └── Konoha de référence
```

---

# Priorité immédiate

La priorité actuelle reste :

```text
1. Exercer suffisamment INFRA-01, HA-01 et LINKY-01
             │
             ▼
2. Exercer trois pannes contrôlées dans plusieurs familles
             │
             ▼
3. Vérifier en réel le mode dégradé sans Katsuyu
             │
             ▼
4. Démontrer la valeur de l'IA sur un incident Konoha réellement ambigu
             │
             ▼
5. Terminer l'audit de sûreté des preuves nécessaire à la sortie de phase
             │
             ▼
6. Passer à la première réparation supervisée
```
La frontière Tsunade/Katsuyu et le rendu Vision sont désormais validés dans le
laboratoire full-stack local. Ils restent à observer et à durcir dans l'usage
réel, mais ne constituent plus à eux seuls les principaux inconnus techniques de
la Phase 1.

La prochaine étape d’Ohana n’est pas d’ajouter un nouveau composant ni d’atteindre une couverture parfaite.

Elle consiste à rendre chaque capacité **suffisamment fiable pour être utilisée**, puis à la durcir progressivement à partir des problèmes réellement rencontrés dans Konoha.
