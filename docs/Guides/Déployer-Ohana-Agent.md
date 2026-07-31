# Déployer Ohana-Agent

Le déploiement de production d'Ohana-Agent est réalisé par **Ohana-Installer** à
partir du manifeste de la release Ohana-Platform.

## Installation recommandée

```bash
sudo ohana install
```

Pour une installation automatisée explicitement acceptée :

```bash
sudo ohana install --yes
```

La composition Platform 1.0.22 installe Ohana-Agent 1.11.0 sous
`/opt/ohana-agent`, déploie ses configurations sous `/etc/ohana-agent` et crée
`ohana-agent.service`.

## Vérification

```bash
sudo systemctl is-active ohana-agent.service
/opt/ohana-agent/venv/bin/ohana-agent --version
sudo journalctl -u ohana-agent.service -n 100 --no-pager
```

Résultats attendus : service `active` et version `ohana-agent 1.11.0`.

## Configuration

Agent reste propriétaire de la configuration déclarative de l'infrastructure.
Les fichiers principaux sont :

```text
/etc/ohana-agent/shikamaru.yaml
/etc/ohana-agent/infrastructure.yaml
/etc/ohana-agent/plugins/
```

Les modifications graphiques réalisées dans Vision passent par l'API
d'administration authentifiée d'Agent. Vision n'écrit jamais directement ces
fichiers.

## Mise à jour

```bash
sudo ohana update
```

Les configurations locales existantes sont conservées. Les fichiers manquants
et l'unité systemd sont réconciliés avec le manifeste courant.
