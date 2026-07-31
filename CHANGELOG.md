# Changelog

Toutes les modifications notables apportées à Ohana Platform sont documentées dans ce fichier.

Le format s’inspire de Keep a Changelog et le projet suit une stratégie de versionnement sémantique.

## [Unreleased]

## [1.0.24] - 2026-07-31

### Corrigé

* Référencement d’Ohana-Agent 1.11.2, qui résout les noms d’hôte fournis comme
  serveurs DNS explicites avant de les transmettre à `dnspython`.

### Modifié

* La composition recommandée devient Ohana-Agent 1.11.2 et Ohana-Vision 1.10.1.
* Ohana-Vision distingue désormais le type Ethernet de sa capacité et anime les
  liaisons selon leur débit déclaré ou négocié, sans estimation de saturation.
* Platform 1.0.23 reste disponible avec le statut `supported`.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.24.
* Noms des wheels alignés sur les artefacts Agent 1.11.2 et Vision 1.10.1.

## [1.0.23] - 2026-07-31

### Corrigé

* Référencement d’Ohana-Agent 1.11.1, qui supprime les anciens baux dnsmasq
  incompatibles avec une nouvelle réservation DHCP.
* Lecture correcte des listes DNS NetworkManager et déploiement du helper DHCP
  privilégié restreint.

### Modifié

* La composition recommandée devient Ohana-Agent 1.11.1, Ohana-Vision 1.10.0
  et Ohana-Installer 1.6.1.
* Platform 1.0.22 reste disponible avec le statut `supported`.
* Le catalogue ne propose plus les versions Platform sans release GitHub
  téléchargeable (`1.0.15` et `1.0.19` à `1.0.21`).

### Validation

* Concordance du manifeste et du catalogue avec les copies embarquées dans
  Ohana-Installer 1.6.1.

## [1.0.22] - 2026-07-30

### Ajouté

* Catalogue `release-catalog.yaml` des couples Agent/Vision installables.
* Statuts `recommended`, `supported` et `legacy` pour les compositions publiées.
* Sélection par version Platform ou par couple Agent/Vision dans
  Ohana-Installer 1.5.0.

### Modifié

* La composition recommandée reste Ohana-Agent 1.11.0 et Ohana-Vision 1.10.0.
* Les releases Platform historiques deviennent sélectionnables sans nouvelle
  version de l’Installer.

### Validation

* Concordance stricte entre le catalogue, le manifeste 1.0.22 et les copies
  embarquées dans Ohana-Installer.

## [1.0.21] - 2026-07-30

### Ajouté

* Administration réseau sécurisée d’INFRA-01 : lecture NetworkManager,
  modification avec sauvegarde, confirmation et retour automatique.
* Provisionnement IPv4 initial par Ohana-Installer.
* Page Réseau Agent dans Ohana-Vision.

### Modifié

* Référencement d’Ohana-Agent 1.11.0, Ohana-Vision 1.10.0 et
  Ohana-Installer 1.0.13.

## [1.0.20] - 2026-07-30

### Ajouté

* Architecture Téléinformation directe : `teleinfo2mqtt` publie une trame HTTP
  vers Ohana-Agent en parallèle de son flux MQTT vers Home Assistant.
* Plages horaires de surveillance portées par les équipements et état
  `suspended` neutre pour la santé globale.
* Référence du fork `hassio-addons` Ohana permettant une installation propre de
  l’add-on modifié dans Home Assistant.

### Modifié

* Référencement d’Ohana-Agent 1.10.0, Ohana-Vision 1.9.0 et
  Ohana-Installer 1.0.12.

## [1.0.19] - 2026-07-30

### Changed

* Référencement d’Ohana-Agent 1.9.0, Ohana-Vision 1.8.0 et Ohana-Installer 1.0.11.
* Télémétrie Home Assistant générique, noms DNS et ports conditionnels.

## [1.0.18] - 2026-07-29

### Changed

* Alignement sur Ohana-Agent 1.8.1, Ohana-Vision 1.7.1 et
  Ohana-Installer 1.0.10.
* Vision valide désormais les noms DNS des réservations DHCP avant leur envoi
  à Agent et explique que les espaces et caractères `_` doivent être remplacés
  par des tirets.

## [1.0.17] - 2026-07-29

### Changed

* Alignement sur Ohana-Agent 1.8.1, Ohana-Vision 1.7.0 et
  Ohana-Installer 1.0.9.
* La composition Téléinformation applique désormais une fraîcheur contextuelle :
  `NTARF` et les index Tempo inactifs ne provoquent plus de fausse alerte.
* `SINSTS` et l’index désigné par le tarif courant restent les données
  effectivement surveillées.

## [1.0.16] - 2026-07-29

### Added

* Ajout du plugin Téléinformation Linky dans la composition officielle.
* Déploiement de `teleinformation.example.yaml` vers
  `/etc/ohana-agent/plugins/teleinformation.yaml`.
* Ajout de l’argument systemd `--teleinformation-config`.

### Changed

* Alignement sur Ohana-Agent 1.8.0, Ohana-Vision 1.7.0 et
  Ohana-Installer 1.0.8.
* Documentation commune complétée pour `SINSTS`, `NTARF` et les six index
  Tempo `EASF01` à `EASF06`.

## [1.0.15] - 2026-07-29

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.7.5 et Ohana-Vision 1.6.3.
* Correction du routage des tâches périodiques Shelly Telemetry : le plugin
  technique `shelly_telemetry` publie de nouveau la capacité
  `shelly.telemetry.freshness` vers Vision.
* Alignement documentaire sur Ohana-Installer 1.0.7.

## [1.0.14] - 2026-07-29

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.7.4 et Ohana-Vision 1.6.3.
* Correction de la replanification Shelly Telemetry et amélioration de la
  fluidité de l'interface Vision.

## [1.0.13] - 2026-07-28

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.7.3 et Ohana-Vision 1.6.2.

## [1.0.12] - 2026-07-28

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.7.2 et Ohana-Vision 1.6.1.

## [1.0.11] - 2026-07-28

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.7.1 et Ohana-Vision 1.6.0.

## [1.0.10] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.5.1 et Ohana-Vision 1.4.4.

## [1.0.9] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Vision 1.4.3.

## [1.0.8] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Vision 1.4.1.

## [1.0.7] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.5.0 et Ohana-Vision 1.4.0.

## [1.0.6] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.3.0 et Ohana-Vision 1.3.0.

## [1.0.5] - 2026-07-27

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.2.1 et
  Ohana-Vision 1.2.1.
* Suppression cohérente d’un équipement.
* Configuration de l’architecture.
* Carte Infrastructure.

## [1.0.4] - 2026-07-25

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.2.1 et
  Ohana-Vision 1.2.0.
* Découverte automatique de tous les services DNS déclarés dans
  l'infrastructure.
* Prise en compte dynamique de l'ajout, de la modification, de la
  désactivation et de la suppression d'un service DNS sans redémarrage
  d'Ohana-Agent.
* Association des observations DNS à l'identifiant exact de chaque service.

## [1.0.3] - 2026-07-24

### Added

* Administration graphique du DHCP et de l'architecture via le contrat local
  authentifié entre Vision et Agent.
* Cartographie sur grille, glisser-déposer des équipements, association des
  services et édition complète des liaisons.

### Changed

* Alignement de la plateforme sur Ohana-Agent 1.2.0 et Ohana-Vision 1.2.0.
* Préparation systemd de l'administration et du rechargement sécurisé de
  dnsmasq par Ohana-Installer 1.0.1.

## [1.0.2] - 2026-07-24

### Changed

* Alignement de la plateforme sur Ohana-Vision 1.1.2.
* Distribution du correctif des ressources graphiques et de l'accès à
  l'interface web depuis l'URL racine.

## [1.0.1] - 2026-07-24

### Changed

* Alignement de la plateforme 1.0.1 sur Ohana-Agent 1.1.1 et
  Ohana-Vision 1.1.1.
* Passage du runtime commun minimal à Python 3.13.
* Séparation des comptes systemd `ohana-agent` et `ohana-vision`.
* Correction des guides, des liens et de la matrice de compatibilité.

### Added

* Initialisation du dépôt Ohana-Platform.
* Création de la structure documentaire.
* Ajout du guide d’installation de la plateforme.
* Référencement d’Ohana-Agent et d’Ohana-Vision comme composants indépendants.

## [0.1.0] - 2026-07-15

### Added

* Création du dépôt d’orchestration et de documentation de la plateforme.
* Définition du périmètre d’Ohana-Platform.
* Ajout des documents initiaux :

  * `README.md` ;
  * `ROADMAP.md` ;
  * `CHANGELOG.md` ;
  * `docs/Architecture.md` ;
  * `docs/Installer-Ohana-Platform.md` ;
  * `docs/Operations.md` ;
  * `docs/Troubleshooting.md`.
