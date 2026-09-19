# Roadmap Ohana

## État de référence

Cette roadmap prend **Ohana-Platform 1.0.100** comme nouveau point de départ.

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
                ┌────────────┴────────────┐
                │                         │
             INFRA-01                   BUBULE
                │                         │
       ┌────────┴────────┐              KATSUYU
       │                 │
   SHIKAMARU          TSUNADE
       │                 │
       │          ┌──────┴──────┐
       │          │             │
       │        VISION        SHIZUNE
       │
   Capacités
   observées
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
- **Tsunade** : incidents, expertise, coordination, décisions et réparations ;
- **Katsuyu** : exécution lourde et IA locale sur Bubule ;
- **Shizune** : interaction personnelle et décisions utilisateur.

---

# Phase 1 — Stabilisation de Tsunade

Suivi : [campagne de validation et premiers constats](docs/Phase-1-Stabilisation-Tsunade.md).
Phase démarrée le 15 septembre 2026 ; validation en production encore partielle.

Checklist rapprochée du rapport le 19 septembre 2026. Les cases cochées
correspondent aux validations ci-dessous dans leur périmètre indiqué ; elles
ne valent pas validation des scénarios de panne ni de toute la chaîne en production.

## Objectif

Valider le comportement de Tsunade sur des incidents réels avant d’étendre ses capacités.

Tsunade doit produire un diagnostic utile, compréhensible et reproductible sans multiplier les analyses IA inutiles.

### Validation des investigations

- [ ] Valider les investigations automatiques en lecture seule sur INFRA-01.
- [ ] Valider les investigations automatiques sur HA-01.
- [ ] Valider les investigations automatiques sur LINKY-01.
- [ ] Valider les investigations automatiques sur ZWAVE-01.
- [ ] Vérifier les diagnostics MQTT de Mosquitto.
- [ ] Vérifier les diagnostics `teleinfo2mqtt`.
- [ ] Vérifier les contrôles Supervisor Home Assistant.
- [ ] Vérifier les investigations DNS, TCP et HTTP.
- [x] Vérifier les métriques système collectées sur INFRA-01 (snapshot CPU, mémoire, disque et unités du 15 septembre ; scénario de surcharge restant).
- [ ] Vérifier que les secrets restent exclus des preuves.

### Qualité des diagnostics

- [ ] Vérifier que Tsunade distingue clairement faits, hypothèses et éléments manquants.
- [ ] Vérifier que les anomalies déjà connues ne déclenchent pas inutilement un nouveau cycle IA (cycles stables et rejeu des corrélations validés ; perte de référence après contrôle partiel constatée le 19 septembre, correction locale à déployer puis vérifier).
- [x] Vérifier que l’arrivée de nouvelles observations peut rouvrir correctement une analyse (nouvelles corrélations du 16 septembre, contrôle 09:01–09:03).
- [x] Vérifier que les diagnostics terminés ne sont pas relancés sans nouvelle information (tests de cycle et rejeu avec réouverture de base ; reprise en production restant à observer).
- [ ] Vérifier que les faux positifs MQTT, série et télémétrie restent maîtrisés.
- [ ] Vérifier que `INSUFFICIENT_CONTEXT` conduit à une investigation utile plutôt qu’à une conclusion artificielle.

### Tests en production

Créer progressivement des scénarios réels ou contrôlés :

- [ ] indisponibilité DNS ;
- [ ] Mosquitto indisponible ;
- [ ] perte de `teleinfo2mqtt` ;
- [ ] problème de communication LINKY-01 ;
- [ ] Z-Wave JS indisponible ;
- [ ] Home Assistant indisponible ;
- [ ] problème réseau d’un équipement ;
- [ ] surcharge ou anomalie d’INFRA-01 ;
- [ ] incident Ohana-Agent ;
- [ ] incident Ohana-Vision.

---

# Phase 2 — Cycle complet incident → réparation

## Objectif

Faire de Tsunade non seulement un moteur de diagnostic, mais aussi un coordinateur capable de proposer une réparation sûre puis de vérifier son résultat.

Le cycle cible est :

```text
Shikamaru détecte
        │
        ▼
Tsunade ouvre l'incident
        │
        ▼
Investigation déterministe
        │
        ├── preuve suffisante
        │
        └── preuve insuffisante
                    │
                    ▼
                 Katsuyu
                    │
                    ▼
            Analyse complémentaire
                    │
                    ▼
              Décision Tsunade
                    │
          ┌─────────┴─────────┐
          │                   │
       Surveiller          Réparer
                              │
                              ▼
                     Autorisation requise
                              │
                              ▼
                         Exécution
                              │
                              ▼
                   Vérification Shikamaru
                              │
                     ┌────────┴────────┐
                     │                 │
                   Succès            Échec
```

### Réparations supervisées

Le redémarrage de `dnsmasq.service` constitue le premier modèle.

Étendre progressivement ce mécanisme à des actions simples, déterministes et réversibles.

Candidats :

- [ ] redémarrage supervisé de Mosquitto ;
- [ ] redémarrage supervisé d’un composant Ohana ;
- [ ] redémarrage supervisé d’un add-on Home Assistant lorsque l’API le permet ;
- [ ] reprise contrôlée d’un service de télémétrie ;
- [ ] renouvellement ou correction d’une configuration réseau connue ;
- [ ] autres réparations identifiées à partir d’incidents réellement rencontrés.

Chaque réparation doit définir :

- le symptôme associé ;
- les préconditions ;
- l’action autorisée ;
- les risques ;
- les conséquences possibles ;
- le mécanisme de retour arrière lorsque nécessaire ;
- la vérification Shikamaru ;
- le délai avant vérification ;
- le résultat attendu.

### Politique d’autorisation

- [ ] Conserver une autorisation humaine pour toute action modifiant l’infrastructure.
- [ ] Autoriser automatiquement uniquement les investigations strictement en lecture seule.
- [ ] Afficher clairement dans Shizune la conséquence d’une action avant validation.
- [ ] Conserver la provenance Vision ou Shizune de chaque autorisation.
- [ ] Conserver l’historique de l’action et de son résultat.

---

# Phase 3 — Mémoire opérationnelle de Tsunade

## Objectif

Permettre à Tsunade de réutiliser ce qui a déjà fonctionné sans transformer l’IA en moteur de décision autonome.

### Réparations connues

- [ ] Consolider les réparations déjà validées.
- [ ] Associer une réparation connue aux symptômes et preuves qui l’ont justifiée.
- [ ] Conserver le nombre de tentatives.
- [ ] Conserver le nombre de réussites.
- [ ] Conserver les échecs.
- [ ] Conserver la date de dernière réussite.
- [ ] Présenter le taux de réussite dans Vision.

### Apprentissage des réparations manuelles

Lorsqu’un incident est résolu manuellement :

```text
Incident
   │
   ▼
Action manuelle utilisateur
   │
   ▼
Shikamaru observe le retour à la normale
   │
   ▼
Tsunade propose :
« Cette action semble avoir résolu l'incident.
Souhaitez-vous l'enregistrer comme réparation connue ? »
```

- [ ] Permettre à l’utilisateur d’indiquer l’action manuelle réalisée.
- [ ] Corréler cette action avec le retour à l’état sain.
- [ ] Demander confirmation avant apprentissage.
- [ ] Ne jamais transformer automatiquement une commande libre en action exécutable.
- [ ] Transformer uniquement les cas retenus en procédures déterministes implémentées explicitement.

---

# Phase 4 — Maintenance préventive

## Objectif

Passer progressivement d’une logique uniquement réactive à une logique de détection précoce.

Tsunade ne doit pas chercher artificiellement des problèmes.

Elle doit exploiter les observations déjà produites par Shikamaru et les contrôles planifiés existants.

### Analyse des tendances

- [ ] Détecter l’évolution inhabituelle de l’utilisation disque.
- [ ] Détecter une croissance anormale de la mémoire.
- [ ] Détecter des redémarrages répétés.
- [ ] Détecter une augmentation progressive des erreurs.
- [ ] Détecter des pertes réseau répétitives.
- [ ] Détecter une dégradation progressive des temps de réponse.
- [ ] Détecter les anomalies récurrentes de journaux.

### Synthèse préventive

Produire une synthèse courte du type :

```text
Konoha est stable.

À surveiller :
- INFRA-01 : espace disque en augmentation depuis 7 jours.
- ZWAVE-01 : 4 interruptions courtes cette semaine.

Aucune intervention nécessaire.
```

Cette synthèse doit être adaptée :

- à Vision pour le détail technique ;
- à Shizune pour l’essentiel.

---

# Phase 5 — Ohana supervise Ohana

## Objectif

Faire des composants Ohana eux-mêmes des capacités supervisées.

### Agent

- [x] état systemd ;
- [x] uptime ;
- [x] CPU ;
- [x] mémoire ;
- [x] disque ;
- [x] température ;
- [x] erreurs systemd ;
- [ ] qualité du scheduler ;
- [ ] longueur des files internes ;
- [ ] âge de la dernière observation ;
- [ ] état du stockage Tsunade ;
- [ ] état de la file Katsuyu.

### Vision

- [x] supervision du service ;
- [x] base SQLite sauvegardée ;
- [ ] temps de réponse HTTP ;
- [ ] état WebSocket ;
- [ ] retard d’ingestion ;
- [ ] taille et croissance de la base ;
- [ ] état de la rétention.

### Katsuyu

- [x] présence du worker ;
- [x] dernière connexion ;
- [x] capacités annoncées ;
- [x] Wake-on-LAN ;
- [x] état des jobs ;
- [ ] santé du runtime IA ;
- [ ] espace disponible du workspace ;
- [ ] dernière exécution réussie ;
- [ ] version disponible.

### Shizune

- [ ] état de la passerelle compagnon ;
- [ ] dernière synchronisation ;
- [ ] version installée ;
- [ ] état de l’association compagnon.

---

# Phase 6 — Katsuyu

## Objectif

Conserver Bubule comme capacité de calcul optionnelle et non critique.

Une panne ou une extinction de Bubule ne doit jamais empêcher les fonctions essentielles de Konoha.

### Cycle worker

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

### Évolutions

- [ ] améliorer les métriques de performance des jobs ;
- [ ] afficher dans Vision la consommation réelle par traitement ;
- [ ] mesurer les gains obtenus en déportant les traitements depuis INFRA-01 ;
- [ ] vérifier régulièrement l’intégrité du workspace ;
- [ ] améliorer le diagnostic du runtime IA ;
- [ ] envisager d’autres handlers uniquement lorsqu’un besoin réel apparaît.

---

# Phase 7 — Shizune

## Objectif

Conserver Shizune comme interface personnelle simple entre Tsunade et l’utilisateur.

Shizune ne doit pas devenir un second Vision.

### Fonctionnalités déjà présentes

- [x] PWA installable sur iPhone ;
- [x] état général de Konoha ;
- [x] incidents prioritaires ;
- [x] activité récente ;
- [x] décisions Tsunade ;
- [x] association contrôlée ;
- [x] autoriser / refuser / plus tard ;
- [x] demandes de diagnostic ;
- [x] suivi des investigations complémentaires.

### Évolutions à décider par l’usage

- [ ] améliorer uniquement les informations qui manquent réellement au quotidien ;
- [ ] conserver une interface très synthétique ;
- [ ] éviter toute topologie détaillée ;
- [ ] éviter les paramètres techniques ;
- [ ] éviter l’administration de l’infrastructure ;
- [ ] étudier les notifications uniquement si l’usage montre qu’elles sont nécessaires.

Les notifications Home Assistant et les notifications push natives restent hors priorité tant que la PWA suffit à l’usage.

---

# Phase 8 — Vision

## Objectif

Conserver Vision comme cockpit technique complet de Konoha.

Vision doit rester l’endroit où l’on comprend précisément :

- ce qui existe ;
- ce qui fonctionne ;
- ce qui ne fonctionne pas ;
- ce que Tsunade a diagnostiqué ;
- ce qui a été exécuté ;
- ce que Shikamaru a vérifié.

### Priorités

- [ ] continuer à améliorer la lisibilité du centre d’incidents ;
- [ ] rendre les investigations Tsunade facilement exploitables ;
- [ ] mieux distinguer constat, diagnostic, décision, intervention et résultat ;
- [ ] afficher clairement les limites d’une analyse ;
- [ ] rendre l’historique des réparations réellement utile ;
- [ ] conserver Vision sans logique métier dupliquée depuis Agent.

---

# Phase 9 — Shikamaru

## Objectif

Continuer à renforcer la qualité des observations plutôt que multiplier les plugins.

Une nouvelle capacité doit correspondre à une fonction réellement importante de Konoha.

### Capacités existantes

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

### Évolutions

- [ ] réduire les faux positifs ;
- [ ] améliorer la détection des états transitoires ;
- [ ] améliorer la corrélation entre capacités ;
- [ ] exploiter les groupes de disponibilité pour les services redondants ;
- [ ] ajouter une capacité uniquement lorsqu’elle garantit une fonction réelle de Konoha.

---

# Phase 10 — Sauvegarde et restauration

## Objectif

Considérer une sauvegarde comme valide uniquement lorsqu’elle peut réellement être restaurée.

### Déjà livré

- [x] sauvegarde HAOS ;
- [x] sauvegarde INFRA-01 ;
- [x] chiffrement `age` ;
- [x] iCloud ;
- [x] streaming sans stockage permanent sur microSD ;
- [x] traitement lourd déporté vers Katsuyu ;
- [x] restauration INFRA-01 ;
- [x] inventaire des versions.

### À renforcer

- [ ] automatiser davantage la validation de restauration ;
- [ ] conserver la date du dernier test de restauration ;
- [ ] signaler une sauvegarde jamais restaurée/testée ;
- [ ] vérifier l’intégrité des archives anciennes ;
- [ ] intégrer l’état des sauvegardes à la maintenance préventive Tsunade.

---

# Phase 11 — Documentation et cohérence de l’écosystème

## Objectif

Faire correspondre la documentation avec le logiciel réellement livré.

### Documentation

- [ ] mettre à jour `ROADMAP.md` à chaque nouvelle phase fonctionnelle importante ;
- [ ] supprimer les éléments historiques devenus faux ou redondants ;
- [ ] documenter clairement les ports et flux réseau ;
- [ ] créer ou finaliser le guide Troubleshooting ;
- [ ] documenter les investigations Tsunade ;
- [ ] documenter les réparations supervisées ;
- [ ] documenter le cycle Wake-on-LAN / Katsuyu / arrêt ;
- [ ] documenter la PWA Shizune ;
- [ ] maintenir le diagramme d’architecture global.

### Cohérence inter-dépôts

Avant toute évolution majeure, vérifier conjointement :

- Ohana-Agent ;
- Ohana-Vision ;
- Ohana-Katsuyu ;
- Ohana-Shizune ;
- Ohana-Installer ;
- Ohana-Platform ;
- Ohana-House.

Les contrats partagés, configurations, manifestes et documentations doivent rester cohérents entre les dépôts.

---

# Phase 12 — Konoha de référence

## Objectif

Faire d’Ohana-House la description fidèle de l’infrastructure Konoha réellement déployée.

- [ ] aligner le vocabulaire Ohana-House avec Konoha ;
- [ ] maintenir l’inventaire matériel ;
- [ ] maintenir les liaisons réseau ;
- [ ] maintenir les équipements supervisés ;
- [ ] maintenir les capacités réellement garanties ;
- [ ] documenter les dépendances entre les services critiques.

Le dépôt reste une description de l’installation de référence et ne doit pas dupliquer la configuration opérationnelle détenue par Agent.

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

# Priorité immédiate

La priorité actuelle est :

```text
1. Stabiliser Agent 1.29 / Katsuyu 0.8.7
             │
             ▼
2. Tester Tsunade sur de vrais incidents
             │
             ▼
3. Identifier les preuves qui lui manquent
             │
             ▼
4. Ajouter des investigations déterministes ciblées
             │
             ▼
5. Étendre progressivement les réparations supervisées
             │
             ▼
6. Vérifier systématiquement le résultat avec Shikamaru
             │
             ▼
7. Construire la mémoire opérationnelle de Tsunade
             │
             ▼
8. Introduire progressivement la maintenance préventive
```

La prochaine étape d’Ohana n’est donc pas d’ajouter un nouveau composant.

Elle consiste à rendre **Tsunade suffisamment fiable pour exploiter Konoha au quotidien**, en utilisant Shikamaru pour observer, Katsuyu pour les traitements lourds, Vision pour le cockpit technique et Shizune pour les interactions personnelles.
