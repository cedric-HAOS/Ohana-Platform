# ADR-0002 — Organisation des produits

* **Statut** : Accepté
* **Date** : 2026-07-16

---

# Contexte

La plateforme Ohana est constituée de plusieurs produits développés indépendamment.

Afin de préserver la cohérence de l'écosystème, il est nécessaire de définir les responsabilités de chaque produit ainsi que les règles qui gouvernent leurs interactions.

Cette décision établit l'organisation officielle des produits composant la plateforme.

---

# Décision

Chaque produit de la plateforme possède une responsabilité clairement définie.

Les produits communiquent exclusivement au travers d'interfaces publiques.

Aucun produit ne doit implémenter une responsabilité appartenant à un autre.

Chaque dépôt reste autonome tout en s'intégrant dans l'architecture globale d'Ohana.

---

# Les produits

## Ohana Platform

Ohana Platform constitue le référentiel officiel de la plateforme.

Il rassemble les éléments communs à l'ensemble de l'écosystème.

Ses responsabilités sont :

* documenter l'architecture ;
* définir les principes de conception ;
* centraliser les Architecture Decision Records (ADR) transversaux ;
* publier les guides de déploiement ;
* maintenir le Design System ;
* fournir les ressources graphiques communes ;
* documenter les produits de la plateforme.

Ohana Platform ne contient aucun composant d'exécution.

---

## Ohana Agent

Ohana Agent est le moteur d'observation.

Ses responsabilités sont :

* exécuter les capacités ;
* piloter les plugins ;
* collecter les observations ;
* produire les événements ;
* exposer les données de supervision ;
* fournir les interfaces de communication.

Ohana Agent ne possède aucune responsabilité de présentation.

---

## Ohana Vision

Ohana Vision est l'interface de visualisation.

Ses responsabilités sont :

* représenter l'état de la plateforme ;
* afficher les chronologies ;
* présenter la topologie ;
* afficher les indicateurs de santé ;
* proposer les interfaces d'administration.

Ohana Vision ne produit aucune observation.

---

## Ohana House

Ohana House constitue le déploiement de référence.

Ses responsabilités sont :

* documenter une infrastructure réelle ;
* valider les procédures d'installation ;
* servir d'environnement de démonstration ;
* vérifier les choix architecturaux dans des conditions d'exploitation.

Ohana House n'est pas un produit logiciel mais une implémentation de référence de la plateforme.

---

# Relations entre les produits

Les produits collaborent au travers de contrats explicites.

Ohana Platform ne dépend d'aucun produit.

Ohana Agent fonctionne indépendamment de toute interface graphique.

Ohana Vision dépend des interfaces exposées par Ohana Agent.

Ohana House assemble les différents produits dans une infrastructure réelle.

Les dépendances sont orientées dans un seul sens.

---

# Documentation

Chaque produit possède sa propre documentation.

Cette documentation couvre :

* son architecture interne ;
* son fonctionnement ;
* ses guides spécifiques ;
* ses ADR ;
* sa feuille de route ;
* son historique des versions.

Ohana Platform documente uniquement les éléments communs à plusieurs produits.

---

# Versionnement

Chaque produit possède son propre cycle de version.

Les versions des produits sont indépendantes.

Une nouvelle version d'un produit n'impose pas nécessairement une évolution des autres composants.

La compatibilité est assurée par les interfaces publiques.

---

# Dépendances

Les dépendances entre produits doivent rester limitées.

Les échanges sont réalisés au travers de modèles publics et d'interfaces documentées.

Les dépendances directes entre implémentations sont proscrites.

Cette approche réduit le couplage et facilite l'évolution des composants.

---

# Alternatives étudiées

## Dépôt unique

Le regroupement de l'ensemble des produits dans un dépôt unique aurait simplifié certains développements.

En revanche, cette approche aurait augmenté le couplage entre les composants et rendu plus difficile leur évolution indépendante.

Cette solution n'a pas été retenue.

---

## Organisation par couches techniques

Une organisation par technologies ou frameworks a également été étudiée.

Elle ne reflétait pas les responsabilités fonctionnelles des différents produits.

Cette approche a été écartée.

---

## Organisation par produits

L'organisation retenue repose sur des produits spécialisés.

Chaque dépôt correspond à un domaine fonctionnel clairement identifié.

Cette approche améliore la lisibilité, la maintenabilité et l'évolutivité de la plateforme.

---

# Conséquences

Cette organisation implique :

* des dépôts indépendants ;
* une documentation spécialisée ;
* des cycles de développement distincts ;
* des responsabilités clairement identifiées ;
* des interfaces publiques stables ;
* une architecture modulaire.

Elle facilite également l'ajout de nouveaux produits dans l'écosystème.

---

# Évolutions futures

L'organisation retenue permet d'intégrer de nouveaux produits sans remettre en cause l'architecture existante.

De futurs composants pourront notamment être ajoutés pour :

* l'administration centralisée ;
* les services cloud ;
* les applications mobiles ;
* les connecteurs spécialisés ;
* les outils d'analyse.

Chaque nouveau produit devra définir une responsabilité propre et respecter les principes architecturaux de la plateforme.

---

# Décisions associées

* ADR-0000 — Architecture Decision Records
* ADR-0001 — Architecture de la plateforme
* ADR-0003 — Design System
