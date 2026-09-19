# Roadmap Ohana

## État de référence

Cette roadmap prend **Ohana-Platform 1.0.100** comme baseline fonctionnelle de départ. Les versions indiquées dans les validations de chaque phase peuvent être ultérieures à cette composition.

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

# Phase 1 — Stabilisation de Tsunade

Suivi : [campagne de validation et premiers constats](docs/Phase-1-Stabilisation-Tsunade.md).  
Phase démarrée le 15 septembre 2026 ; validation en production encore partielle.

Checklist rapprochée du rapport le 19 septembre 2026. Les cases cochées correspondent aux validations ci-dessous dans leur périmètre indiqué ; elles ne valent pas validation des scénarios de panne ni de toute la chaîne en production.

## Objectif

Valider le comportement de Tsunade sur des incidents réels avant d’étendre ses capacités.

Tsunade doit pousser l’investigation déterministe aussi loin que possible. Elle peut déléguer à Katsuyu les traitements déterministes trop coûteux pour INFRA-01.

L’expertise IA de Katsuyu n’est sollicitée que lorsque les preuves disponibles, les investigations déterministes et les éventuels traitements lourds ne permettent pas à Tsunade d’établir un diagnostic suffisamment fiable.

Valider la frontière **Tsunade ↔ Katsuyu** : démontrer que Tsunade résout seule les incidents simples et transfère les traitements lourds ou les incidents complexes à Katsuyu avec un dossier de preuves ciblé, suffisant, structuré et exploitable.

Tsunade reste responsable :

- de l’orchestration de l’incident ;
- de la collecte et de la qualification des preuves ;
- du choix des investigations déterministes ;
- de la décision de déléguer un traitement à Katsuyu ;
- de la décision de solliciter ou non l’expertise IA de Katsuyu ;
- de l’exploitation du résultat retourné ;
- de l’état final de l’incident.

Katsuyu peut intervenir selon deux modes distincts :

1. **traitement déterministe lourd**, lorsque le calcul ou le volume de données serait trop coûteux pour INFRA-01 ;
2. **expertise IA**, lorsqu’une interprétation complexe, une corrélation avancée ou l’élaboration d’hypothèses est nécessaire.

Un appel à Katsuyu ne doit donc pas impliquer automatiquement l’utilisation du LLM.

---

## Principes de sûreté

Les investigations de Tsunade doivent respecter les principes suivants :

- privilégier les faits observables et reproductibles ;
- distinguer clairement observation, preuve, conclusion déterministe et hypothèse ;
- ne jamais transformer une absence de preuve en preuve d’absence ;
- ne jamais produire artificiellement une conclusion lorsque le contexte est insuffisant ;
- conserver explicitement un diagnostic comme indéterminé lorsqu’une cause ne peut pas être démontrée ;
- ne jamais relancer une analyse coûteuse sans nouvelle information utile ;
- ne jamais utiliser Katsuyu pour reformuler simplement ce que Tsunade sait déjà ;
- préserver le fonctionnement essentiel de Konoha même lorsque Bubule ou Katsuyu sont indisponibles.

---

## Cycle de vie d’un incident

Tsunade doit maintenir un état explicite pour chaque incident.

Le cycle de diagnostic cible de la Phase 1 est :

```text
Shikamaru détecte
        │
        ▼
     DETECTED
        │
        ▼
   INVESTIGATING
        │
        ├──────── diagnostic déterministe suffisant
        │                       │
        │                       ▼
        │                   DIAGNOSED
        │
        ├──────── traitement lourd nécessaire
        │                       │
        │                       ▼
        │               WAITING_KATSUYU
        │                       │
        │                       ▼
        │                  INVESTIGATING
        │
        ├──────── expertise IA nécessaire
        │                       │
        │                       ▼
        │               WAITING_KATSUYU
        │                       │
        │                       ▼
        │                  INVESTIGATING
        │
        └──────── preuves insuffisantes
                                │
                                ▼
                     INSUFFICIENT_CONTEXT
```

Un retour à `INVESTIGATING` ne doit intervenir que lorsqu’un résultat ou une nouvelle preuve est réellement disponible.

Un incident peut également passer à :

- `MONITORING` lorsqu’aucune intervention immédiate n’est requise mais qu’une évolution doit être observée ;
- `RESOLVED` lorsque Shikamaru confirme que la situation ayant déclenché l’incident n’existe plus ;
- `INVESTIGATION_BLOCKED` lorsqu’une investigation nécessaire ne peut pas être exécutée, par exemple en raison de l’indisponibilité de Katsuyu.

Les états liés aux réparations (`WAITING_USER`, `REPAIRING`, `VERIFYING`, etc.) seront introduits et validés dans la Phase 2.

### Validation du cycle de vie

- [ ] Vérifier qu’un incident possède toujours un état explicite.
- [ ] Vérifier qu’aucun incident ne reste bloqué silencieusement entre deux étapes.
- [ ] Vérifier qu’un passage vers `WAITING_KATSUYU` indique clairement le type de traitement demandé.
- [ ] Vérifier qu’un retour à `INVESTIGATING` correspond à l’arrivée effective d’une nouvelle information.
- [ ] Vérifier qu’un contexte réellement insuffisant conduit à `INSUFFICIENT_CONTEXT`.
- [ ] Vérifier qu’une indisponibilité d’une dépendance d’investigation conduit à un état explicite plutôt qu’à une fausse conclusion.
- [ ] Vérifier qu’un incident résolu spontanément ou extérieurement peut être correctement clôturé après vérification Shikamaru.

---

## Validation des investigations

- [ ] Valider les investigations automatiques en lecture seule sur INFRA-01.
- [ ] Valider les investigations automatiques sur HA-01.
- [ ] Valider les investigations automatiques sur LINKY-01.
- [x] Valider les investigations automatiques sur ZWAVE-01 (cycle borné du 19 septembre à 17:50–17:53 : collecte ciblée, DNS/TCP, Supervisor Z-Wave JS UI et réévaluation terminés ; scénarios de panne restant à exercer).
- [ ] Vérifier les diagnostics MQTT de Mosquitto.
- [ ] Vérifier les diagnostics `teleinfo2mqtt`.
- [ ] Vérifier les contrôles Supervisor Home Assistant (sélection Z-Wave JS UI, état et ressources confirmés en production avec Agent 1.29.8 le 19 septembre à 17:51 ; couverture des cas d’échec restante).
- [ ] Vérifier les investigations DNS, TCP et HTTP (HEAD 302/401/403/503 et absence de redirection vérifiés sur serveur local ; sélection HTTP avant plafond de sondes corrigée et testée localement le 19 septembre, cibles omises explicites ; validation HTTP sur les cibles réelles restante).
- [x] Vérifier les métriques système collectées sur INFRA-01 (snapshot CPU, mémoire, disque et unités du 15 septembre ; scénario de surcharge restant).
- [ ] Vérifier que les secrets restent exclus des preuves.
- [ ] Vérifier que chaque preuve conserve sa provenance, son horodatage et son lien avec l’incident.
- [ ] Vérifier que les preuves devenues obsolètes ne sont pas utilisées comme si elles représentaient encore l’état courant.

---

## Qualité des diagnostics

Tsunade doit distinguer explicitement :

- les faits établis ;
- les résultats de contrôles déterministes ;
- les conclusions déterministes ;
- les éléments manquants ;
- les hypothèses éventuelles ;
- les contributions provenant de Katsuyu ;
- les limites du diagnostic.

### Niveau de confiance

Un diagnostic doit utiliser des catégories simples et explicables, sans produire de pourcentage artificiel.

Les niveaux retenus sont :

- **CONFIRMED** : la conclusion est directement établie par des preuves et des règles déterministes suffisantes ;
- **PROBABLE** : les preuves convergent vers une explication mais ne permettent pas de la démontrer complètement ;
- **INSUFFICIENT_CONTEXT** : les informations disponibles sont insuffisantes pour établir une conclusion exploitable.

Le niveau de confiance doit toujours être accompagné de sa justification.

Une expertise IA de Katsuyu ne transforme pas automatiquement une hypothèse en diagnostic `CONFIRMED`.

### Validation

- [ ] Vérifier que Tsunade distingue clairement les faits établis, les conclusions déterministes, les éléments manquants et les points nécessitant éventuellement une expertise Katsuyu.
- [ ] Vérifier que chaque diagnostic possède un niveau de confiance explicite.
- [ ] Vérifier qu’un diagnostic `CONFIRMED` repose sur des critères déterministes définis.
- [ ] Vérifier qu’un diagnostic `PROBABLE` indique clairement ce qui empêche sa confirmation.
- [ ] Vérifier que `INSUFFICIENT_CONTEXT` déclenche une investigation complémentaire utile lorsqu’une telle investigation est possible.
- [ ] Vérifier que `INSUFFICIENT_CONTEXT` reste un résultat acceptable lorsqu’aucune preuve supplémentaire ne peut raisonnablement être obtenue.
- [ ] Vérifier qu’une absence de preuve n’est jamais utilisée comme preuve d’absence.
- [ ] Vérifier qu’une hypothèse produite par Katsuyu reste identifiable comme telle.
- [x] Vérifier que les anomalies déjà connues ne déclenchent pas inutilement une nouvelle sollicitation de Katsuyu (Agent 1.29.7 : global → INFRA-01 seul → global validé le 19 septembre à 17:13–17:14, références conservées et aucune nouvelle analyse IA ; répétition des corrélations également validée en rejeu local).
- [x] Vérifier que l’arrivée de nouvelles observations peut rouvrir correctement une analyse (nouvelles corrélations du 16 septembre, contrôle 09:01–09:03).
- [x] Vérifier que les diagnostics terminés ne sont pas relancés sans nouvelle information (tests de cycle et rejeu avec réouverture de base ; reprise en production restant à observer).
- [ ] Vérifier que les faux positifs MQTT, série et télémétrie restent maîtrisés.
- [ ] Vérifier qu’un diagnostic déterministe suffisant termine l’investigation sans solliciter l’expertise IA de Katsuyu.
- [ ] Vérifier qu’une situation réellement ambiguë ou complexe provoque correctement une escalade vers l’expertise IA de Katsuyu.

---

## Maîtrise des cycles d’investigation

Tsunade doit empêcher les investigations de produire des boucles, des réveils inutiles de Bubule ou une consommation excessive de ressources.

Chaque nouvelle étape d’investigation doit être justifiée par une nouvelle information, une preuve manquante identifiable ou une décision explicite du moteur d’investigation.

### Garde-fous

- [ ] Limiter le nombre de réinvestigations successives sans nouvelle preuve.
- [ ] Ne pas relancer Katsuyu pour un dossier d’investigation inchangé.
- [ ] Ne pas relancer une expertise IA avec les mêmes preuves et la même question.
- [ ] Limiter les réveils successifs de Bubule pour un même incident.
- [ ] Regrouper lorsque possible plusieurs traitements Katsuyu compatibles dans un même cycle worker.
- [ ] Conserver la raison ayant déclenché chaque nouvelle investigation.
- [ ] Conserver la preuve ou l’événement ayant justifié la réouverture d’un incident.
- [ ] Détecter et interrompre un éventuel cycle `investigation → Katsuyu → réévaluation → Katsuyu`.
- [ ] Ne pas considérer une reformulation du même résultat comme une nouvelle information.
- [ ] Prévoir une sortie explicite en `INSUFFICIENT_CONTEXT` ou `INVESTIGATION_BLOCKED` lorsque poursuivre l’investigation n’apporte plus de valeur.

Les limites exactes de tentatives et de réveils doivent rester configurables et adaptées au type d’investigation plutôt qu’être codées de manière arbitraire dans la logique métier.

---

## Validation de la frontière Tsunade ↔ Katsuyu

Tsunade doit rester le coordinateur de l’incident.

Katsuyu fournit une capacité d’exécution ou d’expertise et ne devient jamais le propriétaire de l’incident ni le moteur de décision final.

### Dossier transmis à Katsuyu

Avant toute sollicitation de Katsuyu, Tsunade doit constituer un dossier contenant au minimum :

- l’identifiant de l’incident ;
- la cible concernée ;
- le type de traitement demandé ;
- les faits établis ;
- les résultats des contrôles déjà effectués ;
- les preuves pertinentes ;
- leur provenance ;
- leur horodatage ;
- les éléments encore manquants ;
- la question précise à laquelle Katsuyu doit répondre.

### Types de sollicitation

Tsunade doit distinguer explicitement :

```text
Tsunade
   │
   ├── traitement déterministe lourd
   │        │
   │        ▼
   │     Katsuyu
   │     sans IA
   │        │
   │        ▼
   │ résultat structuré
   │
   └── expertise complexe
            │
            ▼
         Katsuyu
           IA
            │
            ▼
      analyse structurée

             │
             ▼
          Tsunade
```

### Validation

- [ ] Vérifier que Tsunade constitue un dossier d’investigation structuré avant toute sollicitation de Katsuyu.
- [ ] Vérifier que ce dossier contient les preuves nécessaires sans transmettre inutilement des données sans rapport avec l’incident.
- [ ] Vérifier que le dossier distingue les faits, les résultats des contrôles, les éléments manquants et la question soumise à Katsuyu.
- [ ] Vérifier que chaque preuve transmise conserve provenance et horodatage.
- [ ] Vérifier qu’un incident simple ne nécessitant aucun traitement lourd ne provoque aucun réveil de Bubule.
- [ ] Vérifier qu’un traitement déterministe trop coûteux pour INFRA-01 peut être délégué à Katsuyu sans déclencher d’expertise IA.
- [ ] Vérifier que l’expertise IA de Katsuyu n’est déclenchée que lorsque l’investigation déterministe et les éventuels traitements lourds ne permettent pas d’établir un diagnostic suffisamment fiable.
- [ ] Vérifier qu’un incident complexe peut provoquer le réveil de Bubule et l’exécution de Katsuyu.
- [ ] Vérifier que Katsuyu travaille à partir des preuves fournies par Tsunade plutôt que de recommencer systématiquement toute l’investigation.
- [ ] Vérifier que Katsuyu ne transforme pas arbitrairement une absence d’information en conclusion.
- [ ] Vérifier que la réponse de Katsuyu revient à Tsunade sous une forme structurée et exploitable.
- [ ] Vérifier que le résultat précise s’il provient d’un traitement déterministe ou d’une expertise IA.
- [ ] Vérifier que Tsunade reste responsable de l’interprétation et de l’état final de l’incident après le retour de Katsuyu.
- [ ] Vérifier qu’une indisponibilité de Bubule ou de Katsuyu ne bloque pas la supervision ni les investigations déterministes de Tsunade.
- [ ] Vérifier qu’une expertise impossible reste explicitement en attente ou bloquée plutôt que remplacée par une conclusion artificielle.

---

## Tests en production

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

Pour chaque scénario, déterminer explicitement :

1. ce que Shikamaru a réellement observé ;
2. quelles preuves Tsunade a collectées ;
3. si Tsunade peut établir seule un diagnostic fiable ;
4. si une investigation complémentaire déterministe est nécessaire ;
5. si un traitement déterministe lourd doit être délégué à Katsuyu ;
6. si une expertise IA de Katsuyu est réellement justifiée ;
7. quelles preuves sont transmises à Katsuyu ;
8. quelle valeur ajoutée réelle apporte Katsuyu ;
9. quel niveau de confiance est attribué au diagnostic final ;
10. si l’incident atteint correctement un état terminal ou explicitement bloqué.

---

## Critères de sortie de la Phase 1

La Phase 1 peut être considérée comme terminée lorsque les conditions suivantes sont remplies :

- [ ] Les investigations essentielles sur INFRA-01, HA-01, LINKY-01 et ZWAVE-01 ont été validées dans leur périmètre prévu.
- [ ] Les diagnostics MQTT, `teleinfo2mqtt`, DNS, TCP, HTTP et Supervisor nécessaires à la couverture actuelle de Konoha sont validés.
- [ ] Les principaux scénarios de panne contrôlée ont été exercés en production ou dans un environnement représentatif.
- [ ] Le cycle de vie des incidents fonctionne sans état ambigu ou incident silencieusement bloqué.
- [ ] Les diagnostics distinguent correctement faits, conclusions, hypothèses et éléments manquants.
- [ ] Les niveaux `CONFIRMED`, `PROBABLE` et `INSUFFICIENT_CONTEXT` sont cohérents et compréhensibles.
- [ ] Aucun secret n’est exposé dans les preuves ou les dossiers transmis.
- [ ] Les preuves conservent leur provenance et leur horodatage.
- [ ] Les cycles d’investigation inutiles ou répétitifs sont maîtrisés.
- [ ] Un dossier inchangé ne provoque pas de nouvelle expertise IA.
- [ ] Un incident simple reste traité par Tsunade lorsque Katsuyu n’apporte aucune valeur.
- [ ] Un traitement déterministe lourd peut être correctement déporté vers Katsuyu sans LLM.
- [ ] Une expertise IA n’est déclenchée que lorsqu’elle apporte une valeur supplémentaire identifiable.
- [ ] Une indisponibilité de Katsuyu ou de Bubule laisse Tsunade fonctionner en mode dégradé.
- [ ] Tsunade reste toujours propriétaire de l’incident et de la décision finale.
- [ ] Les résultats des investigations sont suffisamment lisibles dans Vision pour comprendre ce qui a été observé, testé, conclu et éventuellement délégué.

Une fois ces critères atteints, la Phase 2 peut étendre le moteur stabilisé vers le cycle complet **incident → décision → réparation supervisée → vérification**.

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
        ├── diagnostic suffisant ───────────────────────┐
        │                                               │
        ├── traitement lourd requis                     │
        │          │                                    │
        │          ▼                                    │
        │       Katsuyu                                 │
        │   déterministe                                │
        │          │                                    │
        │          ▼                                    │
        │       résultat                                │
        │                                               │
        └── expertise nécessaire                        │
                   │                                    │
                   ▼                                    │
                Katsuyu                                 │
                   IA                                   │
                   │                                    │
                   ▼                                    │
              expertise                                 │
                   │                                    │
                   └────────────────┬───────────────────┘
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

- [ ] Conserver une autorisation humaine pour toute action corrective modifiant l’état de Konoha, hors opérations techniques explicitement préautorisées du cycle worker Katsuyu telles que Wake-on-LAN, exécution d’un job autorisé et arrêt après traitement.
- [ ] En dehors des opérations techniques explicitement préautorisées du cycle worker Katsuyu, autoriser automatiquement uniquement les investigations strictement en lecture seule.
- [ ] Afficher clairement dans Shizune la conséquence d’une action avant validation.
- [ ] Conserver la provenance Vision ou Shizune de chaque autorisation.
- [ ] Conserver l’historique de l’action et de son résultat.


## Critères de validation de la Phase 2

La Phase 2 peut être considérée comme validée lorsque :

- [ ] Au moins une réparation supervisée a été exercée de bout en bout en conditions réelles ou représentatives.
- [ ] Le cycle `diagnostic → décision → autorisation → exécution → vérification` fonctionne sans état ambigu.
- [ ] Toute action corrective modifiant Konoha nécessite une autorisation humaine, hors opérations techniques explicitement préautorisées du cycle Katsuyu.
- [ ] Shizune et Vision affichent clairement l’action proposée, sa cible, ses conséquences et son niveau de risque avant validation.
- [ ] La provenance de chaque autorisation est conservée.
- [ ] Chaque réparation est associée à des préconditions, un résultat attendu et un mécanisme de vérification Shikamaru.
- [ ] Une réparation refusée, différée ou non autorisée ne peut pas être exécutée.
- [ ] Une réparation déjà échouée n’est pas répétée automatiquement sans nouvelle preuve ou nouvelle décision explicite.
- [ ] Un échec de réparation laisse l’incident dans un état explicite et exploitable.
- [ ] Les résultats de vérification sont conservés dans l’historique de l’incident.
- [ ] Le redémarrage de `dnsmasq.service` sert de procédure de référence documentée et reproductible.
- [ ] Au moins un autre type de réparation supervisée a été validé ou préparé selon le même contrat.
- [ ] Shikamaru reste responsable de la vérification du retour à l’état attendu.
- [ ] Tsunade reste responsable de la décision et de l’état final de l’incident.

Une fois ces critères atteints, la Phase 3 peut capitaliser les réparations validées sans transformer cette mémoire en apprentissage autonome.

---

# Phase 3 — Mémoire opérationnelle de Tsunade

## Objectif

Permettre à Tsunade de réutiliser ce qui a déjà fonctionné sans transformer sa mémoire opérationnelle en système d’apprentissage autonome ni déléguer la décision à Katsuyu.

### Réparations connues

- [ ] Consolider les réparations déjà validées.
- [ ] Associer une réparation connue aux symptômes et preuves qui l’ont justifiée.
- [ ] Conserver le nombre de tentatives.
- [ ] Conserver le nombre de réussites.
- [ ] Conserver les échecs.
- [ ] Conserver la date de dernière réussite.
- [ ] Présenter le taux de réussite dans Vision.

### Capitalisation des réparations manuelles

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
- [ ] Demander confirmation avant enregistrement comme réparation connue.
- [ ] Ne jamais transformer automatiquement une commande libre en action exécutable.
- [ ] Transformer uniquement les cas retenus en procédures déterministes implémentées explicitement.
- [ ] Ne jamais considérer la simple proximité temporelle entre une action et un retour à la normale comme une preuve suffisante de causalité.


## Critères de validation de la Phase 3

La Phase 3 peut être considérée comme validée lorsque :

- [ ] Une réparation connue peut être associée à un ensemble explicite de symptômes et de preuves.
- [ ] Les tentatives, réussites, échecs et date de dernière réussite sont correctement historisés.
- [ ] Vision affiche un historique compréhensible des réparations connues.
- [ ] Le taux de réussite est calculé à partir de données réellement observées et non estimées.
- [ ] Une action manuelle peut être déclarée par l’utilisateur et corrélée au retour à l’état sain.
- [ ] La simple proximité temporelle entre une action manuelle et un retour à la normale n’est jamais considérée comme une preuve suffisante de causalité.
- [ ] Tsunade demande une confirmation explicite avant d’enregistrer une action comme réparation connue.
- [ ] Une commande libre ou une action textuelle n’est jamais transformée automatiquement en commande exécutable.
- [ ] Toute réparation exécutable reste une procédure déterministe implémentée explicitement.
- [ ] Une réparation connue peut être retirée, désactivée ou déclarée obsolète sans perdre son historique.
- [ ] La mémoire opérationnelle ne permet pas à Katsuyu de devenir le moteur autonome de décision.
- [ ] La réutilisation d’une réparation connue respecte toujours la politique d’autorisation définie en Phase 2.

Une fois ces critères atteints, la Phase 4 peut exploiter l’historique et les observations pour détecter des tendances avant qu’elles ne deviennent des incidents critiques.

---

# Phase 4 — Maintenance préventive

## Objectif

Passer progressivement d’une logique uniquement réactive à une logique de détection précoce.

Tsunade ne doit pas chercher artificiellement des problèmes.

Elle doit exploiter les observations déjà produites par Shikamaru et les contrôles planifiés existants.

Shikamaru produit les mesures. Tsunade planifie et interprète les règles déterministes simples. Katsuyu peut être utilisé pour les traitements historiques ou les analyses de journaux trop coûteux pour INFRA-01.

```text
Shikamaru
   │
   │ observations
   ▼
Tsunade
   │
   ├── tendance simple ──────► diagnostic/règle
   │
   └── données volumineuses
              │
              ▼
           Katsuyu
              │
              ▼
        résultat structuré
              │
              ▼
           Tsunade
```

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

# Chantiers transverses

Les sections suivantes ne constituent pas nécessairement des étapes séquentielles. Elles évoluent en parallèle des phases fonctionnelles 1 à 4 selon les besoins rencontrés en production.


## Critères de validation de la Phase 4

La Phase 4 peut être considérée comme validée lorsque :

- [ ] Au moins plusieurs tendances simples sont détectées de manière reproductible à partir des observations existantes.
- [ ] Une évolution normale n’est pas systématiquement transformée en anomalie.
- [ ] Les seuils, fenêtres d’observation ou règles utilisées sont explicables et configurables lorsque nécessaire.
- [ ] Les tendances simples restent interprétées par des règles déterministes dans Tsunade.
- [ ] Les traitements historiques ou volumineux peuvent être déportés vers Katsuyu sans rendre Bubule critique pour la supervision.
- [ ] Une analyse lourde Katsuyu retourne un résultat structuré exploitable par Tsunade.
- [ ] L’indisponibilité de Katsuyu n’empêche pas les contrôles préventifs essentiels.
- [ ] Les anomalies récurrentes de journaux peuvent être distinguées d’événements isolés.
- [ ] Les redémarrages répétés, pertes réseau répétitives et dégradations de temps de réponse peuvent être détectés sans créer de boucle d’incidents.
- [ ] Une synthèse préventive courte et compréhensible est disponible dans Shizune.
- [ ] Le détail technique correspondant est disponible dans Vision.
- [ ] Une synthèse indiquant « aucune intervention nécessaire » reste possible lorsque Konoha est stable.
- [ ] La maintenance préventive ne déclenche pas automatiquement une réparation non autorisée.

La Phase 4 est validée lorsque Tsunade peut signaler des dérives utiles sans chercher artificiellement des problèmes ni surcharger INFRA-01.

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


## Critères de validation de la Phase 5

La Phase 5 peut être considérée comme satisfaisante lorsque :

- [ ] Agent expose un état exploitable de son service, de ses ressources et de ses composants internes critiques.
- [ ] L’âge de la dernière observation permet de détecter une supervision figée ou silencieuse.
- [ ] Les files internes importantes possèdent un état ou une longueur observable.
- [ ] Le stockage Tsunade possède un état de santé vérifiable.
- [ ] La file Katsuyu possède un état exploitable.
- [ ] Vision expose son état HTTP, WebSocket, ingestion et rétention.
- [ ] La croissance de la base Vision peut être suivie dans le temps.
- [ ] Katsuyu expose l’état du worker, des jobs, du workspace et du runtime IA.
- [ ] Une dernière exécution réussie Katsuyu est identifiable.
- [ ] Shizune expose l’état de sa passerelle, de sa synchronisation, de sa version et de son association.
- [ ] Une défaillance d’un composant Ohana peut elle-même générer une observation ou un incident exploitable.
- [ ] La supervision d’Ohana ne crée pas de dépendance circulaire critique entre ses propres composants.
- [ ] L’indisponibilité d’un composant n’empêche pas d’observer les autres composants lorsqu’ils restent accessibles.

La phase est satisfaisante lorsque les composants Ohana deviennent eux-mêmes des éléments observables de Konoha sans créer un système d’auto-surveillance fragile.

---

# Phase 6 — Katsuyu

## Objectif

Conserver Bubule comme capacité de calcul optionnelle et non critique.

Une panne ou une extinction de Bubule ne doit jamais empêcher les fonctions essentielles de Konoha.

Une indisponibilité de Katsuyu doit laisser Tsunade poursuivre les investigations déterministes. Une expertise impossible reste explicitement en attente et ne doit jamais être remplacée par une conclusion artificielle.

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


## Critères de validation de la Phase 6

La Phase 6 peut être considérée comme satisfaisante lorsque :

- [ ] Bubule reste une capacité optionnelle et non critique.
- [ ] Le Wake-on-LAN fonctionne de manière fiable lorsque Katsuyu est nécessaire.
- [ ] Un worker déjà disponible est réutilisé sans réveil inutile.
- [ ] Plusieurs jobs compatibles peuvent être regroupés dans un même cycle worker.
- [ ] L’arrêt après traitement n’intervient que lorsque les conditions prévues sont réunies.
- [ ] Bubule n’est pas arrêté par Ohana lorsqu’un usage utilisateur actif ou un état bloquant est détecté.
- [ ] Un job interrompu peut être repris ou marqué explicitement comme échoué.
- [ ] Les traitements déterministes lourds fonctionnent indépendamment du runtime IA lorsqu’ils n’en ont pas besoin.
- [ ] Une indisponibilité du runtime IA n’empêche pas les handlers déterministes compatibles de fonctionner.
- [ ] Une expertise IA impossible reste explicitement en attente ou en échec sans produire de conclusion artificielle.
- [ ] Le workspace peut être contrôlé et son intégrité vérifiée.
- [ ] Les métriques de durée, ressources et résultat des jobs sont disponibles.
- [ ] Vision permet d’identifier les traitements réellement déportés depuis INFRA-01.
- [ ] Le bénéfice du déport de traitements peut être mesuré sans rendre Katsuyu systématique.
- [ ] L’ajout d’un nouveau handler reste motivé par un besoin réel identifié.

La phase est satisfaisante lorsque Katsuyu apporte puissance de calcul et expertise complexe sans devenir une dépendance essentielle du fonctionnement de Konoha.

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


## Critères de validation de la Phase 7

La Phase 7 peut être considérée comme satisfaisante lorsque :

- [ ] Shizune reste installable et utilisable comme PWA sur iPhone sans dépendance à une application native.
- [ ] L’état général de Konoha est compréhensible sans afficher la complexité technique de Vision.
- [ ] Les incidents prioritaires sont présentés de manière synthétique.
- [ ] Les décisions demandées par Tsunade sont clairement identifiables.
- [ ] L’utilisateur peut autoriser, refuser ou reporter une décision sans ambiguïté.
- [ ] Le contexte nécessaire à une décision est visible sans exposer des détails techniques inutiles.
- [ ] Les investigations complémentaires peuvent être suivies sans transformer Shizune en cockpit d’administration.
- [ ] Les informations présentées proviennent des contrats Agent et ne recréent pas une logique métier parallèle.
- [ ] L’association compagnon reste contrôlée et réversible.
- [ ] Une perte de synchronisation ou une passerelle indisponible est explicitement signalée.
- [ ] Aucune administration technique directe de Konoha n’est introduite dans Shizune.
- [ ] L’absence de notifications push natives n’empêche pas l’usage quotidien prévu.
- [ ] De nouvelles fonctions ne sont ajoutées qu’en réponse à un besoin réellement constaté.

La phase est satisfaisante lorsque Shizune remplit son rôle d’interface personnelle sans devenir un second Vision.

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
- [ ] afficher clairement si un diagnostic est entièrement déterministe, complété par un traitement Katsuyu ou issu d’une expertise IA Katsuyu ;
- [ ] rendre l’historique des réparations réellement utile ;
- [ ] conserver Vision sans logique métier dupliquée depuis Agent.


## Critères de validation de la Phase 8

La Phase 8 peut être considérée comme satisfaisante lorsque :

- [ ] Le centre d’incidents permet de comprendre rapidement l’état actuel d’un incident.
- [ ] Observation, diagnostic, décision, intervention et résultat sont visuellement distincts.
- [ ] Les investigations Tsunade sont lisibles sans consulter directement les données internes d’Agent.
- [ ] Les faits, preuves, conclusions et hypothèses sont clairement distingués.
- [ ] Le niveau de diagnostic et les limites d’une analyse sont visibles.
- [ ] Vision indique clairement si un résultat est déterministe, issu d’un traitement Katsuyu ou d’une expertise IA Katsuyu.
- [ ] Les contributions Katsuyu restent attribuées à Katsuyu et ne sont pas présentées comme des faits établis lorsqu’elles sont hypothétiques.
- [ ] L’historique d’une réparation permet de retrouver la décision, l’autorisation, l’exécution et la vérification.
- [ ] Les informations de supervision de Shikamaru restent accessibles sans dupliquer sa logique dans Vision.
- [ ] Vision ne reconstruit pas le cycle de vie des incidents à partir d’heuristiques locales.
- [ ] Les états affichés proviennent des contrats d’Agent.
- [ ] Les performances de l’interface restent acceptables avec l’historique et les investigations activés.
- [ ] L’ajout d’informations techniques ne dégrade pas la lisibilité générale du cockpit.

La phase est satisfaisante lorsque Vision permet d’expliquer ce qui s’est passé dans Konoha sans devenir une seconde implémentation de Tsunade ou Shikamaru.

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
- [ ] améliorer la contextualisation et la qualification des observations entre capacités ;
- [ ] exploiter les groupes de disponibilité pour les services redondants ;
- [ ] ajouter une capacité uniquement lorsqu’elle garantit une fonction réelle de Konoha.


## Critères de validation de la Phase 9

La Phase 9 peut être considérée comme satisfaisante lorsque :

- [ ] Les capacités existantes produisent des observations stables et exploitables.
- [ ] Les faux positifs connus sont réduits ou explicitement documentés.
- [ ] Les états transitoires sont distingués d’une indisponibilité réelle lorsque les données disponibles le permettent.
- [ ] La contextualisation entre capacités améliore les observations sans produire de diagnostic à la place de Tsunade.
- [ ] Les dépendances objectives entre capacités peuvent être représentées sans introduire d’interprétation causale non démontrée.
- [ ] Les groupes de disponibilité peuvent représenter correctement les services redondants lorsqu’ils existent.
- [ ] Une capacité nouvelle n’est ajoutée que lorsqu’elle correspond à une fonction réellement importante de Konoha.
- [ ] Chaque capacité possède des critères de santé explicites.
- [ ] L’âge de l’observation permet d’identifier une donnée devenue obsolète.
- [ ] Les changements d’état sont historisés de manière exploitable par Tsunade.
- [ ] Une panne de Shikamaru ou d’un de ses collecteurs est distinguée de la panne de la capacité observée.
- [ ] La charge de supervision reste adaptée à INFRA-01.

La phase est satisfaisante lorsque Shikamaru fournit des observations fiables, contextualisées et suffisamment neutres pour permettre à Tsunade de raisonner sans dupliquer les rôles.

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


## Critères de validation de la Phase 10

La Phase 10 peut être considérée comme satisfaisante lorsque :

- [ ] Une sauvegarde HAOS peut être restaurée dans une procédure documentée et vérifiée.
- [ ] Une sauvegarde INFRA-01 peut être restaurée dans une procédure documentée et vérifiée.
- [ ] La date du dernier test de restauration est conservée.
- [ ] Une sauvegarde jamais restaurée ou jamais testée est explicitement signalée.
- [ ] L’intégrité des archives peut être vérifiée indépendamment de leur date de création.
- [ ] Les archives anciennes font l’objet d’un contrôle périodique.
- [ ] Le chiffrement `age` reste vérifiable sans exposer les secrets.
- [ ] La sauvegarde vers iCloud est considérée comme réussie uniquement lorsque l’archive attendue est réellement disponible.
- [ ] Le streaming évite bien le stockage permanent inutile sur la microSD d’INFRA-01.
- [ ] Katsuyu réalise les traitements lourds prévus sans rendre la sauvegarde impossible lorsque Bubule est temporairement indisponible.
- [ ] Les versions nécessaires à la restauration sont inventoriées.
- [ ] Une restauration incomplète ou échouée produit un état explicite.
- [ ] L’état des sauvegardes et restaurations est exploitable par la maintenance préventive Tsunade.
- [ ] Une alerte est produite lorsque l’ancienneté du dernier test de restauration dépasse la politique définie.

La phase est satisfaisante lorsqu’une sauvegarde n’est plus considérée comme fiable parce qu’elle existe, mais parce qu’elle a été vérifiée et peut réellement être restaurée.

---

# Phase 11 — Documentation et cohérence de l’écosystème

## Objectif

Faire correspondre en permanence la documentation, les contrats techniques et les compositions de releases avec le logiciel réellement livré.

La documentation ne doit pas décrire une architecture théorique différente de celle exécutée en production.

Les échanges entre composants doivent rester explicites, versionnés et compatibles afin qu’une évolution d’un dépôt ne puisse pas casser silencieusement un autre composant d’Ohana.

Cette phase est transverse : elle accompagne les autres phases fonctionnelles et doit être mise à jour au fur et à mesure des évolutions réellement validées.

---

## Documentation fonctionnelle

La documentation doit décrire le rôle réel de chaque composant et les frontières entre responsabilités.

- [ ] Maintenir `ROADMAP.md` à chaque évolution fonctionnelle importante.
- [ ] Supprimer ou archiver les éléments historiques devenus faux, obsolètes ou redondants.
- [ ] Maintenir le diagramme d’architecture global.
- [ ] Documenter clairement les responsabilités de Shikamaru, Tsunade, Katsuyu, Vision et Shizune.
- [ ] Documenter explicitement la frontière Tsunade ↔ Katsuyu.
- [ ] Documenter la distinction entre traitement déterministe lourd et expertise IA Katsuyu.
- [ ] Documenter le cycle de vie des incidents Tsunade.
- [ ] Documenter les niveaux de diagnostic `CONFIRMED`, `PROBABLE` et `INSUFFICIENT_CONTEXT`.
- [ ] Documenter le comportement attendu lorsqu’une investigation est bloquée ou qu’une dépendance est indisponible.
- [ ] Documenter les garde-fous empêchant les boucles d’investigation inutiles.
- [ ] Maintenir la documentation de la PWA Shizune et de son rôle limité à l’interaction personnelle.
- [ ] Maintenir Vision comme référence du cockpit technique sans dupliquer la logique métier d’Agent.

---

## Documentation des investigations Tsunade

Chaque type d’investigation doit préciser :

- le déclencheur ;
- la cible ;
- les préconditions ;
- les contrôles effectués ;
- les preuves collectées ;
- leur provenance ;
- leur durée de validité lorsqu’elle est pertinente ;
- les conclusions déterministes possibles ;
- les situations conduisant à `INSUFFICIENT_CONTEXT` ;
- les conditions pouvant justifier un traitement Katsuyu ;
- les conditions pouvant justifier une expertise IA ;
- les limites connues de l’investigation.

### Validation

- [ ] Documenter les investigations INFRA-01.
- [ ] Documenter les investigations HA-01.
- [ ] Documenter les investigations LINKY-01.
- [ ] Documenter les investigations ZWAVE-01.
- [ ] Documenter les investigations DNS.
- [ ] Documenter les investigations TCP.
- [ ] Documenter les investigations HTTP.
- [ ] Documenter les investigations MQTT.
- [ ] Documenter les investigations `teleinfo2mqtt`.
- [ ] Documenter les investigations Supervisor Home Assistant.
- [ ] Documenter les investigations système et métriques INFRA-01.
- [ ] Documenter les limites et les cas connus de faux positifs.

---

## Documentation des réparations supervisées

Chaque réparation disponible dans Tsunade doit être documentée comme une procédure explicite.

Pour chaque réparation, conserver :

- le symptôme associé ;
- les preuves nécessaires ;
- les préconditions ;
- l’action exécutée ;
- le niveau d’autorisation requis ;
- les conséquences possibles ;
- les risques ;
- le retour arrière éventuel ;
- le délai avant vérification ;
- la vérification Shikamaru attendue ;
- les conditions de réussite ;
- les conditions d’échec ;
- le comportement après échec.

### Validation

- [ ] Documenter chaque réparation au moment où elle est introduite.
- [ ] Vérifier qu’aucune action modifiant Konoha n’existe uniquement dans le code sans documentation correspondante.
- [ ] Documenter les actions explicitement préautorisées.
- [ ] Documenter les actions nécessitant une autorisation utilisateur.
- [ ] Documenter les limites du nombre de tentatives.
- [ ] Documenter le comportement lorsqu’une réparation échoue.

---

## Contrat Tsunade ↔ Katsuyu

Le contrat Tsunade ↔ Katsuyu doit être considéré comme une interface majeure de l’architecture.

Tsunade reste propriétaire de l’incident.

Katsuyu reçoit une demande structurée et retourne un résultat structuré sans devenir responsable de la décision finale.

### Dossier d’entrée Katsuyu

Le contrat doit permettre de transmettre au minimum :

- l’identifiant de l’incident ;
- l’identifiant de la demande ;
- la cible ;
- le type de traitement demandé ;
- le contexte utile ;
- les faits établis ;
- les contrôles déjà exécutés ;
- les preuves pertinentes ;
- la provenance de chaque preuve ;
- l’horodatage de chaque preuve ;
- les éléments manquants ;
- la question ou le traitement demandé ;
- les limites éventuellement imposées au traitement.

Le type de traitement doit distinguer explicitement au minimum :

```text
DETERMINISTIC_HEAVY
AI_EXPERTISE
```

Un traitement `DETERMINISTIC_HEAVY` ne doit pas provoquer implicitement l’utilisation du LLM.

### Résultat Katsuyu

La réponse doit permettre de distinguer :

- le statut du traitement ;
- le type de traitement réellement exécuté ;
- les résultats déterministes produits ;
- les éléments analysés ;
- les hypothèses éventuelles ;
- les limites de l’analyse ;
- les éléments manquants ;
- les erreurs éventuelles ;
- la valeur produite pour Tsunade.

Une réponse Katsuyu ne doit pas modifier directement l’état final de l’incident.

Tsunade interprète le résultat et reste responsable de la suite.

### Validation

- [ ] Documenter le schéma d’entrée Tsunade → Katsuyu.
- [ ] Documenter le schéma de sortie Katsuyu → Tsunade.
- [ ] Documenter la distinction `DETERMINISTIC_HEAVY` / `AI_EXPERTISE`.
- [ ] Documenter le comportement en cas de timeout.
- [ ] Documenter le comportement lorsque Bubule est indisponible.
- [ ] Documenter le comportement lorsque le runtime IA est indisponible mais que les traitements déterministes restent disponibles.
- [ ] Documenter le comportement lorsque Katsuyu retourne un résultat incomplet.
- [ ] Documenter le comportement lorsqu’une demande est rejouée.
- [ ] Garantir l’idempotence lorsque le traitement s’y prête.
- [ ] Documenter les informations qui ne doivent jamais être transmises à Katsuyu.

---

## Versionnement des contrats inter-composants

Les échanges structurés entre dépôts doivent être explicitement versionnés.

Sont notamment concernés :

- les observations Shikamaru ;
- les incidents Tsunade ;
- les preuves ;
- les dossiers d’investigation ;
- les demandes Katsuyu ;
- les résultats Katsuyu ;
- les décisions Tsunade ;
- les demandes d’autorisation ;
- les réparations ;
- les résultats de vérification ;
- les données exposées à Vision ;
- les données exposées à Shizune.

Chaque contrat partagé doit posséder une version identifiable.

Une modification incompatible doit être considérée comme un changement de contrat et ne doit pas être introduite silencieusement.

### Règles

- [ ] Versionner les schémas partagés.
- [ ] Documenter les champs obligatoires.
- [ ] Documenter les champs optionnels.
- [ ] Documenter les valeurs d’énumération.
- [ ] Définir le comportement face à un champ inconnu.
- [ ] Définir le comportement face à une version non supportée.
- [ ] Maintenir la compatibilité ascendante lorsque cela reste raisonnable.
- [ ] Introduire une migration explicite lorsqu’une rupture de compatibilité est nécessaire.
- [ ] Ajouter des tests de contrat entre producteurs et consommateurs.

---

## Cycle de vie des incidents

Les états d’incident doivent être partagés entre Agent, Vision, Shizune et, lorsqu’il est concerné, Katsuyu.

Les états introduits par Tsunade doivent être documentés dans une source de référence unique.

Les transitions autorisées doivent également être explicites.

Exemples d’états de diagnostic :

```text
DETECTED
INVESTIGATING
WAITING_KATSUYU
DIAGNOSED
MONITORING
INSUFFICIENT_CONTEXT
INVESTIGATION_BLOCKED
RESOLVED
```

Les états liés à la réparation peuvent notamment compléter ce cycle :

```text
WAITING_USER
REPAIRING
VERIFYING
```

### Validation

- [ ] Documenter chaque état.
- [ ] Documenter les transitions autorisées.
- [ ] Documenter l’acteur responsable de chaque transition.
- [ ] Interdire les états ou transitions connus uniquement de Vision ou de Shizune.
- [ ] Garantir que Vision et Shizune représentent l’état fourni par Agent plutôt que de reconstruire leur propre logique.
- [ ] Documenter les états terminaux.
- [ ] Documenter les états bloquants et leur mécanisme de reprise.

---

## Documentation réseau et dépendances

La documentation doit permettre de comprendre rapidement comment communiquent les composants.

- [ ] Documenter les ports réseau réellement utilisés.
- [ ] Documenter les protocoles utilisés.
- [ ] Documenter les flux entrants et sortants.
- [ ] Documenter les dépendances entre services.
- [ ] Documenter les communications locales entre Agent, Vision et les autres services d’INFRA-01.
- [ ] Documenter les communications INFRA-01 ↔ Bubule.
- [ ] Documenter les communications nécessaires à Shizune.
- [ ] Documenter les dépendances Home Assistant.
- [ ] Documenter les dépendances MQTT.
- [ ] Documenter les dépendances DNS et NTP.
- [ ] Identifier clairement les dépendances critiques et les dépendances optionnelles.

Les éléments d’authentification, clés, tokens et autres secrets ne doivent jamais apparaître dans cette documentation.

---

## Troubleshooting

Créer et maintenir un guide de diagnostic destiné à permettre une intervention humaine lorsque l’automatisation ne suffit pas.

Le guide doit privilégier des procédures courtes et reproductibles.

### Contenu attendu

- état d’Ohana-Agent ;
- état de Vision ;
- état de Katsuyu ;
- état de Shizune ;
- vérification des processus ;
- état des files internes ;
- diagnostic des erreurs de communication ;
- diagnostic du Wake-on-LAN ;
- diagnostic du cycle Katsuyu ;
- vérification des jobs en attente ;
- diagnostic des problèmes MQTT ;
- diagnostic des problèmes Home Assistant ;
- diagnostic de la télémétrie ;
- consultation des incidents Tsunade ;
- consultation des preuves ;
- récupération après une mise à jour défaillante ;
- vérification des versions installées.

### Validation

- [ ] Créer ou finaliser le guide Troubleshooting.
- [ ] Tester périodiquement les commandes et procédures documentées.
- [ ] Retirer les procédures devenues obsolètes.
- [ ] Préférer des commandes reproductibles aux explications dépendant d’un état historique du système.

---

## Documentation du cycle Katsuyu

Documenter complètement :

```text
Tsunade
   │
   ▼
Besoin Katsuyu
   │
   ▼
Vérification présence
   │
   ├── worker disponible
   │
   └── worker indisponible
               │
               ▼
          Wake-on-LAN
               │
               ▼
       attente disponibilité
               │
               ▼
         envoi du job
               │
               ▼
          traitement
               │
               ▼
       résultat Tsunade
               │
               ▼
      autres jobs en attente ?
         │             │
        oui           non
         │             │
         ▼             ▼
    traitement        arrêt
                     Bubule
```

- [ ] Documenter le Wake-on-LAN.
- [ ] Documenter le délai d’attente de disponibilité.
- [ ] Documenter le regroupement des jobs.
- [ ] Documenter les conditions autorisant l’arrêt de Bubule.
- [ ] Documenter les cas empêchant l’arrêt.
- [ ] Documenter la reprise après interruption.
- [ ] Documenter les timeouts.
- [ ] Documenter les jobs échoués.
- [ ] Documenter les jobs abandonnés.
- [ ] Documenter le comportement lorsqu’un utilisateur a démarré Bubule indépendamment d’Ohana.

---

## Cohérence inter-dépôts

Avant toute évolution majeure, vérifier conjointement :

- Ohana-Agent ;
- Ohana-Vision ;
- Ohana-Katsuyu ;
- Ohana-Shizune ;
- Ohana-Installer ;
- Ohana-Platform ;
- Ohana-House.

Les contrats partagés, configurations, manifestes et documentations doivent rester cohérents entre ces dépôts.

### Responsabilités principales

**Ohana-Agent**

Source de vérité pour :

- Shikamaru ;
- Tsunade ;
- cycle des incidents ;
- investigations ;
- décisions ;
- réparations supervisées ;
- orchestration Katsuyu.

**Ohana-Vision**

Consommateur des états et contrats Agent pour :

- affichage technique ;
- historique ;
- configuration ;
- administration ;
- diagnostics détaillés.

Vision ne doit pas réimplémenter la logique métier de Tsunade.

**Ohana-Katsuyu**

Implémente :

- les handlers lourds ;
- les traitements déterministes déportés ;
- l’expertise IA locale ;
- le runtime worker Bubule.

Katsuyu ne doit pas devenir un moteur autonome de décision ou d’administration de Konoha.

**Ohana-Shizune**

Consomme uniquement les informations nécessaires à l’interaction personnelle :

- état synthétique ;
- incidents prioritaires ;
- décisions ;
- demandes d’autorisation ;
- résultats utiles.

Shizune ne doit pas devenir un second Vision.

**Ohana-Installer**

Doit connaître :

- les versions compatibles ;
- les migrations nécessaires ;
- les dépendances d’installation ;
- les opérations de mise à jour.

**Ohana-Platform**

Doit maintenir :

- les compositions de releases ;
- les contrats communs ;
- les versions compatibles ;
- la documentation d’architecture partagée.

**Ohana-House**

Décrit Konoha réellement déployé sans devenir une copie de la configuration opérationnelle Agent.

---

## Validation avant release

Une release fonctionnelle importante doit vérifier au minimum :

1. la compatibilité des contrats ;
2. la cohérence des versions ;
3. les migrations nécessaires ;
4. les changements de configuration ;
5. les impacts sur Agent ;
6. les impacts sur Vision ;
7. les impacts sur Katsuyu ;
8. les impacts sur Shizune ;
9. les impacts sur Installer ;
10. les impacts sur Platform ;
11. les impacts éventuels sur Ohana-House ;
12. la documentation associée.

### Checklist

- [ ] Les versions déclarées sont cohérentes.
- [ ] Les contrats modifiés sont versionnés.
- [ ] Les tests inter-dépôts concernés passent.
- [ ] Les migrations sont disponibles.
- [ ] Les anciennes configurations compatibles restent supportées ou disposent d’une migration.
- [ ] Les notes de release décrivent les changements importants.
- [ ] La documentation correspond au comportement réellement livré.
- [ ] Aucun secret ou exemple sensible n’est ajouté à la documentation.
- [ ] La composition Platform référence les versions réellement compatibles.

---

## Critères de validation de la Phase 11

La cohérence documentaire de l’écosystème peut être considérée comme satisfaisante lorsque :

- [ ] les rôles des composants sont clairement documentés ;
- [ ] les frontières Shikamaru / Tsunade / Katsuyu sont explicites ;
- [ ] le cycle de vie des incidents possède une documentation de référence ;
- [ ] le contrat Tsunade ↔ Katsuyu est documenté et versionné ;
- [ ] les traitements déterministes lourds sont clairement distingués de l’expertise IA ;
- [ ] les contrats inter-composants critiques sont versionnés ;
- [ ] les états consommés par Vision et Shizune proviennent des sources métier appropriées ;
- [ ] les ports et flux réseau sont documentés ;
- [ ] le cycle Wake-on-LAN / jobs / arrêt Katsuyu est documenté ;
- [ ] les réparations supervisées sont documentées ;
- [ ] le guide Troubleshooting couvre les incidents opérationnels essentiels ;
- [ ] la documentation des différents dépôts ne contient pas de contradictions majeures ;
- [ ] les releases importantes incluent systématiquement une vérification de cohérence inter-dépôts.

La documentation doit rester une conséquence du logiciel réellement validé, et non devenir une spécification théorique indépendante de l’implémentation.

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


## Critères de validation de la Phase 12

La Phase 12 peut être considérée comme satisfaisante lorsque :

- [ ] Le vocabulaire d’Ohana-House est aligné avec Konoha et les rôles fonctionnels actuels.
- [ ] L’inventaire matériel reflète l’infrastructure réellement déployée.
- [ ] Les liaisons réseau documentées correspondent aux connexions réellement utilisées.
- [ ] Les équipements supervisés sont correctement identifiés.
- [ ] Les capacités annoncées comme garanties correspondent à des fonctions réellement observées et maintenues.
- [ ] Les dépendances entre services critiques sont documentées.
- [ ] Les informations de réseau, rôle et dépendance permettent de comprendre l’architecture sans consulter plusieurs sources contradictoires.
- [ ] Les données historiques ou anciennes sont clairement distinguées de l’état actuel.
- [ ] Ohana-House ne contient pas de secrets ou de configuration opérationnelle sensible inutile.
- [ ] Ohana-House ne duplique pas la configuration dynamique détenue par Agent.
- [ ] Une modification importante de Konoha entraîne une mise à jour correspondante d’Ohana-House.
- [ ] Les informations utilisées par la documentation, la roadmap et les schémas restent cohérentes entre elles.
- [ ] L’infrastructure de référence peut être comprise par une personne extérieure au développement sans dépendre d’informations implicites.

La phase est satisfaisante lorsqu’Ohana-House constitue une description fidèle, lisible et maintenable de Konoha, sans devenir une seconde source de configuration opérationnelle.

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

Elle consiste à rendre **Tsunade suffisamment fiable pour exploiter Konoha au quotidien**, en utilisant Shikamaru pour observer et vérifier, Katsuyu pour les traitements lourds et l’expertise complexe, Vision pour le cockpit technique et Shizune pour les interactions personnelles.
