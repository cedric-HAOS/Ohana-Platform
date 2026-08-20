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
| 1.15.0 | 1.14.0 | 1.9.7 | 1.0.58 |
| 1.14.4 | 1.13.1 | 1.9.7 | 1.0.57 |
| 1.14.3 | 1.13.0 | 1.9.7 | 1.0.56 |
| 1.14.2 | 1.13.0 | 1.9.4 | 1.0.55 |
| 1.14.1 | 1.13.0 | 1.9.4 | 1.0.54 |
| 1.14.0 | 1.13.0 | 1.9.0 | 1.0.53 |
| 1.13.1 | 1.12.1 | 1.8.1 | 1.0.52 |
| 1.13.0 | 1.12.0 | 1.8.0 | 1.0.51 |
| 1.12.7 | 1.11.8 | 1.7.3 | 1.0.50 |
| 1.12.7 | 1.11.7 | 1.7.3 | 1.0.49 |
| 1.12.6 | 1.11.7 | 1.7.3 | 1.0.48 |
| 1.12.5 | 1.11.6 | 1.7.3 | 1.0.47 |
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

Sauvegardes, DHCP, DNS, NTP, MQTT, présence réseau, Z-Wave, WireGuard,
Télémétrie Home Assistant et Téléinformation.

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

Ohana-Agent 1.12.4 ajoute les sauvegardes HAOS chiffrées vers iCloud, sans
archive persistante sur INFRA-01, avec validation distante avant rotation et
diagnostic non destructif depuis Vision.

Ohana-Agent 1.12.5 remplace le proxy interne `/api/hassio/*` par l'API
WebSocket publique de Home Assistant, accepte la saisie masquée des secrets via
Vision et pilote la configuration rclone/iCloud sans exposer les identifiants
enregistrés.

Ohana-Agent 1.12.6 lance une cible HAOS précise en arrière-plan depuis l'API
d'administration, publie son état d'exécution et interdit une seconde
sauvegarde simultanée de la même cible.

Ohana-Agent 1.12.7 utilise la taille exacte de l'inventaire HAOS pour les
téléchargements segmentés sans `Content-Length`, sans relâcher le contrôle qui
interdit un flux réellement non borné.

Ohana-Agent 1.13.0 sauvegarde les configurations et un instantané cohérent de
la base Vision dans une archive `age` créée en RAM, publiée vers iCloud avec un
manifeste vérifié et une rétention distante désactivée par défaut.

Ohana-Agent 1.13.1 présente ce plugin commun sous le nom **Sauvegardes**, pour
refléter la protection des systèmes HAOS comme d'INFRA-01.

Ohana-Agent 1.14.0 utilise le destinataire public géré localement et envoie la
copie de récupération de l'identité `age` dans iCloud avant chaque sauvegarde
INFRA-01.

Ohana-Agent 1.14.1 lit la version de Vision depuis l'environnement Python dédié
de Vision afin que l'inventaire des sauvegardes INFRA-01 reste fiable.

Ohana-Agent 1.14.2 utilise l'API locale de Vision pour cet inventaire et
préserve ainsi les permissions privées de l'environnement Vision.

Ohana-Agent 1.14.3 compresse l'archive INFRA-01 avant son chiffrement, vérifie
la capacité minimale du tmpfs et remonte le diagnostic réel d'`age` lorsqu'un
pipe se ferme prématurément.

Ohana-Agent 1.14.4 ferme explicitement l'entrée standard d'`age` après la
création du tar compressé. Le chiffrement peut ainsi se terminer et l'état de
sauvegarde n'est plus bloqué indéfiniment.

Ohana-Agent 1.15.0 borne la file d'observations, enrichit les mesures de
ressources d'INFRA-01 et introduit le protocole optionnel de jobs Tsunade vers
Katsuyu avec `system.health` comme premier contrat strict et déterministe.
