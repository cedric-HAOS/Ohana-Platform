# Diagrammes officiels de la plateforme Ohana

Ce répertoire rassemble l'ensemble des diagrammes SVG officiels de la plateforme Ohana.

Les diagrammes constituent la représentation graphique de l'architecture de référence. Ils complètent la documentation présente dans le répertoire `docs/` et sont utilisés dans les différents documents d'architecture, les guides et les présentations.

Les diagrammes sont organisés par domaine fonctionnel afin de distinguer les vues d'architecture, les flux métier et les scénarios de déploiement.

---

# Organisation

```text
diagrams/
├── README.md
│
├── architecture/
│   ├── ecosystem.svg
│   ├── platform-architecture.svg
│   └── data-flow.svg
│
├── flows/
│   ├── observation-flow.svg
│   ├── event-flow.svg
│   ├── health-flow.svg
│   ├── timeline-flow.svg
│   ├── visualization-flow.svg
│   ├── configuration-flow.svg
│   └── administration-flow.svg
│
└── deployment/
    ├── deployment.svg
    └── deployment-multi-site.svg
```

---

# Diagrammes d'architecture

Les diagrammes contenus dans `architecture/` décrivent la structure générale de la plateforme.

| Diagramme                   | Description                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------- |
| `ecosystem.svg`             | Vue d'ensemble de l'écosystème Ohana et des relations entre les composants de la plateforme. |
| `platform-architecture.svg` | Architecture logique de la plateforme organisée en couches fonctionnelles.                    |
| `data-flow.svg`             | Vue synthétique du parcours des données à travers les principaux composants.                  |

---

# Diagrammes de flux

Les diagrammes contenus dans `flows/` illustrent les principaux échanges fonctionnels de la plateforme.

| Diagramme                 | Description                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `observation-flow.svg`    | Parcours complet d'une observation depuis une capacité jusqu'à sa visualisation.    |
| `event-flow.svg`          | Distribution des événements au sein du runtime.                                     |
| `health-flow.svg`         | Calcul et agrégation de la santé des capacités et de l'infrastructure.              |
| `timeline-flow.svg`       | Construction des périodes d'état à partir des observations successives.             |
| `visualization-flow.svg`  | Transformation des données techniques en représentations graphiques.                |
| `configuration-flow.svg`  | Application de la configuration déclarative au comportement de la plateforme.       |
| `administration-flow.svg` | Exécution des opérations d'administration et production des observations associées. |

---

# Diagrammes de déploiement

Les diagrammes contenus dans `deployment/` présentent les différents scénarios de déploiement de la plateforme.

| Diagramme                   | Description                                                               |
| --------------------------- | ------------------------------------------------------------------------- |
| `deployment.svg`            | Architecture de déploiement standard de la plateforme.                    |
| `deployment-multi-site.svg` | Extension de l'architecture vers un déploiement distribué ou multi-sites. |

---

# Conventions graphiques

Les diagrammes suivent les conventions de lisibilité du Design System Ohana.
La palette de l'interface Vision reste celle de ses tokens CSS ; certains SVG
historiques conservent leurs couleurs d'illustration et ne prescrivent pas les
valeurs à utiliser dans les composants de l'interface.

* Palette de couleurs officielle de la plateforme.
* Fond sombre Ohana.
* Accent turquoise pour les flux principaux et les composants mis en évidence.
* Gris bleuté pour les relations secondaires.
* Hiérarchie visuelle homogène entre tous les diagrammes.
* Typographie cohérente avec la charte graphique.
* Composants principaux identifiés par un contour accentué.
* Flèches orientées dans le sens des échanges.
* Format SVG autonome, sans dépendance externe.

---

## Sources et périmètre

La palette de l'interface est documentée dans [Colors](../docs/Design/Colors.md).
La vue [écosystème](architecture/ecosystem.svg) inclut les huit dépôts ;
[le flux d'administration](flows/administration-flow.svg) place la validation
et l'exécution dans Agent. Le répertoire canonique est `deployment/` ;
les copies identiques de l'ancien répertoire mal orthographié ont été retirées.
Le schéma multi-sites représente une extension prévue, pas un déploiement acquis.

# Maintenance

Les diagrammes sont versionnés avec la documentation de la plateforme.

Toute évolution de l'architecture, des flux ou des scénarios de déploiement doit être répercutée dans les diagrammes concernés afin de garantir leur cohérence avec les documents de référence.
