# Installer et mettre à jour Ohana-Platform

La composition recommandée 1.0.26 installe Ohana-Agent 1.11.4 et
Ohana-Vision 1.10.1.

Ohana-Installer 1.7.0 lit le catalogue publié par Platform et peut installer
n’importe quel couple Agent/Vision qui y est déclaré.

## Lister les compositions disponibles

```bash
ohana versions
```

## Installation recommandée

```bash
sudo ohana install
```

## Installation d’une composition précise

Par version Platform :

```bash
sudo ohana install --platform-version 1.0.20
```

Par couple Agent/Vision :

```bash
sudo ohana install \
  --agent-version 1.10.0 \
  --vision-version 1.9.0
```

Un couple absent de `release-catalog.yaml` est refusé.

## Mise à jour d’une installation existante

```bash
sudo ohana update --yes
```

Pour appliquer volontairement une composition plus ancienne :

```bash
sudo ohana update \
  --platform-version 1.0.20 \
  --allow-downgrade
```

La rétrogradation n’efface pas les fichiers de configuration locaux. Une sauvegarde
est recommandée avant de revenir à une composition historique.

## Provisionnement réseau d’INFRA-01

Cette fonction est disponible avec les compositions intégrant Ohana-Agent
1.11.0 ou une version ultérieure.

```bash
sudo ohana install --yes \
  --network-interface eth0 \
  --network-address 192.168.1.10/24 \
  --network-gateway 192.168.1.1 \
  --network-dns 192.168.1.11 \
  --network-dns 192.168.1.12
```

Une fois installé, le réseau peut être consulté et modifié depuis Vision avec
un retour automatique si la nouvelle configuration n’est pas confirmée.
