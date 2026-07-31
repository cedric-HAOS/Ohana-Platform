# Ohana-Agent

Ohana-Agent est le moteur d'observation et la source de vérité de
l'infrastructure déclarative Ohana.

## Responsabilités

- charger et valider `infrastructure.yaml` ;
- exécuter les plugins d'observation ;
- produire et exporter les observations ;
- synchroniser l'infrastructure vers Vision ;
- exposer l'API d'administration authentifiée ;
- appliquer de manière atomique les configurations administrées.

Agent ne contient aucune interface de visualisation.

## Version de la composition courante

| Agent | Vision | Installer | Platform |
|---|---|---|---|
| 1.11.0 | 1.10.0 | 1.5.0 | 1.0.22 |
| 1.11.0 | 1.10.0 | 1.0.13 | 1.0.21 |
| 1.10.0 | 1.9.0 | 1.0.12 | 1.0.20 |
| 1.9.0 | 1.8.0 | 1.0.11 | 1.0.19 |
| 1.8.1 | 1.7.1 | 1.0.10 | 1.0.18 |

## Plugins de la composition courante

DHCP, DNS, NTP, MQTT, présence réseau, Z-Wave, WireGuard, Télémétrie Home Assistant et Téléinformation.

Voir également [le guide de déploiement](../Guides/Déployer-Ohana-Agent.md).


## Téléinformation Linky

Ohana-Agent 1.9.0 contrôle la fraîcheur des données Linky publiées par
`teleinfo2mqtt` vers Home Assistant et expose la capacité
`teleinformation.freshness`, avec interprétation des six périodes Tempo.


Ohana-Agent 1.10.0 reçoit les trames Linky directement depuis
`teleinfo2mqtt` sur une API HTTP dédiée. Le flux ne dépend ni de l’API Home
Assistant ni du broker MQTT de HA-Green. La version introduit également les
plages horaires d’équipements et l’état `suspended`.


Ohana-Agent 1.11.0 expose l’état NetworkManager de l’hôte et applique une
configuration IPv4 via un helper privilégié limité, avec sauvegarde,
confirmation et restauration automatique.
