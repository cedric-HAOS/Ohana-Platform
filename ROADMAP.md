# Roadmap

## Vision

Ohana-Platform constitue le point d’entrée officiel de l’écosystème Ohana.

Le dépôt rassemble la documentation globale, les procédures de déploiement, les outils d’orchestration et les exemples permettant d’installer et d’exploiter Ohana-Agent et Ohana-Vision comme une plateforme cohérente.

---

## Phase 0 — Fondation du dépôt

* [x] Création du dépôt Ohana-Platform.
* [x] Définition de son périmètre.
* [x] Création de l’arborescence documentaire.
* [x] Ajout du README.
* [x] Ajout du CHANGELOG.
* [x] Ajout de la roadmap.
* [x] Ajout de la licence.
* [x] Premier audit transversal de l'écosystème.

---

## Phase 1 — Documentation de la plateforme

* [x] Finaliser la documentation d'architecture.
* [x] Finaliser `docs/Installer-Ohana-Platform.md`.
* [x] Rédiger `docs/Operations.md`.
* [ ] Rédiger `docs/Troubleshooting.md`.
* [x] Ajouter une matrice de compatibilité Agent/Vision.
* [ ] Documenter les ports et flux réseau.
* [ ] Documenter les stratégies de sauvegarde et de restauration.

---

## Phase 2 — Déploiement reproductible

* [x] Ajouter l'installation Linux via Ohana-Installer.
* [ ] Ajouter des scripts d’installation Windows.
* [x] Générer les unités `systemd` via Ohana-Installer.
* [ ] Ajouter les modèles de services Windows.
* [x] Distribuer les fichiers de configuration d’exemple dans les releases.
* [x] Ajouter les vérifications post-installation dans Ohana-Installer.
* [x] Ajouter la désinstallation dans Ohana-Installer.

---

## Phase 3 — Orchestration

* [ ] Étudier Docker Compose.
* [ ] Séparer les volumes de configuration et de données.
* [ ] Ajouter les contrôles de santé.
* [ ] Ajouter la gestion des secrets.
* [ ] Ajouter un reverse proxy optionnel.
* [ ] Ajouter le support HTTPS.
* [ ] Préparer les procédures de mise à jour et de rollback.

---

## Phase 4 — Exploitation

* [ ] Ajouter une procédure de sauvegarde automatisée.
* [ ] Ajouter une procédure de restauration complète.
* [ ] Ajouter la rotation des journaux.
* [ ] Ajouter la supervision d’Ohana par Ohana.
* [ ] Ajouter les diagnostics automatisés.
* [ ] Documenter la maintenance préventive.

---

## Phase 5 — Distribution de la plateforme

* [x] Publier des releases cohérentes de la plateforme.
* [x] Associer les versions compatibles d’Ohana-Agent et d’Ohana-Vision.
* [x] Fournir des sommes de contrôle pour les releases des composants.
* [ ] Fournir des archives de déploiement.
* [x] Ajouter un manifeste de plateforme.
* [x] Fournir un installateur unifié avec Ohana-Installer.

---

## Évolutions futures

* authentification ;
* gestion multi-utilisateur ;
* stockage persistant ;
* notifications ;
* gestion des incidents ;
* haute disponibilité ;
* déploiements distribués ;
* catalogue de plugins ;
* SDK Ohana.

## Version 1.0.20 — Lot B

- [x] Ohana-Agent 1.10.0 ;
- [x] Ohana-Vision 1.9.0 ;
- [x] Ohana-Installer 1.0.12 ;
- [x] Téléinformation HTTP directe depuis RPI-Linky ;
- [x] plages horaires et état de surveillance suspendu ;
- [x] fork Home Assistant installable et image multiarchitecture.


## Version 1.0.27 — Routage des suspensions d’équipements

- [x] Référencer Ohana-Agent 1.11.5 et Ohana-Vision 1.10.1.
- [x] Conserver le ciblage `device` lors des suspensions planifiées.
- [x] Reproduire le second défaut observé sur Infra-01 après 1.0.26.
- [x] Retirer Platform 1.0.26 du catalogue sélectionnable.


## Version 1.0.26 — Stabilité des surveillances planifiées

- [x] Référencer Ohana-Agent 1.11.4 et Ohana-Vision 1.10.1.
- [x] Exporter les suspensions planifiées sans interrompre Agent.
- [x] Conserver leurs métadonnées explicatives dans Vision.
- [x] Conserver Platform 1.0.25 comme composition supportée.


## Version 1.0.25 — Stabilité MQTT Home Assistant

- [x] Référencer Ohana-Agent 1.11.3 et Ohana-Vision 1.10.1.
- [x] Supprimer les faux états `Indisponible` lors des reconfigurations.
- [x] Publier le résumé de santé MQTT avec rétention.
- [x] Conserver Platform 1.0.24 comme composition supportée.


## Version 1.0.24 — Lecture des capacités réseau

- [x] Référencer Ohana-Agent 1.11.2 et Ohana-Vision 1.10.1.
- [x] Distinguer le type Ethernet de sa capacité dans Vision.
- [x] Représenter la capacité sans estimation de trafic ou de saturation.
- [x] Conserver Platform 1.0.23 comme composition supportée.


## Version 1.0.23 — Fiabilité DHCP

- [x] Référencer Ohana-Agent 1.11.1 et Ohana-Vision 1.10.0.
- [x] Déployer le helper de purge ciblée avec Ohana-Installer 1.6.1.
- [x] Conserver Platform 1.0.22 comme composition supportée.
- [x] Publier le manifeste et le catalogue coordonnés.

## Version 1.0.22 — Catalogue de compositions

- [x] Publier `release-catalog.yaml` dans la release Platform.
- [x] Référencer les compositions validées de Platform 1.0.13 à 1.0.22.
- [x] Définir une composition recommandée unique.
- [x] Permettre à Ohana-Installer 1.5.0 de sélectionner une version historique.
- [x] Maintenir le manifeste 1.0.22 sur Agent 1.11.0 et Vision 1.10.0.

## Version 1.0.21 — Lot C

- [x] Ohana-Agent 1.11.0 ;
- [x] Ohana-Vision 1.10.0 ;
- [x] Ohana-Installer 1.0.13 ;
- [x] administration réseau sécurisée et provisionnement initial.
