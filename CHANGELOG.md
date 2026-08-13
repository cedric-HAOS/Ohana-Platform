# Changelog

Toutes les modifications notables apportées à Ohana Platform sont documentées dans ce fichier.

Le format s’inspire de Keep a Changelog et le projet suit une stratégie de versionnement sémantique.

## [1.0.51] - 2026-08-13

### Ajouté

* Composition d'Ohana-Agent 1.13.0 et Ohana-Vision 1.12.0 pour sauvegarder
  logiquement INFRA-01 vers iCloud, sans staging persistant sur sa microSD.
* Profil `infra-01` déclarant dnsmasq, Chrony et l'utilitaire `age` pour un
  provisionnement reproductible par Ohana-Installer 1.8.0.
* Contrat de restauration associant le manifeste public au descripteur inclus
  dans l'archive chiffrée.

### Sécurité

* Le DHCP reste inactif après installation ou restauration jusqu'à une
  activation explicite confirmant l'arrêt de l'ancien serveur DHCP.
* La rotation iCloud est désactivée par défaut et n'opère qu'après validation
  complète d'une nouvelle sauvegarde.

### Validation

* Agent 1.13.0 : 1278 tests réussis, 1 ignoré et Ruff validé.
* Vision 1.12.0 : 852 tests, Ruff et syntaxe JavaScript validés.
* Installer 1.8.0 : 269 tests, Ruff et contrats de manifeste validés.

## [1.0.50] - 2026-08-11

### Corrigé

* Référencement d'Ohana-Vision 1.11.8, qui actualise en place les états de
  santé et de présence sans reconstruire la topologie ni rejouer ses animations.
* Les libellés, indicateurs, liaisons et attributs d'accessibilité de la carte
  restent synchronisés avec les observations reçues en temps réel.
* Une action Home Assistant absente pour ZWAVE-01 reste vide après application.
  La planification NVM native de Z-Wave JS UI devient le parcours recommandé.

### Validation

* Vision 1.11.8 : 850 tests réussis, Ruff, syntaxe JavaScript, paquet et
  installation isolée validés.
* Manifeste et catalogue validés avec le parseur Ohana-Installer.

## [1.0.49] - 2026-08-11

### Corrigé

* Référencement d'Ohana-Agent 1.12.7, qui récupère la taille exacte de
  `backup/info` lorsque Home Assistant diffuse une sauvegarde sans
  `Content-Length`.
* Le streaming reste borné et refuse toujours un téléchargement dont la taille
  est absente à la fois des métadonnées HAOS et de la réponse HTTP.
* La protection de la carte microSD d'INFRA-01 et la validation distante avant
  rotation restent inchangées.

### Validation

* Agent : 1274 tests réussis, 1 ignoré, Ruff, paquet et installation isolée.
* Manifeste et catalogue validés avec le parseur Ohana-Installer.

## [1.0.48] - 2026-08-11

### Ajouté

* La prochaine composition Agent/Vision permet de déclencher une sauvegarde
  HAOS immédiate depuis la fiche de l'équipement, avec une correspondance
  stricte entre l'identifiant de l'équipement et celui de la cible du plugin.

### Corrigé

* Vision accorde un délai dédié au démarrage à froid de la connexion iCloud et
  du test de sauvegarde, sans modifier les autres délais d'administration.

### Validation

* Agent 1.12.6 : 1272 tests réussis, 1 ignoré et Ruff validé.
* Vision 1.11.7 : 848 tests réussis, Ruff et syntaxe JavaScript validés.

## [1.0.47] - 2026-08-11

### Corrigé

* Référencement d'Ohana-Vision 1.11.6 : les champs Apple masqués ne
  bloquent plus silencieusement l'application de la configuration HAOS.
* Les identifiants Apple et le code 2FA sont exigés uniquement pendant la
  connexion ou le renouvellement iCloud.
* Le test signale les modifications non appliquées au lieu d'utiliser sans
  avertissement l'ancienne configuration enregistrée par Agent.

### Validation

* Vision : 846 tests réussis, Ruff, format, syntaxe JavaScript, import isolé
  du wheel et artefacts distants validés par SHA-256.
* Concordance du manifeste et du catalogue Platform 1.0.47 validée avec le
  parseur Ohana-Installer.

## [1.0.46] - 2026-08-11

### Amélioré

* Référencement d'Ohana-Vision 1.11.5, qui nomme explicitement la clé de
  chiffrement des sauvegardes et indique son emplacement dans Home Assistant.
* Les valeurs HAOS non encore appliquées restent préservées pendant la
  connexion iCloud et la validation 2FA.
* Le formulaire de connexion Apple est replié après configuration et précise
  que les identifiants ne sont pas conservés.

### Validation

* Vision : 846 tests réussis, Ruff, format, syntaxe JavaScript et artefacts
  distants validés par SHA-256.
* Concordance du manifeste et du catalogue Platform 1.0.46 validée avec le
  parseur Ohana-Installer.

## [1.0.45] - 2026-08-11

### Modifié

* Vision recueille désormais directement les jetons HAOS et mots de passe de
  chiffrement dans des champs masqués, sans exposer leur valeur après
  enregistrement.
* La connexion iCloud et son renouvellement 2FA sont pilotés depuis Vision ;
  Installer fournit automatiquement la version vérifiée de rclone.
* Agent s'appuie sur les API publiques de sauvegarde Home Assistant et conserve
  `backup.env` uniquement pour la migration des installations existantes.

## [1.0.44] - 2026-08-11

### Ajouté

* Référencement d'Ohana-Agent 1.12.4, qui chiffre et transmet directement les
  sauvegardes HAOS vers iCloud sans écrire les archives sur la carte microSD
  d'INFRA-01.
* Référencement d'Ohana-Vision 1.11.3, qui administre l'activation, les adresses
  et les heures quotidiennes de HA-01, LINKY-01 et ZWAVE-01.
* Le manifeste installe `backup.example.yaml`, transmet `--backup-config` à
  Agent et conserve la configuration désactivée jusqu'à sa préparation par
  l'opérateur.
* Guide transversal de préparation de rclone, des secrets, de l'export NVM et
  de la validation progressive des restaurations.

### Sécurité

* Les secrets restent dans `/etc/ohana-agent/backup.env`, lisible par Agent et
  jamais renvoyé à Vision.
* Une sauvegarde Ohana reste disponible sur chaque HAOS ; la précédente n'est
  supprimée qu'après validation distante de l'archive et du SHA-256.
* Le diagnostic Vision est en lecture seule et les fichiers temporaires rclone
  sont refusés hors `tmpfs` par défaut.

### Validation

* Agent : 1269 tests réussis, 1 test ignoré, Ruff et format validés.
* Vision : 846 tests réussis, Ruff, format et syntaxe JavaScript validés.
* Concordance du manifeste et du catalogue Platform 1.0.44 validée avec le
  parseur Ohana-Installer.

## [1.0.43] - 2026-08-10

### Amélioré

* Référencement d'Ohana-Vision 1.11.2, qui transforme la page
  **Supervision / Hôte** en cockpit de santé avec de grands pictogrammes sain,
  dégradé et critique, des jauges de ressources et un diagnostic synthétique.
* La composition recommandée conserve Ohana-Agent 1.12.3 et adopte
  Ohana-Vision 1.11.2.

### Validation

* Vision : 845 tests réussis, Ruff et format validés, installation isolée du
  wheel 1.11.2 et présence des trois pictogrammes contrôlée dans le paquet.
* Rendu Vision contrôlé aux largeurs 1920, 1024 et 600 pixels sans erreur
  JavaScript.
* Concordance du manifeste et du catalogue Platform 1.0.43 validée avec le
  parseur Ohana-Installer.

## [1.0.42] - 2026-08-10

### Amélioré

* Référencement d'Ohana-Agent 1.12.3, qui partage la santé de l'hôte avec
  Vision, affiche les uptimes sous forme lisible et calcule l'état global ainsi
  que les incidents critiques au niveau des services logiques redondants.
* Référencement d'Ohana-Vision 1.11.1, qui ajoute la page
  **Supervision / Hôte** et le groupe de disponibilité dans l'éditeur de
  services.
* Les anciennes configurations possédant plusieurs DNS activés sont reconnues
  automatiquement comme un groupe redondant.

### Validation

* Agent : 1247 tests réussis, 1 test ignoré, installation propre et quinze
  assets vérifiés avec leurs empreintes GitHub.
* Vision : 842 tests réussis, installation du wheel 1.11.1 et quatre assets
  vérifiés avec leurs empreintes GitHub.
* Concordance du manifeste et du catalogue Platform 1.0.42 validée avec le
  parseur Ohana-Installer.

## [1.0.41] - 2026-08-10

### Corrigé

* Référencement d'Ohana-Agent 1.12.2, qui corrige les modèles MQTT Discovery
  des métriques hôte optionnelles.
* Le helper DHCP privilégié ne dépend plus du chargement de Pydantic lorsqu'il
  est déclenché pendant le remplacement de l'environnement Agent.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.41 validée avec le
  parseur Ohana-Installer.
* Les quinze artefacts Agent 1.12.2 et leurs empreintes GitHub ont été
  contrôlés avant publication de Platform.

## [1.0.40] - 2026-08-10

### Amélioré

* Référencement d'Ohana-Agent 1.12.1, qui publie la santé de la machine hôte
  dans Home Assistant et agrège les instances redondantes en services
  logiques.
* La perte d'une seule instance DNS produit désormais un service dégradé tant
  qu'une autre instance du groupe reste saine, sans masquer les alertes
  techniques individuelles.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.40 validée avec le
  parseur Ohana-Installer.
* Les fichiers de configuration attendus par le manifeste sont inclus dans la
  release Agent 1.12.1 et couverts par `SHA256SUMS`.

## [1.0.39] - 2026-08-10

### Ajouté

* Référencement d'Ohana-Agent 1.12.0, qui garantit sur disque les observations
  en attente et les rejoue de manière ordonnée et idempotente.
* Référencement d'Ohana-Vision 1.11.0, qui persiste les observations et ajoute
  le Centre d'incidents avec acquittement, silence temporaire et résolution.

### Déploiement

* Ohana-Installer 1.7.1 crée les répertoires d'état systemd nécessaires sous
  `/var/lib/ohana-agent` et `/var/lib/ohana-vision`.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.39.
* Tags, assets et sommes SHA-256 d'Agent 1.12.0, Vision 1.11.0 et Installer
  1.7.1 vérifiés après publication.

## [1.0.38] - 2026-08-10

### Amélioré

* Référencement d'Ohana-Agent 1.11.11, qui contextualise les alertes Home
  Assistant avec les équipements, services et capacités affectés, et retire
  l'ancienne entité « Dernière évaluation » devenue redondante.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.38.
* Assets et sommes SHA-256 d'Agent 1.11.11 vérifiés après publication.

## [1.0.36] - 2026-08-05

### Corrigé

* Référencement d'Ohana-Agent 1.11.9. Une réponse ICMP Windows n’est désormais valide que si elle contient un TTL.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.36.

## [1.0.35] - 2026-08-04

### Corrigé

* Référencement d'Ohana-Vision 1.10.9, qui supprime les troncs radio
  synthétiques : chaque chemin Wi-Fi ou Z-Wave affiché correspond désormais à
  une liaison déclarée dans la topologie.

### Validation

* Validation visuelle de 18 liaisons radio déclarées et rendues sans segment
  synthétique.
* Concordance du manifeste et du catalogue Platform 1.0.35.

## [1.0.34] - 2026-08-04

### Corrigé

* Référencement d'Ohana-Vision 1.10.8, qui corrige le routage des liaisons
  Wi-Fi et Z-Wave : troncs pointillés, indicateurs radio lisibles et absence de
  troncs intermédiaires pour une ou deux branches.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.34.
* Assets et sommes SHA-256 de Vision 1.10.8 vérifiés après publication.

## [1.0.33] - 2026-08-04

### Ajouté

* Référencement d'Ohana-Agent 1.11.8, qui publie les nœuds découverts avec le
  type dédié `zwave_module`.
* Référencement d'Ohana-Vision 1.10.7, qui ajoute « Module Z-Wave », une icône
  inspirée de la marque et harmonise les cartes compactes et leurs liaisons.
* Les équipements Z-Wave découverts contribuent désormais aux indicateurs de
  supervision, le bandeau est réduit à quatre KPI complémentaires et les
  liaisons Wi-Fi utilisent les mêmes troncs radio que Z-Wave.

### Validation

* Validation visuelle du bandeau à quatre KPI et des cartes radio compactes.
* Suites complètes Agent (`1220 passed, 1 skipped`), Vision (`813 passed`) et
  Installer (`247 passed`), Ruff, manifeste, catalogue, assets et sommes
  SHA-256 vérifiés avant publication.

## [1.0.32] - 2026-08-04

### Ajouté

* Référencement d'Ohana-Vision 1.10.6, qui indique les équipements Z-Wave
  découverts restant à positionner et prépare leur placement uniquement sur
  action explicite dans la page Architecture.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.32.
* Simulation des 19 équipements d’INFRA-01 et validation du brouillon par le
  modèle strict d’Ohana-Agent.
* Assets Vision complets et sommes SHA-256 vérifiées après publication.

## [1.0.31] - 2026-08-04

### Corrigé

* Référencement d'Ohana-Vision 1.10.5, qui restaure le rendu de la topologie
  lorsque plusieurs liaisons partagent le même équipement, notamment la
  passerelle Z-Wave.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.31.
* Assets Vision complets et sommes SHA-256 vérifiées après publication.

## [1.0.30] - 2026-08-04

### Ajouté

* Référencement d'Ohana-Agent 1.11.7, qui découvre automatiquement les nœuds
  Z-Wave JS et publie leur état vivant sans reproduire le maillage radio.
* Référencement d'Ohana-Vision 1.10.4, qui affiche les équipements radio sous
  forme compacte et permet de replier indépendamment les groupes Wi-Fi et
  Z-Wave.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.30.
* Assets Agent et Vision complets et sommes SHA-256 vérifiées après publication.

## [1.0.29] - 2026-08-04

### Corrigé

* Référencement d'Ohana-Agent 1.11.6, qui publie les suspensions planifiées de
  télémétrie Home Assistant avec le même identifiant de capacité que les
  observations exécutées.
* Référencement d'Ohana-Vision 1.10.3, qui resynchronise immédiatement la carte
  avec les observations et reconstruit les timelines bornées par plage horaire.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.29.
* Assets Agent et Vision complets et sommes SHA-256 vérifiées après publication.

## [1.0.28] - 2026-08-02

### Corrigé

* Référencement d'Ohana-Vision 1.10.2, qui aligne la santé et les capacités
  de la carte des services sur la timeline utilisée par la fiche équipement.
* Les services dont l'observation est absente des 100 dernières observations
  globales conservent leur dernier état connu dans les deux vues.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.28.
* Nom du wheel aligné sur l'artefact Vision 1.10.2.

## [1.0.27] - 2026-08-01

### Corrigé

* Référencement d’Ohana-Agent 1.11.5, qui conserve le routage `device` des
  observations suspendues lorsque le plugin réseau n’est pas exécuté.
* La surveillance hors plage de `SUN-01` ne peut plus être interprétée comme
  une mise à jour d’un service d’infrastructure inconnu.

### Modifié

* Platform 1.0.26 est retirée du catalogue sélectionnable car son correctif
  partiel révélait encore un second crash dans le même chemin de suspension.

### Validation

* Reproduction du défaut observé en production après le déploiement 1.0.26.
* Concordance du manifeste et du catalogue Platform 1.0.27.
* Nom du wheel aligné sur l’artefact Agent 1.11.5.

## [1.0.26] - 2026-08-01

### Corrigé

* Référencement d’Ohana-Agent 1.11.4, qui exporte les suspensions planifiées
  sans interrompre le processus Agent ni son API d’administration.
* Suppression de la boucle de redémarrage déclenchée hors de la plage horaire
  d’un équipement surveillé.

### Modifié

* Les suspensions planifiées sont projetées vers l’état neutre `unknown` et
  conservent leurs métadonnées explicatives.
* Platform 1.0.25 reste disponible avec le statut `supported`.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.26.
* Nom du wheel aligné sur l’artefact Agent 1.11.4.

## [1.0.25] - 2026-08-01

### Corrigé

* Référencement d’Ohana-Agent 1.11.3, qui conserve la connexion MQTT Home
  Assistant lors des seules mises à jour d’infrastructure.
* Suppression des faux passages simultanés à `Indisponible` provoqués par les
  publications transitoires `offline`.

### Modifié

* Le résumé de santé MQTT est retenu pour restaurer immédiatement les entités
  Home Assistant après une reconnexion.
* Platform 1.0.24 reste disponible avec le statut `supported`.

### Validation

* Concordance du manifeste et du catalogue Platform 1.0.25.
* Nom du wheel aligné sur l’artefact Agent 1.11.3.

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
