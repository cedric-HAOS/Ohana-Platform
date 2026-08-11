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

## Flux des sauvegardes HAOS

Vision administre la politique de sauvegarde à travers l'API locale d'Agent,
sans lire les secrets. Agent appelle le proxy Supervisor de chaque HAOS, puis
transmet le flux chiffré directement à rclone. Seuls les tampons rclone placés
sur `tmpfs` résident sur INFRA-01. La rotation locale intervient après
validation de la taille distante et du SHA-256.

Voir le guide [Sauvegarder les HAOS vers iCloud](Guides/Sauvegarder-HAOS-vers-iCloud.md).


## Flux Téléinformation direct

`teleinfo2mqtt` conserve sa publication MQTT vers HA-Green et envoie en parallèle
la même trame décodée vers Ohana-Agent. Les deux sorties sont indépendantes. Le
récepteur Agent utilise un jeton dédié et ne partage pas le contrat
d’administration. Les plages horaires sont évaluées par Agent à partir des
métadonnées des équipements.
