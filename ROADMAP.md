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
* [x] Documenter la stratégie de sauvegarde HAOS et sa validation de restauration.

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

* [x] Ajouter une procédure de sauvegarde HAOS automatisée vers iCloud.
* [x] Ajouter une procédure de restauration complète.
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

## Version 1.0.69 — Expertise Tsunade et analyse IA avancée

**Statut : publiée.**

- [x] Exécuter les procédures et investigations déterministes avant tout LLM.
- [x] Limiter le contexte IA aux preuves utiles et bornées de l'incident.
- [x] Conserver les causes LLM comme hypothèses soumises à Tsunade.
- [x] Afficher diagnostics, hypothèses, confiance et preuves dans Vision.
- [x] Publier la composition Agent 1.22.0 / Vision 1.19.0, compatible avec
  Katsuyu 0.6.0.

## Version 1.0.64 — Appairage Katsuyu et jobs déterministes

**Statut : publiée.**

- [x] Publier les contrats Agent pour l'enregistrement et l'appairage Katsuyu.
- [x] Publier les handlers déterministes `system.health`, `backup.compress`,
  `backup.encrypt` et `backup.verify`.
- [x] Exposer dans Vision la validation des demandes d'appairage.
- [x] Publier la composition Agent 1.16.0 / Vision 1.15.0.

## Version 1.0.63 — Supervision Hôte stable en charge

**Statut : publiée.**

- [x] Servir la santé Hôte sans attendre le pool de threads d'ingestion.
- [x] Éviter le faux incident DHCP à l'arrêt de l'Agent.
- [x] Publier la composition Agent 1.15.2 / Vision 1.14.4.

## Version 1.0.62 — Catalogue stable après validation production

**Statut : publiée.**

- [x] Classer la composition régressive 1.0.60 comme historique.
- [x] Conserver Agent 1.15.1 / Vision 1.14.3 comme composition recommandée.

## Version 1.0.61 — Santé Hôte compacte complète

**Statut : publiée.**

- [x] Conserver les dernières capacités équipement dans l'état compact Vision.
- [x] Maintenir leur exclusion de la timeline de santé des services.
- [x] Publier la composition Agent 1.15.1 / Vision 1.14.3.

## Version 1.0.60 — Santé Hôte sans contention

**Statut : publiée.**

- [x] Lire `host.health` depuis l'état compact du processeur Vision.
- [x] Éviter le verrou SQLite lors du rafraîchissement de la page Hôte.
- [x] Publier la composition Agent 1.15.1 / Vision 1.14.2.

## Version 1.0.59 — Supervision fraîche et premier worker Katsuyu

**Statut : publiée.**

- [x] Rendre le rattrapage de la file Vision non bloquant pour Agent.
- [x] Réutiliser un processeur Vision persistant et indexer `host.health`.
- [x] Ajouter le worker Katsuyu `system.health` dans le dépôt Agent.
- [x] Publier la composition Agent 1.15.1 / Vision 1.14.1.
- [x] Ne pas lancer de sauvegarde réelle avant son orchestration par Katsuyu.

## Version 1.0.58 — Protection INFRA-01 et jobs distribués

**Statut : publiée.**

- [x] Supprimer le chargement intégral de SQLite dans Vision.
- [x] Borner, indexer et paginer les requêtes historiques.
- [x] Ajouter la rétention, la purge et l'instrumentation runtime.
- [x] Protéger les files d'observations et la sauvegarde INFRA-01.
- [x] Introduire le protocole de jobs et le contrat `system.health`.
- [x] Publier la composition Agent 1.15.0 / Vision 1.14.0.

## Version 1.0.57 — Sauvegarde INFRA-01 terminable et carte stable

**Statut : publiée.**

- [x] Fermer le flux envoyé à `age` avant d'attendre la fin du processus.
- [x] Libérer l'état **Backup in progress** après le chiffrement.
- [x] Stabiliser l'action de sauvegarde pendant les rafraîchissements temps réel.
- [x] Éviter le décalage de la fiche équipement sur mobile.
- [x] Publier la composition Agent 1.14.4 / Vision 1.13.1.

## Version 1.0.56 — Archive INFRA-01 adaptée au tmpfs

**Statut : publiée.**

- [x] Compresser le tar avant son chiffrement avec `age`.
- [x] Vérifier la capacité minimale du tmpfs avant l'instantané Vision.
- [x] Remonter le diagnostic réel d'`age` au lieu de `Broken pipe`.
- [x] Restaurer les tar compressés et non compressés.
- [x] Publier la composition Agent 1.14.3 / Vision 1.13.0.

## Version 1.0.55 — Inventaire Vision par API locale

**Statut : publiée.**

- [x] Lire la version de Vision via son API locale publique.
- [x] Préserver les permissions privées de l'environnement Vision.
- [x] Publier la composition Agent 1.14.2 / Vision 1.13.0.

## Version 1.0.54 — Inventaire Vision fiable pour les sauvegardes

**Statut : publiée.**

- [x] Lire la version de Vision depuis son environnement Python dédié.
- [x] Empêcher l'échec d'inventaire des sauvegardes INFRA-01.
- [x] Publier la composition Agent 1.14.1 / Vision 1.13.0.

## Version 1.0.53 — Identité age gérée et restauration autonome

**Statut : publiée.**

- [x] Créer et valider automatiquement l'identité `age` d'INFRA-01.
- [x] Conserver sa copie de récupération dans iCloud.
- [x] Migrer `backup.yaml` sans perdre les réglages existants.
- [x] Récupérer l'identité avant le déchiffrement d'une restauration iCloud.
- [x] Limiter le menu aux neuf compositions antérieures supportées.

## Version 1.0.52 — Sauvegardes et clé age explicites

**Statut : publiée.**

- [x] Présenter le plugin commun sous le nom **Sauvegardes**.
- [x] Documenter la génération Windows du destinataire public `age`.
- [x] Rappeler que l'identité privée reste hors d'INFRA-01.
- [x] Afficher l'installation ou la présence de `age` dans Ohana-Installer.

## Version 1.0.51 — Sauvegarde et restauration d'INFRA-01

**Statut : publiée.**

- [x] Déclarer dnsmasq, Chrony et age dans le profil INFRA-01.
- [x] Sauvegarder les configurations et la base Vision vers iCloud.
- [x] Restaurer depuis iCloud ou une copie locale en `tmpfs`.
- [x] Lier le manifeste public au descripteur inclus dans l'archive chiffrée.
- [x] Conserver le DHCP inactif jusqu'à sa mise en production explicite.

## Version 1.0.50 — Topologie stable et préparation Z-Wave fiable

**Statut : publiée.**

- [x] Actualiser santé et présence sans reconstruire la carte.
- [x] Synchroniser libellés, indicateurs, liaisons et accessibilité.
- [x] Conserver vide l'action préparatoire ZWAVE-01 lorsqu'elle est supprimée.
- [x] Recommander la planification NVM native de Z-Wave JS UI.

## Version 1.0.49 — Streaming HAOS segmenté

**Statut : publiée.**

- [x] Accepter l'absence de `Content-Length` pour le téléchargement HAOS.
- [x] Utiliser la taille exacte publiée par `backup/info`.
- [x] Refuser tout flux qui reste réellement non borné.
- [x] Conserver le streaming sans archive persistante sur INFRA-01.

## Version 1.0.48 — Sauvegarde HAOS immédiate par équipement

**Statut : publiée.**

- [x] Déclencher la cible HAOS correspondant exactement à l'équipement.
- [x] Exécuter la sauvegarde en arrière-plan sans bloquer Vision.
- [x] Remplacer l'action par **Backup in progress** pendant l'exécution.
- [x] Tolérer le démarrage à froid de rclone pour iCloud et le test.

## Version 1.0.47 — Application fiable des sauvegardes HAOS

**Statut : publiée.**

- [x] Ne pas soumettre les champs Apple à la validation du formulaire HAOS.
- [x] Valider les identifiants Apple uniquement pendant la connexion iCloud.
- [x] Signaler les modifications non appliquées avant un test.
- [x] Conserver Agent 1.12.5 et Installer 1.7.3.

## Version 1.0.46 — Ergonomie des sauvegardes HAOS

**Statut : publiée.**

- [x] Distinguer clairement la clé de chiffrement du jeton Home Assistant.
- [x] Indiquer l'emplacement de la clé dans l'interface Home Assistant.
- [x] Préserver le formulaire HAOS pendant la connexion iCloud et le 2FA.
- [x] Replier les identifiants Apple après configuration.

## Version 1.0.45 — Secrets HAOS et connexion iCloud

**Statut : publiée.**

- [x] Saisir les secrets HAOS dans Vision sans les relire depuis Agent.
- [x] Connecter et renouveler iCloud avec le flux 2FA rclone.
- [x] Installer automatiquement une version vérifiée de rclone.
- [x] Utiliser les API publiques de sauvegarde Home Assistant.

## Version 1.0.44 — Sauvegardes HAOS vers iCloud

- [x] Référencer Ohana-Agent 1.12.4 et Ohana-Vision 1.11.3.
- [x] Distribuer `backup.example.yaml` et l'argument `--backup-config`.
- [x] Conserver les secrets hors YAML et hors de Vision.
- [x] Documenter la validation progressive et la restauration.

## Version 1.0.20 — Lot B

- [x] Ohana-Agent 1.10.0 ;
- [x] Ohana-Vision 1.9.0 ;
- [x] Ohana-Installer 1.0.12 ;
- [x] Téléinformation HTTP directe depuis RPI-Linky ;
- [x] plages horaires et état de surveillance suspendu ;
- [x] fork Home Assistant installable et image multiarchitecture.


## Version 1.0.28 — Cohérence de la santé des services

- [x] Référencer Ohana-Agent 1.11.5 et Ohana-Vision 1.10.2.
- [x] Utiliser la timeline dans la carte des services comme dans la fiche.
- [x] Conserver les capacités absentes des 100 observations récentes.
- [x] Conserver Platform 1.0.27 comme composition supportée.


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
