# Ohana Platform

> A modular infrastructure supervision platform built around observation,
> health monitoring and real-time visualization.

Ohana separates collection, visualization and deployment into independent
components connected by explicit contracts.

## Ecosystem

| Repository | Responsibility |
| --- | --- |
| [Ohana-Agent](https://github.com/cedric-HAOS/Ohana-Agent) | Collects observations and owns the declarative infrastructure topology. |
| [Ohana-Vision](https://github.com/cedric-HAOS/Ohana-Vision) | Ingests observations and displays health, history and topology. |
| [Ohana-Installer](https://github.com/cedric-HAOS/Ohana-Installer) | Installs, updates and removes the released platform on Linux/systemd. |
| [Ohana-House](https://github.com/cedric-HAOS/Ohana-House) | Documents the reference home deployment. |
| **Ohana-Platform** | Defines the shared architecture, documentation, design system and release manifest. |

```text
Infrastructure
      |
      v
Ohana-Agent -- REST --> Ohana-Vision --> Web dashboard
      ^
      |
Ohana-Installer reads the Ohana-Platform release catalog
```

## Shared contracts

- Agent publishes observations to `POST /api/observations`.
- Agent synchronizes topology through `PUT /api/infrastructure`.
- Vision listens on `127.0.0.1:8000` by default.
- `release-catalog.yaml` lists every officially installable Agent/Vision couple.
- `release-manifest.yaml` is the immutable contract of one Platform release.
- Each Platform release publishes both files as GitHub release assets.
- Component releases publish every wheel and configuration file declared by the manifest.
- `Ohana-Installer/config/release-catalog.yaml` and
  `Ohana-Installer/config/release-manifest.yaml` are synchronized validation copies.

## Documentation

| Document | Description |
| --- | --- |
| [Architecture](docs/Architecture/Architecture.md) | Global platform architecture |
| [Development installation](docs/getting-started/Installer-Ohana-Platform.md) | Local Agent + Vision setup |
| [Operations](docs/Architecture/Déploiement.md) | Deployment architecture |
| [Sauvegardes HAOS vers iCloud](docs/Guides/Sauvegarder-HAOS-vers-iCloud.md) | Configuration, sécurité et validation des sauvegardes |
| [Design system](docs/Design/Brand.md) | Shared visual identity |

## Getting started

For a development environment, follow
[the complete installation guide](docs/getting-started/Installer-Ohana-Platform.md).
Production installation is handled by Ohana-Installer from official GitHub
releases.

## Repository structure

```text
Ohana-Platform/
├── diagrams/
├── docs/
├── CHANGELOG.md
├── LICENSE
├── README.md
├── ROADMAP.md
├── release-catalog.yaml
└── release-manifest.yaml
```

## Version compatibility

| Platform | Agent | Vision | Python | Target |
| --- | --- | --- | --- | --- |
| 1.0.44 | 1.12.4 | 1.11.3 | 3.13+ | Linux/systemd |
| 1.0.43 | 1.12.3 | 1.11.2 | 3.13+ | Linux/systemd |
| 1.0.42 | 1.12.3 | 1.11.1 | 3.13+ | Linux/systemd |
| 1.0.41 | 1.12.2 | 1.11.0 | 3.13+ | Linux/systemd |
| 1.0.40 | 1.12.1 | 1.11.0 | 3.13+ | Linux/systemd |
| 1.0.33 | 1.11.8 | 1.10.7 | 3.13+ | Linux/systemd |
| 1.0.32 | 1.11.7 | 1.10.6 | 3.13+ | Linux/systemd |
| 1.0.31 | 1.11.7 | 1.10.5 | 3.13+ | Linux/systemd |
| 1.0.30 | 1.11.7 | 1.10.4 | 3.13+ | Linux/systemd |
| 1.0.29 | 1.11.6 | 1.10.3 | 3.13+ | Linux/systemd |
| 1.0.28 | 1.11.5 | 1.10.2 | 3.13+ | Linux/systemd |
| 1.0.27 | 1.11.5 | 1.10.1 | 3.13+ | Linux/systemd |
| 1.0.25 | 1.11.3 | 1.10.1 | 3.13+ | Linux/systemd |
| 1.0.24 | 1.11.2 | 1.10.1 | 3.13+ | Linux/systemd |
| 1.0.39 | 1.12.0 | 1.11.0 | 3.13+ | Linux/systemd |
| 1.0.38 | 1.11.11 | 1.10.9 | 3.13+ | Linux/systemd |
| 1.0.23 | 1.11.1 | 1.10.0 | 3.13+ | Linux/systemd |
| 1.0.22 | 1.11.0 | 1.10.0 | 3.13+ | Linux/systemd |
| 1.0.21 | 1.11.0 | 1.10.0 | 3.13+ | Linux/systemd |
| 1.0.20 | 1.10.0 | 1.9.0 | 3.13+ | Linux/systemd |
| 1.0.19 | 1.9.0 | 1.8.0 | 3.13+ | Linux/systemd |
| 1.0.18 | 1.8.1 | 1.7.1 | 3.13+ | Linux/systemd |
| 1.0.17 | 1.8.1 | 1.7.0 | 3.13+ | Linux/systemd |
| 1.0.16 | 1.8.0 | 1.7.0 | 3.13+ | Linux/systemd |
| 1.0.15 | 1.7.5 | 1.6.3 | 3.13+ | Linux/systemd |
| 1.0.14 | 1.7.4 | 1.6.3 | 3.13+ | Linux/systemd |
| 1.0.13 | 1.7.3 | 1.6.2 | 3.13+ | Linux/systemd |
| 1.0.12 | 1.7.2 | 1.6.1 | 3.13+ | Linux/systemd |
| 1.0.11 | 1.7.1 | 1.6.0 | 3.13+ | Linux/systemd |
| 1.0.10 | 1.5.1 | 1.4.4 | 3.13+ | Linux/systemd |
| 1.0.9 | 1.5.0 | 1.4.3 | 3.13+ | Linux/systemd |
| 1.0.8 | 1.5.0 | 1.4.1 | 3.13+ | Linux/systemd |
| 1.0.7 | 1.5.0 | 1.4.0 | 3.13+ | Linux/systemd |
| 1.0.6 | 1.3.0 | 1.3.0 | 3.13+ | Linux/systemd |
| 1.0.5 | 1.2.1 | 1.2.1 | 3.13+ | Linux/systemd |
| 1.0.4 | 1.2.1 | 1.2.0 | 3.13+ | Linux/systemd |
| 1.0.3 | 1.2.0 | 1.2.0 | 3.13+ | Linux/systemd |
| 1.0.2 | 1.1.1 | 1.1.2 | 3.13+ | Linux/systemd |
| 1.0.1 | 1.1.1 | 1.1.1 | 3.13+ | Linux/systemd |

The complete list of selectable compositions is defined in
`release-catalog.yaml`. The exact artifact names and service contracts of each
composition remain defined by the `release-manifest.yaml` published in its Platform
release.

## Contributing

The platform is currently maintained as the reference implementation of the
Ohana ecosystem. Component-specific changes belong in the corresponding
repository; shared contracts and release coordination belong here.

## License

Distributed under the MIT license. See `LICENSE`.

## Composition 1.0.44

Cette composition ajoute les sauvegardes complètes et chiffrées de HA-01,
LINKY-01 et ZWAVE-01 vers iCloud. Agent diffuse les archives sans stockage
persistant sur INFRA-01 et Vision configure les cibles, leurs adresses et leurs
heures quotidiennes sans recevoir les secrets.

## Composition 1.0.33

Cette composition distingue les nœuds découverts avec le type « Module
Z-Wave » et une icône radio dédiée. Les cartes compactes contiennent leurs
libellés et les liaisons d’une même passerelle partagent des troncs plus
discrets pour réduire l’enchevêtrement visuel.

## Composition 1.0.32

Cette composition signale dans Architecture les équipements Z-Wave découverts
restant à positionner. Leur placement automatique est explicitement demandé,
prévisualisé dans le brouillon puis persisté uniquement avec « Appliquer
l’architecture ».

## Composition 1.0.31

Cette composition corrige le rendu de la topologie lorsqu’un même équipement,
notamment la passerelle Z-Wave, porte plusieurs liaisons. Elle conserve la
découverte automatique et l’état vivant des nœuds fournis par Agent 1.11.7.

## Composition 1.0.30

Cette composition ajoute la découverte automatique des nœuds Z-Wave JS et
leur état vivant dans la carte d’infrastructure. Les équipements radio sont
compacts, les groupes Wi-Fi et Z-Wave peuvent être repliés indépendamment et
le maillage Z-Wave entre équipements n’est pas reproduit.

## Composition 1.0.29

Cette composition resynchronise immédiatement la carte avec les observations,
reconstruit correctement les timelines bornées par plage horaire et unifie
l’identifiant des capacités de télémétrie Home Assistant suspendues.

## Composition 1.0.28

Cette composition aligne la carte des services sur la timeline déjà utilisée
par les fiches équipement. Un service conserve ainsi le même dernier état
connu dans les deux vues, même si son observation n'est plus dans les 100 plus
récentes.

## Composition 1.0.27

Cette composition stabilise complètement les surveillances planifiées. Une
observation suspendue hors plage conserve son ciblage équipement et est exportée
avec l’état neutre `unknown`, sans interrompre Agent ni son API d’administration.

## Composition 1.0.22

Cette composition introduit le catalogue officiel des couples Agent/Vision.
Ohana-Installer 1.5.0 peut lister les compositions, sélectionner une version
Platform ou retrouver une composition à partir des versions Agent et Vision.
L’ajout d’un couple dans une future release Platform ne demande plus de modifier
le code de l’Installer.

## Composition 1.0.21

Cette composition ajoute l’administration réseau sécurisée d’INFRA-01 :
Ohana-Installer provisionne l’adresse initiale et prépare le helper limité,
Ohana-Agent applique les changements avec rollback automatique, et
Ohana-Vision fournit la page de consultation, confirmation et restauration.

## Composition 1.0.20

Cette composition ajoute la réception directe des trames Linky depuis le fork
`teleinfo2mqtt Ohana` et les plages horaires de surveillance des équipements.
Le flux MQTT vers Home Assistant reste indépendant du flux HTTP vers Agent.
