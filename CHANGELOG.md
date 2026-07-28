# Changelog

Toutes les modifications notables apportées à Ohana Platform sont documentées dans ce fichier.

Le format s’inspire de Keep a Changelog et le projet suit une stratégie de versionnement sémantique.

## [Unreleased]

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
