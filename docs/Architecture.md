# Architecture Ohana

Ce document sert de point d'entrée vers l'architecture officielle de la
plateforme.

- [Architecture générale](Architecture/Architecture.md)
- [Principes](Architecture/Principes.md)
- [Flux](Architecture/Flux.md)
- [Déploiement](Architecture/Déploiement.md)
- [Décisions d'architecture](<Architecture/adr/ADR-0000 - Architecture Decision Records.md>)

Les compositions installables sont listées dans
[`../release-catalog.yaml`](../release-catalog.yaml). La composition recommandée
et son contrat complet sont définis par
[`../release-manifest.yaml`](../release-manifest.yaml).


## Flux Téléinformation direct

`teleinfo2mqtt` conserve sa publication MQTT vers HA-Green et envoie en parallèle
la même trame décodée vers Ohana-Agent. Les deux sorties sont indépendantes. Le
récepteur Agent utilise un jeton dédié et ne partage pas le contrat
d’administration. Les plages horaires sont évaluées par Agent à partir des
métadonnées des équipements.
