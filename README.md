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
Ohana-Installer reads the Ohana-Platform release manifest
```

## Shared contracts

- Agent publishes observations to `POST /api/observations`.
- Agent synchronizes topology through `PUT /api/infrastructure`.
- Vision listens on `127.0.0.1:8000` by default.
- `release-manifest.yaml` is the platform release source of truth.
- Each Platform release publishes `release-manifest.yaml` as a GitHub release asset.
- Component releases publish every wheel and configuration file declared by the manifest.
- `Ohana-Installer/config/release-manifest.yaml` is the synchronized validation
  copy used by Installer tests and must remain identical to the platform manifest.

## Documentation

| Document | Description |
| --- | --- |
| [Architecture](docs/Architecture/Architecture.md) | Global platform architecture |
| [Development installation](docs/getting-started/Installer-Ohana-Platform.md) | Local Agent + Vision setup |
| [Operations](docs/Architecture/Déploiement.md) | Deployment architecture |
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
└── release-manifest.yaml
```

## Version compatibility

| Platform | Agent | Vision | Python | Target |
| --- | --- | --- | --- | --- |
| 1.0.7 | 1.4.0 | 1.4.0 | 3.13+ | Linux/systemd |
| 1.0.6 | 1.3.0 | 1.3.0 | 3.13+ | Linux/systemd |
| 1.0.5 | 1.2.1 | 1.2.1 | 3.13+ | Linux/systemd |
| 1.0.4 | 1.2.1 | 1.2.0 | 3.13+ | Linux/systemd |
| 1.0.3 | 1.2.0 | 1.2.0 | 3.13+ | Linux/systemd |
| 1.0.2 | 1.1.1 | 1.1.2 | 3.13+ | Linux/systemd |
| 1.0.1 | 1.1.1 | 1.1.1 | 3.13+ | Linux/systemd |

The exact installable versions and artifact names are defined in
`release-manifest.yaml`.

## Contributing

The platform is currently maintained as the reference implementation of the
Ohana ecosystem. Component-specific changes belong in the corresponding
repository; shared contracts and release coordination belong here.

## License

Distributed under the MIT license. See `LICENSE`.
