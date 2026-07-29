# Flux de la plateforme Ohana

## 1. Introduction

La plateforme Ohana repose sur un ensemble de flux permettant aux différents composants de collaborer de manière cohérente, découplée et observable.

Chaque flux représente un échange fonctionnel entre plusieurs composants de la plateforme.

Les flux sont indépendants des technologies utilisées pour leur implémentation.

Ils décrivent les échanges métier qui structurent le fonctionnement de l'écosystème Ohana.

---

# 2. Vue d'ensemble

Les principaux flux de la plateforme sont les suivants :

* Flux d'observation
* Flux d'événements
* Flux de santé
* Flux de chronologie
* Flux de visualisation
* Flux de configuration
* Flux d'administration

Chaque flux possède une responsabilité clairement définie.

---

# 3. Flux d'observation

Le flux d'observation constitue le cœur de la plateforme.

Les capacités supervisées produisent des observations décrivant leur état.

Ces observations sont collectées par Ohana Agent puis traitées par le runtime avant d'être mises à disposition des autres composants.

Les observations représentent la source de vérité de la plateforme.

### Objectifs

* Décrire l'état des capacités.
* Alimenter les moteurs internes.
* Conserver un historique.
* Fournir les données de supervision.

---

# 4. Flux d'événements

Les événements représentent les changements significatifs intervenant au sein de la plateforme.

Ils permettent aux composants de réagir sans dépendance directe.

Le runtime diffuse les événements aux composants concernés.

Les événements favorisent une architecture faiblement couplée.

### Objectifs

* Synchroniser les composants.
* Découpler les traitements.
* Réagir aux changements d'état.

---

# 5. Flux de santé

À partir des observations reçues, le moteur de santé d'Ohana Vision détermine l'état des capacités, des services, des nœuds et de l'infrastructure.

Le résultat constitue une vue synthétique de la plateforme.

Ce flux permet d'identifier rapidement les anomalies.

### Objectifs

* Évaluer la santé des capacités.
* Produire une synthèse de l'infrastructure.
* Alimenter les tableaux de bord.

---

# 6. Flux de chronologie

Dans Ohana Vision, les observations successives sont regroupées afin de construire une chronologie des états.

Cette chronologie permet de représenter l'évolution des capacités dans le temps.

Elle constitue la base de la timeline affichée par Ohana Vision.

### Objectifs

* Reconstituer les périodes d'état.
* Conserver l'historique.
* Produire une représentation temporelle.

---

# 7. Flux de visualisation

Ohana Vision consomme les informations produites par Ohana Agent.

Les données sont transformées en représentations graphiques adaptées aux utilisateurs.

La visualisation ne modifie jamais les données produites par le runtime.

### Objectifs

* Présenter l'état global.
* Visualiser les observations.
* Afficher les chronologies.
* Représenter la topologie.
* Mettre en évidence les alertes.

---

# 8. Flux de configuration

Agent possède la configuration déclarative de l'infrastructure et des capacités supervisées. Chaque produit possède uniquement sa configuration applicative.

Vision lit et modifie la configuration métier par l'API d'administration d'Agent ; il ne conserve pas de copie métier indépendante.

La configuration reste déclarative.

### Objectifs

* Décrire l'infrastructure.
* Déclarer les capacités.
* Paramétrer les composants.
* Adapter le comportement de la plateforme.

---

# 9. Flux d'administration

Le flux d'administration permet aux utilisateurs de modifier le comportement de la plateforme.

Les opérations d'administration sont transmises au runtime au travers d'interfaces dédiées.

Les modifications sont appliquées de manière contrôlée.

### Objectifs

* Administrer les composants.
* Modifier la configuration.
* Déclencher des opérations.
* Superviser la plateforme.

---

# 10. Relations entre les flux

Les différents flux ne sont pas indépendants.

Le flux d'observation alimente :

* le flux de santé ;
* le flux de chronologie ;
* le flux de visualisation.

Le flux d'événements permet de synchroniser les traitements internes.

Le flux de configuration influence le comportement du runtime.

Le flux d'administration peut provoquer de nouvelles observations.

Cette organisation garantit une architecture cohérente dans laquelle chaque flux possède une responsabilité précise.

---

# 11. Principes de circulation des données

La circulation des informations dans la plateforme respecte plusieurs règles.

Une observation n'est produite qu'une seule fois.

Une observation publiée n'est jamais modifiée.

Les moteurs internes enrichissent les informations sans altérer les données d'origine.

La visualisation consomme les données mais ne les transforme pas.

Les composants échangent uniquement les informations nécessaires à leur fonctionnement.

Les interfaces publiques constituent les seuls points d'échange entre les produits.

---

# 12. Évolutions futures

L'architecture des flux est conçue pour accueillir de nouveaux échanges sans remettre en cause les principes fondamentaux de la plateforme.

De futurs flux pourront notamment être ajoutés pour :

* les notifications ;
* les automatisations ;
* les déploiements distribués ;
* la synchronisation multi-sites ;
* les services cloud ;
* les assistants intelligents.

Toute évolution devra préserver la séparation des responsabilités et la cohérence des flux existants.

---

# 13. Conclusion

Les flux décrits dans ce document représentent les échanges fonctionnels de la plateforme Ohana.

Ils définissent la manière dont les composants collaborent tout en restant indépendants de leur implémentation technique.

Ces flux constituent la base des diagrammes d'architecture et des interfaces publiques de l'écosystème Ohana.
