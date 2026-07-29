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
| 1.8.0 | 1.7.0 | 1.0.8 | 1.0.16 |

## Plugins de la composition courante

DHCP, DNS, NTP, MQTT, présence réseau, Z-Wave, WireGuard, Shelly Telemetry et Téléinformation.

Voir également [le guide de déploiement](../Guides/Déployer-Ohana-Agent.md).


## Téléinformation Linky

Ohana-Agent 1.8.0 contrôle la fraîcheur des données Linky publiées par
`teleinfo2mqtt` vers Home Assistant et expose la capacité
`teleinformation.freshness`, avec interprétation des six périodes Tempo.
