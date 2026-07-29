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
| 1.7.4 | 1.6.3 | 1.0.6 | 1.0.14 |

## Plugins de la composition courante

DHCP, DNS, NTP, MQTT, présence réseau, Z-Wave, WireGuard et Shelly Telemetry.

Voir également [le guide de déploiement](../Guides/Déployer-Ohana-Agent.md).
