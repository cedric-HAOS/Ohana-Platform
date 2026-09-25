# Versions, commits et releases

Convention commune à tous les dépôts `cedric-HAOS/Ohana-*`.

## Pourquoi

Depuis août 2026, presque chaque commit des dépôts Ohana est une release :
environ 50 pour Agent et 90 pour Platform. La plupart des messages ne décrivent
pas le changement (`v1.0.114` trois fois de suite, `Release Ohana-Agent 1.29.17`,
`modified: ROADMAP.md …`). Le détail n'existe que dans les CHANGELOG.

Conséquences :

- `git log` et `git blame` ne permettent pas de retrouver pourquoi une ligne a
  changé ;
- chaque correctif d'Agent entraîne une release Platform, puis une mise à jour
  d'Installer ;
- les numéros de version ne distinguent plus un correctif d'une nouvelle
  capacité.

## 1. Messages de commit

Format [Conventional Commits](https://www.conventionalcommits.org/fr/) :

```text
type(portée): résumé à l'impératif

Corps facultatif : pourquoi, et ce qui n'est pas évident dans le diff.
```

| Type | Usage |
| --- | --- |
| `feat` | nouvelle capacité visible (API, écran, plugin, champ de configuration) |
| `fix` | correction d'un comportement incorrect |
| `refactor` | restructuration sans changement de comportement |
| `perf` | amélioration de performance |
| `test` | ajout ou correction de tests uniquement |
| `docs` | documentation, ROADMAP, suivi de phase |
| `ci` / `build` | workflows GitHub, packaging, scripts de build |
| `chore` | maintenance sans effet fonctionnel |
| `release` | commit de release (voir § 3) |
| `revert` | annulation d'un commit |

La portée est facultative et libre, en minuscules : `tsunade`, `jobs`, `web`,
`dhcp`, `installer`, `sandbox`, `phase-1`…

Un changement incompatible (contrat d'API, format de configuration, schéma
SQLite) s'écrit avec un `!` : `feat(api)!: …`, et le corps explique la migration.

Exemples :

```text
fix(tsunade): lancer l'expertise directe sans source de journaux
feat(web): afficher la cible de chaque preuve network.ping
docs(phase-1): consigner la panne contrôlée SHE-04
release: Ohana-Agent 1.30.0
```

Un commit correspond à un seul changement logique. On ne mélange pas un
correctif et un changement de version.

Les workflows CI d'Agent, Vision, Installer et Platform vérifient le format
(voir § 6).

## 2. CHANGELOG : section « Non publié »

Chaque dépôt garde en tête de son `CHANGELOG.md` une section :

```markdown
## Non publié

- …
```

Chaque commit `feat` ou `fix` ajoute sa ligne dans cette section. Au moment de
la release, on la renomme en `## [X.Y.Z] — AAAA-MM-JJ — titre`, puis on recrée
une section vide.

## 3. Quand publier une release

Une release est une version **destinée à être déployée** sur INFRA-01 ou Bubule.
Ce n'est pas un point de sauvegarde du travail.

Règles :

1. Les correctifs s'accumulent sur `main` dans la section « Non publié ».
2. On publie quand le lot est qualifié (tests, Ruff, Sandbox adaptée) **et** que
   son déploiement est prévu.
3. Au plus **une release par composant et par jour**. Seule exception : un
   correctif urgent pour un défaut constaté en production.
4. Le commit de release ne contient que le changement de version et le
   CHANGELOG : `release: Ohana-Agent 1.30.0`.
5. Le tag `vX.Y.Z` est créé avec `git tag`. On ne fait pas de commit dont le
   message est seulement `v1.0.114`.

## 4. Numéros de version (SemVer)

| Incrément | Quand |
| --- | --- |
| **PATCH** `1.29.19 → 1.29.20` | uniquement des `fix`, sans changement de contrat |
| **MINOR** `1.29.x → 1.30.0` | au moins un `feat` : nouvelle capacité, nouvel endpoint, nouveau champ de configuration, migration SQLite rétrocompatible |
| **MAJOR** `1.x → 2.0.0` | changement incompatible (`!`) qui oblige Installer ou un autre composant à suivre |

Un lot qui mélange des `feat` et des `fix` donne une MINOR.

## 5. Releases Platform

Platform compose des versions ; elle ne suit pas chaque composant.

- On publie une release Platform **une fois par lot de déploiement**, avec
  toutes les versions de composants publiées dans ce lot, et non une par
  composant.
- Modifier ROADMAP, le suivi de phase ou la documentation donne un commit
  `docs`, sans release Platform.
- La Sandbox, les manifestes et le catalogue changent uniquement dans un commit
  `release: compose Platform 1.0.X` ou `build(sandbox): …`.

## 6. Contrôle automatique

Le workflow réutilisable
[`commit-messages.yml`](../../.github/workflows/commit-messages.yml) vérifie le
titre de chaque commit poussé :

- **pull request** : un titre non conforme fait échouer le contrôle ;
- **push direct sur une branche** : un titre non conforme produit un
  avertissement dans l'onglet Actions. Il ne bloque rien, puisqu'un commit déjà
  poussé sur `main` ne peut plus être renommé.

Les commits de merge et les titres `Revert "…"` générés par Git sont acceptés.
