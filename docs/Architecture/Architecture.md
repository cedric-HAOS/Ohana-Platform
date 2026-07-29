# Architecture de la plateforme Ohana

## 1. Introduction

Ohana est une plateforme d'observabilité conçue pour superviser, analyser et administrer une infrastructure de manière déclarative, résiliente et extensible.

La plateforme repose sur une séparation claire des responsabilités entre l'acquisition des observations, leur traitement, leur visualisation et leur déploiement.

Cette architecture favorise la modularité, la maintenabilité et l'évolutivité tout en conservant un modèle de données cohérent à travers l'ensemble des composants.

Ce document constitue la référence architecturale officielle de la plateforme.

---

# 2. Vision

La plateforme Ohana est organisée autour de plusieurs produits complémentaires, chacun possédant une responsabilité clairement définie.

* **Ohana Platform** constitue le référentiel officiel de la plateforme. Il regroupe l'architecture, la documentation, les guides de déploiement, les ressources communes et les décisions d'architecture.

* **Ohana Agent** est le moteur d'observation. Il exécute les capacités, collecte les observations, pilote les plugins et publie les événements produits par l'infrastructure.

* **Ohana Vision** est l'interface de visualisation et d'administration. Il présente l'état de l'infrastructure en temps réel, conserve l'historique des observations et offre une représentation graphique des capacités supervisées.

* **Ohana Installer** applique le manifeste de composition publié par Platform. Il installe, met à jour et désinstalle Agent et Vision sur Linux/systemd.

* **Ohana House** est le déploiement de référence de la plateforme. Il constitue une implémentation réelle permettant de valider les choix d'architecture, les guides de déploiement et les évolutions de la plateforme.

Ces produits forment ensemble l'écosystème Ohana.

---

# 3. Philosophie

La conception d'Ohana repose sur plusieurs principes fondamentaux.

Une infrastructure est décrite par les capacités qu'elle fournit plutôt que par les technologies qu'elle utilise.

Les composants sont indépendants, spécialisés et faiblement couplés.

Chaque information importante doit être observable.

La configuration décrit le comportement attendu sans imposer une implémentation particulière.

Les échanges entre composants sont réalisés au travers d'interfaces clairement définies.

L'architecture privilégie la simplicité, la lisibilité et la stabilité plutôt que la complexité fonctionnelle.

---

# 4. les composants de la plateforme

## Ohana Platform

Ohana Platform rassemble l'ensemble de la documentation officielle de la plateforme.

Il définit les principes architecturaux, les conventions, les guides de déploiement, les ressources graphiques et les références communes utilisées par tous les autres projets.

Il constitue la source de vérité de l'écosystème Ohana.

---

## Ohana Agent

Ohana Agent est le moteur d'exécution de la plateforme.

Il orchestre les capacités, exécute les plugins, collecte les observations, publie les événements et expose les données nécessaires aux autres composants.

L'agent ne possède aucune logique de présentation.

---

## Ohana Vision

Ohana Vision fournit une représentation graphique de l'état de l'infrastructure.

Il exploite les observations produites par l'agent afin de présenter :

* la santé des capacités ;
* la topologie ;
* les observations récentes ;
* les chronologies d'état ;
* les indicateurs de supervision.

Vision reste indépendant du moteur d'exécution.

---

## Ohana Installer

Ohana Installer gère le cycle de vie des composants publiés. Il lit le manifeste de Platform, vérifie les artefacts officiels et réconcilie les configurations et unités systemd sans contenir de logique métier.

---

## Ohana House

Ohana House représente une infrastructure réelle utilisant l'ensemble des composants de la plateforme.

Il sert de référence pour les procédures d'installation, les scénarios de validation et les démonstrations.

Il permet de vérifier les choix d'architecture dans des conditions proches de la production.

---

# 5. Les couches de la plateforme

L'architecture d'Ohana est organisée selon plusieurs couches successives.

## Infrastructure

La couche d'infrastructure représente les équipements, les services et les ressources supervisées.

Elle ne dépend d'aucun composant logiciel de la plateforme.

---

## Plugins

Les plugins assurent la communication avec l'infrastructure.

Ils implémentent une capacité métier spécifique sans connaître le fonctionnement global du système.

---

## Runtime

Le runtime constitue le cœur d'Ohana Agent.

Il orchestre les plugins, le planificateur, le bus d'événements, les moteurs internes et les exportateurs.

Le runtime représente l'unique point de coordination des traitements.

---

## API

Les interfaces d'échange exposent les observations et les informations produites par le runtime.

Elles assurent l'interopérabilité avec les autres composants de la plateforme.

---

## Visualisation

Cette couche transforme les données techniques en représentations compréhensibles par les utilisateurs.

Elle regroupe les tableaux de bord, les chronologies, la topologie et les interfaces d'administration.

---

## Utilisateur

La dernière couche correspond aux personnes qui exploitent la plateforme.

Les utilisateurs interagissent exclusivement avec les interfaces prévues à cet effet.

---

# 6. Les flux

La plateforme repose sur plusieurs flux fonctionnels indépendants.

Les principaux flux sont :

* les observations produites par les capacités ;
* les événements internes ;
* les données exposées par les API ;
* les informations affichées par Vision ;
* les commandes d'administration ;
* les configurations déclaratives.

Chaque flux est documenté en détail dans le document *Flux.md*.

---

# 7. Les capacités

La capacité constitue l'unité fonctionnelle fondamentale d'Ohana.

Une capacité représente un service observable fourni par une infrastructure.

Chaque capacité produit des observations décrivant son état.

Les observations constituent le langage commun de l'ensemble de la plateforme.

Les définitions précises des concepts métier sont centralisées dans le document *Reference/Glossaire.md*.

---

# 8. Principes architecturaux

L'ensemble de la plateforme respecte les principes suivants.

* Responsabilité unique par composant.
* Faible couplage entre les modules.
* Forte cohésion interne.
* Interfaces explicites.
* Architecture orientée événements.
* Configuration déclarative.
* Extensibilité par plugins.
* API stables et versionnées.
* Documentation maintenue avec le code.
* Tests automatisés pour chaque comportement observable.

Ces principes s'appliquent à tous les composants de la plateforme de l'écosystème.

---

# 9. Extensions

L'architecture est conçue pour accueillir de nouvelles fonctionnalités sans remise en cause de ses fondations.

Les principales évolutions envisagées sont notamment :

* administration complète de la plateforme ;
* supervision multi-sites ;
* déploiements distribués ;
* applications mobiles ;
* services cloud ;
* intelligence artificielle ;
* catalogue de plugins.

L'intégration de nouvelles fonctionnalités doit respecter les principes architecturaux définis par ce document.

---

# 10. Évolutions futures

L'architecture d'Ohana est pensée comme une base stable destinée à évoluer progressivement.

Les décisions structurantes sont documentées dans les Architecture Decision Records (ADR).

Toute évolution majeure de la plateforme doit préserver la cohérence de l'écosystème, la stabilité des interfaces publiques et la compatibilité des concepts fondamentaux.

Ce document constitue la référence architecturale de l'ensemble des projets Ohana.
