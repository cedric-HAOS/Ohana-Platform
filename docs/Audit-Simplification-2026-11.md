# Audit de simplification — 4 novembre 2026

Lot 5 du [chantier maintenance et alerte](Chantier-Maintenance-systeme-et-alerte.md).
**Rien n'a été supprimé ni modifié** : ce rapport classe ce qui coûte de la
complexité ou du bruit, avec la mesure qui le justifie, pour que l'utilisateur
tranche. Mesures du 04/11, lecture seule sur INFRA-01.

## Ce qui va bien (inutile d'y toucher)

| Point | Mesure |
|---|---|
| Tests unitaires | Agent : 2 131 tests en 41 s ; le plus lent (2 s) est un test de roue Python |
| Sandbox | 49 scénarios en 141 s, tous réussis ; pas de tests lents à élaguer |
| Bruit de journaux | 83 lignes en 24 h pour l'Agent et Vision, 0 avertissement |
| Qualité statique | `ruff` propre ; tests du script de release : 25 réussis (l'échec signalé fin septembre n'existe plus) |
| Shizune | 521 lignes de source : rien à simplifier |

## Constats classés

Légende : gain = effet sur le bruit ou la charge d'entretien ; coût = effort
estimé ; risque = de casser quelque chose en production.

### 1. Bruit d'incidents — gain élevé, coût moyen, risque faible

122 incidents en 30 jours (environ 4 par jour), tous résolus, aucune réparation
proposée. Sur les 100 plus récents : 77 critiques, 43 résolus en moins de
10 minutes, 87 déjà survenus auparavant. Quelques sources concentrent le bruit :

| Source | Incidents |
|---|---|
| `dns.resolve` sur LINKY-01 | 19 |
| `home_assistant.telemetry.freshness` sur SUN-01 | 10 |
| `adguard_sync.status` sur INFRA-01 | 10 |
| `network.reachable` sur VAC-01 | 8 |
| `teleinformation.freshness` sur LINKY-01 | 8 |

Pistes : comprendre pourquoi le DNS de LINKY-01 vacille (19 fois), puis
n'ouvrir un incident qu'après une panne confirmée sur deux mesures pour les
sources qui se rétablissent seules en quelques minutes (la règle existe déjà
pour la télémétrie périmée). La politique de gravité « critique » par défaut
(77 % des incidents) mérite aussi d'être relue.

### 2. Fuite mémoire de l'Agent — risque réel, coût moyen

La règle `memory_growth` désigne l'Agent : environ **+10,9 Mo par jour**. C'était
le point ouvert depuis le 25/10 (redémarrage dans le même élan) : la cause reste
à trouver (profilage du processus). Ce n'est pas de la simplification, mais c'est
le défaut le plus coûteux de la liste.

### 3. Éléments « à surveiller » qui ne se résolvent jamais — gain moyen, coût nul

Trois éléments `backup_restore` (HA-01, LINKY-01, ZWAVE-01 : « jamais testée en
restauration ») restent à surveiller tant que vous n'avez pas déclaré de test de
restauration. Ils sont justes, mais constants : soit les tests sont réalisés et
déclarés (Phase 10), soit la règle est mise en sourdine (90 jours maximum).

### 4. Grosses classes et fonctions — gain moyen, coût élevé, risque moyen

| Fichier | Taille | Remarque |
|---|---|---|
| `api/service.py` (Agent) | 2 247 lignes, 118 méthodes | une seule classe porte toute l'API d'administration |
| `incidents.js` (Vision) | 2 713 lignes, 72 méthodes | un seul contrôleur ; 41 commits dont 6 depuis le 09/10 |
| `tsunade/preventive.py` | 1 132 lignes | règles réparties sur cinq modules |
| 10 fonctions de complexité supérieure à 15 | de 16 à 24 | `_snapshot` (AdGuard) 24, `build_production_agent` 22 |

Recommandation : ne pas tout découper d'un coup. Extraire par domaine à chaque
fois qu'on y touche (c'est ce que fait déjà `preventive_expiry.py`). Le lot 2 de
ce chantier a quand même ajouté une soixantaine de lignes à `service.py`.

### 5. Code de compatibilité — gain moyen, coût faible, **à confirmer**

- Vision : cinq branches « un Agent plus ancien ne fournit pas… ». Agent et
  Vision sont déployés ensemble par `ohana update` : elles ne servent plus.
- Agent : alias dépréciés de la télémétrie Home Assistant, adaptateur Shelly
  « hérité », vérification HTTP « hérité » de Z-Wave JS UI, correspondance
  globale d'entités « héritée », deux modules de réexport
  (`infrastructure/observation*.py`).

Je ne peux pas lire les fichiers de configuration d'INFRA-01 : avant de
supprimer, il faut confirmer qu'aucun n'utilise encore ces formes (vous, ou
`sudo` en lecture seule).

### 6. Duplication dans Vision — gain faible, coût faible

`renderCard` et `STATE_LABELS` existent en double dans `ohana.js` et
`system_updates.js` (cette dernière duplication est de mon fait) ; trois modules
formatent les dates de Paris chacun à sa façon alors que `utils.js` a déjà
`formatDate`. À factoriser dans `utils.js`.

### 7. Documentation — gain moyen, coût faible

- `ROADMAP.md` (2 050 lignes) garde une « base de référence » de Platform 1.0.100,
  Agent 1.29.0 : l'état réel est Platform 1.0.150, Agent 1.53.0. Un lecteur est
  induit en erreur dès la première page.
- La Phase 1 occupe environ 770 lignes de la roadmap et 2 608 lignes dans son
  document ; les Phases 1 à 10 totalisent 6 600 lignes. Les phases closes
  pourraient être réduites à leurs critères de sortie et à un renvoi vers
  l'archive.

### 8. Règles préventives — gain faible

15 règles, non redondantes entre elles (les trois règles de sauvegarde regardent
trois choses différentes). La seule dette est structurelle : leurs définitions
vivent dans cinq modules et la liste des identifiants « ignorables » est
assemblée à la main (elle a une troisième source depuis le lot 3). Un registre
unique suffirait.

### 9. Cadence des releases — gain faible

25 releases de composants depuis le 09/10 (Agent 11, Vision 7, Installer 6,
Katsuyu 1). Les commits « build(catalogue) » de l'Installer s'accumulent (quatre
fichiers de catalogue sont modifiés et non commités en ce moment). Des releases
groupées une fois par semaine, sauf urgence, réduiraient ce bruit sans perdre de
sécurité.

### 10. Pages de Vision — décision d'usage, pas de mesure

Timeline, Historique et Observations se recoupent, de même qu'Hôte, Ohana et
Infrastructure. Je n'ai pas de mesure d'usage pour trancher : c'est à vous de
dire lesquelles vous ouvrez réellement.

## Ordre proposé

1. Fuite mémoire de l'Agent (2).
2. DNS de LINKY-01 et règle de confirmation des incidents brefs (1).
3. Factorisation des helpers de Vision (6) et mise à jour de la base de la
   roadmap (7) : petits et sans risque.
4. Registre unique des règles préventives (8).
5. Suppression du code de compatibilité après confirmation des configurations (5).
6. Découpage de `service.py` et `incidents.js` au fil des changements (4).

Chaque point est indépendant et se décide séparément.

## Suite donnée (4 novembre 2026, soir)

Les points 1 à 6 ont été traités le jour même à la demande de l'utilisateur.
Rien de ce qui suit n'est publié ni déployé à l'heure de l'écriture, sauf le
diagnostic mémoire (Agent 1.54.1).

1. **Fuite mémoire de l'Agent** : diagnostic à la demande
   (`/v1/diagnostics/memory`, trace `tracemalloc` déployée en 1.54.1) puis mesures
   en production : les objets vivants sont stables (107 500 à 107 700 sur 10
   minutes, 0,7 Mo suivis), donc **pas de fuite d'objets**. Le seul gros
   consommateur éphémère est la sonde Z-Wave JS, qui charge toute l'état du
   contrôleur chaque minute (5 Mo de JSON, 1 700 valeurs, copies). Ce graphe en
   cycles attend le prochain ramasse-miettes complet et laisse des pages libres
   dans l'allocateur : la mémoire résidente ne fait que monter. Correctif :
   `release_freed_memory()` (ramasse-miettes puis `malloc_trim`) après chaque
   sonde. À confirmer par `memory_growth` quelques jours après déploiement. Une
   piste plus radicale (sonde dans un sous-processus) reste ouverte si ce
   correctif ne suffit pas.
2. **DNS de LINKY-01** : 10 des 20 incidents duraient moins de deux minutes (un
   contrôle manqué). Un échec DNS doit maintenant se répéter (`failure_threshold`,
   2 par défaut) ; le premier est « inconnu ». La cause du vacillement de LINKY-01
   reste inconnue (pas de lien avec la synchronisation AdGuard, qui tourne toutes
   les 5 minutes). Les autres sources bruyantes ont des durées médianes de 10 à
   30 minutes : ce sont de vraies indisponibilités, laissées telles quelles.
3. **Helpers de Vision et base de la roadmap** : cartes partagées entre « Ohana »
   et « Mise à jour système » ; `formatDate` affiche l'heure de Paris ; roadmap
   avec la composition courante.
4. **Registre unique des règles** : `all_rules()` ; correction d'un défaut au
   passage : les règles de sauvegarde, d'iCloud et d'AdGuard ne pouvaient pas
   être mises en sourdine (l'audit supposait le contraire).
5. **Compatibilité** : retirés `PluginRuntime.state()`, les alias `device_name`,
   `power`, `energy` de la télémétrie Home Assistant, l'attribut
   `shelly_telemetry_config` et `infrastructure.Observation`. Conservés : le
   fichier `shelly-telemetry.yaml`, le mode Linky par Home Assistant et la
   vérification HTTP de Z-Wave JS UI (dépendent de la configuration d'INFRA-01),
   et les cinq branches de Vision « Agent plus ancien », qui servent aussi de
   repli quand une lecture échoue.
6. **Découpage** : `service.py` passe de 2 265 à 853 lignes (cinq modules par
   domaine, copies à l'identique) ; les méthodes de maintenance préventive de
   `incidents.js` (299 lignes) sont dans `incidents_preventive.js`. `incidents.js`
   garde 2 414 lignes : le reste (journaux, réparations, décisions) reste à
   découper, car ses tests évaluent ce fichier seul.

Défaut constaté en direct : le bouton « Mettre à jour » a répondu « Agent :
délai dépassé » alors que l'installation démarrait. Cause : la demande relançait
la simulation apt, lente sur INFRA-01 (surtout avec la trace mémoire active).
Corrigé (dernière lecture réutilisée, délai de Vision porté à 30 s).
