# Déployer Ohana-Vision

Le déploiement de production d'Ohana-Vision est réalisé par
**Ohana-Installer** avec la même composition que l'Agent.

## Installation recommandée

```bash
sudo ohana install
```

La composition sélectionnée dans le catalogue installe Ohana-Vision sous
`/opt/ohana-vision`, déploie sa configuration sous `/etc/ohana-vision` et crée
`ohana-vision.service`.

## Vérification

```bash
sudo systemctl is-active ohana-vision.service
/opt/ohana-vision/venv/bin/ohana-vision --version
sudo journalctl -u ohana-vision.service -n 100 --no-pager
```

Résultats attendus : service `active` et version correspondant au manifeste
de la composition choisie. Consulter [le guide nominal](../Installer-Ohana-Platform.md)
et [le catalogue](../../release-catalog.yaml) avant de comparer les versions.
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
