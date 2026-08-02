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
| 1.11.5 | 1.10.2 | 1.7.0 | 1.0.28 |
| 1.11.5 | 1.10.1 | 1.7.0 | 1.0.27 |
| 1.11.3 | 1.10.1 | 1.6.1 | 1.0.25 |
| 1.11.2 | 1.10.1 | 1.6.1 | 1.0.24 |
| 1.11.1 | 1.10.0 | 1.6.1 | 1.0.23 |
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

Ohana-Agent 1.11.1 supprime uniquement les anciens baux dnsmasq qui contredisent
une nouvelle réservation DHCP et normalise les listes DNS retournées par
NetworkManager.

Ohana-Agent 1.11.2 résout les noms d’hôte utilisés comme serveurs DNS explicites
avant de les transmettre à `dnspython`, tout en conservant leur nom dans les
observations.

Ohana-Agent 1.11.3 conserve la connexion MQTT Home Assistant lorsque seule
l’infrastructure change et publie un résumé de santé retenu. Les entités ne
passent plus artificiellement à `Indisponible` pendant une reconfiguration.

Ohana-Agent 1.11.4 exporte les suspensions planifiées avec l’état neutre
`unknown` et conserve l’API d’administration disponible hors plage horaire.

Ohana-Agent 1.11.5 conserve également le ciblage équipement lorsque le plugin
est suspendu, supprimant le second crash révélé en production par `SUN-01`.
