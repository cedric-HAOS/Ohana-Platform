# Architecture de déploiement de la plateforme Ohana

## 1. Introduction

La plateforme Ohana est conçue pour être déployée de manière modulaire.

Chaque composant possède une responsabilité clairement définie et peut évoluer indépendamment des autres.

L'architecture de déploiement privilégie la simplicité, la résilience et l'observabilité.

Ce document décrit les principes d'organisation des composants de la plateforme.

Les procédures d'installation sont documentées dans les guides de déploiement.

---

# 2. Objectifs

L'architecture de déploiement poursuit plusieurs objectifs.

* Simplifier l'installation de la plateforme.
* Permettre une évolution progressive.
* Favoriser la modularité.
* Réduire les dépendances entre composants.
* Faciliter la maintenance.
* Autoriser différents scénarios de déploiement.

---

# 3. Les composants

La plateforme est composée de plusieurs produits indépendants.

## Ohana Platform

Référentiel documentaire.

Il ne participe pas à l'exécution de la plateforme.

---

## Ohana Agent

Moteur d'observation.

Il supervise les capacités, collecte les observations et expose les informations nécessaires aux autres composants.

---

## Ohana Vision

Interface utilisateur et portail d'administration.

Elle consomme les données produites par Agent et transmet les opérations d'administration à son API authentifiée.

---

## Ohana Installer

Gestionnaire de cycle de vie.

Il lit le manifeste publié par Platform, installe Agent et Vision, prépare leurs configurations et gère les unités systemd.

---

## Infrastructure supervisée

L'infrastructure représente l'ensemble des équipements, services et ressources observés par la plateforme.

Elle reste indépendante des composants Ohana.

---

# 4. Architecture logique

La plateforme est organisée selon plusieurs couches.

* Infrastructure
* Plugins
* Runtime
* Interfaces
* Visualisation
* Utilisateurs

Chaque couche dépend uniquement des services fournis par la couche inférieure.

Cette organisation favorise le découplage des composants.

---

# 5. Scénarios de déploiement

La plateforme peut être déployée selon différents scénarios.

## Déploiement minimal

Le déploiement minimal comprend :

* un Ohana Agent ;
* une infrastructure supervisée.

Ce scénario permet de produire des observations sans interface graphique.

---

## Déploiement standard

Le déploiement standard comprend :

* un Ohana Agent ;
* un Ohana Vision ;
* une infrastructure supervisée.

Il constitue le scénario recommandé.

---

## Déploiement de référence

Le déploiement de référence correspond au projet Ohana House.

Il rassemble :

* Ohana Agent ;
* Ohana Vision ;
* l'infrastructure réelle ;
* les configurations de référence.

Ce déploiement sert de validation permanente de la plateforme.

---

## Déploiement étendu

L'architecture permet d'ajouter :

* plusieurs agents ;
* plusieurs infrastructures ;
* plusieurs interfaces ;
* des composants complémentaires.

Ces évolutions ne remettent pas en cause les principes fondamentaux de la plateforme.

---

# 6. Communication entre composants

Les composants communiquent uniquement au travers d'interfaces clairement définies.

Les observations sont publiées par Ohana Agent.

Les interfaces exposent les informations nécessaires aux autres produits.

Ohana Vision consomme ces informations sans intervenir dans leur production.

Cette séparation garantit l'indépendance des composants.

---

# 7. Configuration

Agent est la source de vérité de l'infrastructure déclarative et des services observés. Vision possède uniquement sa configuration applicative et utilise l'API d'administration d'Agent pour toute modification métier.

Installer déploie les fichiers initiaux définis par le manifeste Platform, puis préserve les personnalisations locales lors des mises à jour.

La plateforme privilégie les formats ouverts, lisibles et validés avant écriture.

---

# 8. Résilience

L'architecture favorise la continuité de fonctionnement.

Une défaillance d'un composant ne doit pas entraîner l'arrêt de l'ensemble de la plateforme.

Les responsabilités étant clairement séparées, chaque produit peut être redémarré, remplacé ou mis à jour indépendamment.

---

# 9. Évolutivité

L'architecture de déploiement est conçue pour accompagner la croissance de la plateforme.

De nouveaux produits peuvent être ajoutés.

Les composants existants peuvent évoluer indépendamment.

Les interfaces publiques assurent la compatibilité entre les différentes versions.

Cette approche permet une évolution progressive sans remise en cause de l'architecture.

---

# 10. Sécurité

Les composants de la plateforme communiquent exclusivement au travers d'interfaces prévues à cet effet.

Chaque produit reste responsable de ses propres mécanismes d'authentification, d'autorisation et de protection des données.

La plateforme privilégie la réduction de la surface d'exposition et la séparation des responsabilités.

Les aspects de sécurité spécifiques à chaque composant sont documentés dans leurs projets respectifs.

---

# 11. Bonnes pratiques de déploiement

Les recommandations suivantes s'appliquent à tous les déploiements de la plateforme.

* Déployer chaque produit indépendamment.
* Conserver des configurations déclaratives.
* Versionner les fichiers de configuration.
* Superviser les composants de la plateforme.
* Sauvegarder les configurations.
* Documenter les personnalisations locales.
* Tester les mises à jour avant leur mise en production.

Ces pratiques contribuent à la stabilité et à la maintenabilité de la plateforme.

---

# 12. Évolutions futures

L'architecture de déploiement permet d'intégrer progressivement de nouveaux scénarios.

Parmi les évolutions envisagées :

* supervision distribuée ;
* infrastructures multi-sites ;
* haute disponibilité ;
* orchestration par conteneurs ;
* services cloud ;
* administration centralisée.

Ces évolutions s'inscrivent dans les principes architecturaux définis par la plateforme.

---

# 13. Conclusion

L'architecture de déploiement d'Ohana repose sur une séparation claire des responsabilités entre les différents produits.

Cette organisation garantit une plateforme modulaire, extensible et adaptée à des contextes de déploiement variés.

Les guides de déploiement décrivent les procédures d'installation et de configuration correspondant à cette architecture.
