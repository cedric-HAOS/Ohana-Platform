# Déployer Ohana-Vision

Le déploiement de production d'Ohana-Vision est réalisé par
**Ohana-Installer** avec la même composition que l'Agent.

## Installation recommandée

```bash
sudo ohana install
```

La composition Platform 1.0.59 installe Ohana-Vision 1.14.1 sous
`/opt/ohana-vision`, déploie sa configuration sous `/etc/ohana-vision` et crée
`ohana-vision.service`.

## Vérification

```bash
sudo systemctl is-active ohana-vision.service
/opt/ohana-vision/venv/bin/ohana-vision --version
sudo journalctl -u ohana-vision.service -n 100 --no-pager
```

Résultats attendus : service `active` et version `ohana-vision 1.14.1`.
L'interface est disponible par défaut sur :

```text
http://ADRESSE_DU_SERVEUR:8000
```

## Relation avec Agent

Vision reçoit les observations et la topologie par REST. Pour l'administration,
son backend appelle l'API locale d'Agent avec le secret partagé préparé par
Installer. Agent reste responsable de la validation et de la persistance.

## Mise à jour

```bash
sudo ohana update
```
