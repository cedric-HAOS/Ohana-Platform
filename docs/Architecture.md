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

Vision administre la politique, la saisie masquée des secrets et le flux 2FA
iCloud à travers l'API locale d'Agent, sans jamais relire les valeurs
enregistrées. Agent utilise l'API WebSocket publique de Home Assistant et la
route publique de téléchargement, puis transmet le flux chiffré directement à
rclone. Seuls les tampons rclone placés sur `tmpfs` résident sur INFRA-01. La
rotation locale intervient après validation de la taille distante et du
SHA-256.

Voir le guide [Sauvegarder les HAOS vers iCloud](Guides/Sauvegarder-HAOS-vers-iCloud.md).

## Flux Katsuyu sur le LAN

L'administration Agent/Vision reste confinée à `127.0.0.1:8765`. Agent expose
séparément un listener HTTPS limité aux routes worker Katsuyu. L'Installer
provisionne une autorité locale, conserve sa clé privée sous `root`, donne à
Agent uniquement le certificat serveur et sa clé de service, puis active les
jobs distribués. Lors de l'appairage, Vision et Katsuyu affichent le même code
court et la même empreinte SHA-256 complète. Après cette validation humaine,
Katsuyu épingle l'autorité publique et le jeton worker circule uniquement dans
le canal HTTPS vérifié.

Ce flux étend les contrats Agent existants. Il n'ajoute ni reverse proxy, ni
bus, ni système d'authentification parallèle. Le listener worker ne doit pas
être publié directement sur Internet.


## Flux Téléinformation direct

`teleinfo2mqtt` conserve sa publication MQTT vers HA-Green et envoie en parallèle
la même trame décodée vers Ohana-Agent. Les deux sorties sont indépendantes. Le
récepteur Agent utilise un jeton dédié et ne partage pas le contrat
d’administration. Les plages horaires sont évaluées par Agent à partir des
métadonnées des équipements.
