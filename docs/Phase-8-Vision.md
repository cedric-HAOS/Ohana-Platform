# Phase 8 — Vision

## Cadre — 2 octobre 2026

Phase démarrée alors que les derniers essais réels des phases 6 et 7 restent
reportés. Référence : [roadmap commune](../ROADMAP.md#phase-8--vision).

Objectif : comprendre depuis Vision ce qu'Ohana a observé, investigué, conclu,
décidé, exécuté et vérifié pour un incident, sans ouvrir SQLite ni SSH. Agent
reste la source de vérité ; Vision présente ses contrats.

## Audit initial

L'audit porte sur le contrat `TsunadeIncident` d'Agent, le rendu
`incidents.js` de Vision et les métadonnées d'incidents réels lues en mode
SQLite lecture seule sur INFRA-01 le 2 octobre. Aucun contenu de preuve ni
secret de production n'a été copié dans ce suivi.

| Critère de sortie | État au démarrage |
| --- | --- |
| État actuel rapidement compréhensible | Partiel : carte avec priorité, état, conclusion datée et prochaine action ; dossier long pour reconstruire le parcours. |
| Étapes distinctes | Partiel : décision, expertise, réparation et chronologie existent dans des blocs séparés ; pas de parcours synthétique observation → vérification. |
| Preuves principales accessibles | Partiel : anomalies de journaux, indices d'hypothèse et détails d'événements visibles selon le cas ; les faits et leur provenance ne sont pas rassemblés. |
| Hypothèses distinguées des faits | Partiel : liste « Hypothèses » et indices concordants/contradictoires ; l'origine d'une analyse est parfois déduite par Vision de la présence d'hypothèses. |
| Contribution Katsuyu qualifiée | Partiel : bloc « Analyse Katsuyu » et erreurs techniques ; vérifier sur un cycle IA réel la différence entre calcul, hypothèse et confirmation déterministe. |
| Limites visibles | Insuffisant : Agent fournit notamment `confirmation_gap`, `failed_investigations` et les limites de certaines investigations, mais le dossier ne les présente pas comme telles. |
| Réparation traçable | Partiel : statut et résultat affichés ; le contrat contient les dates de proposition, autorisation, exécution et vérification, mais le dossier n'en fait pas une séquence lisible. |
| États fournis par Agent | À surveiller : l'état métier et `assessment` viennent d'Agent, mais Vision déduit encore certains libellés et la nature Katsuyu de plusieurs champs. |
| Performances | Non mesurées pour ce nouveau parcours. Mesurer le coût du chargement d'un dossier réel et le rendu des incidents longs. |
| Incident compris entièrement dans Vision | Non démontré. Recette réelle à mener sur les deux cas ci-dessous. |

## Cas pilotes réels

1. **Téléinformation, 28 septembre vers 11:15** : observation, deux
   investigations, diagnostic, proposition de réparation, autorisation,
   exécution et vérification réussie, puis résolution. Ce cas couvre toute la
   chaîne de réparation. La présence de ces événements et de leurs dates est
   vérifiée dans Agent ; la lisibilité du dossier Vision reste à vérifier.
2. **Santé de l'hôte, 29 septembre vers 08:33** : observation, investigations,
   diagnostic, action proposée sans réparation supervisée, aggravation,
   observations répétées et résolution. Ce cas vérifie que Vision distingue
   proposition et action exécutée, ainsi que les limites d'investigation.

Un cas avec analyse IA Katsuyu et hypothèses devra compléter la recette avant
clôture. Il ne faut pas présenter une hypothèse ou une corrélation temporelle
comme une cause confirmée.

## Lots de travail

| Lot | Résultat attendu | État |
| --- | --- | --- |
| 1 — Parcours lisible | Dans le dossier, une synthèse ordonnée des étapes disponibles, datées, avec état courant, provenance et prochaine action en tête ; les détails existants restent accessibles. | Aperçu local validé par l’utilisateur le 2 octobre |
| 2 — Preuves, hypothèses et limites | Présenter les faits et preuves principaux avec leur source ; afficher explicitement les hypothèses, contradictions, lacunes et analyses impossibles à conclure. Compléter le contrat Agent seulement si la preuve manque réellement. | Implémenté localement ; recette réelle à faire |
| 3 — Décision et réparation | Rendre lisibles proposition, autorisation ou refus, exécution et vérification avec leurs dates et résultat, sans confondre proposition et action. | Implémenté localement ; recette réelle à faire |
| 4 — Recette et performances | Rejouer les cas pilotes dans la Sandbox et dans Vision, vérifier bureau/mobile, mesurer chargement et rendu, puis contrôler un dossier représentatif sur Konoha après déploiement. | Qualification locale réussie ; confirmation après déploiement à consigner |

La phase se clôt quand les dix critères de la roadmap sont prouvés sur un
incident représentatif depuis Vision. La validation locale, la publication,
le déploiement et la confirmation réelle sont consignés séparément.

## Lot 1 — Première implémentation locale, 2 octobre

Le dossier Vision présente un parcours chronologique compact : dernier événement
de chaque type, date, résumé et nombre d'occurrences. L'état courant reste dans
l'en-tête de la carte ; la prochaine action et la provenance déclarées par Agent
précèdent les étapes. L'historique complet et les blocs existants restent accessibles.
Une proposition n'est pas qualifiée d'exécution et une origine absente n'est pas
déduite de la présence d'hypothèses. Aucun contrat Agent ni appel API supplémentaire.

Validation locale : 476 tests web passent, dont une régression sur l'ordre des
étapes, les occurrences, la provenance, les données absentes, l'échappement HTML
et la priorité de l'évaluation courante sur le dossier en cache.
La recette visuelle bureau/mobile et les cas pilotes réels restent à effectuer.
Aucune publication, aucun déploiement ni confirmation de production.

## Lots 2 et 3 — Implémentation locale, 2 octobre

Le dossier présente les faits et limites de la décision : provenance explicite,
lacunes de confirmation, contexte manquant, investigations non abouties et
collecte tronquée. Le nombre de lignes correspondantes reste distinct du nombre
d’anomalies. Une collecte sans anomalie ne vaut pas résolution. Les hypothèses
et leurs contradictions restent qualifiées comme telles ; leur présence ne
suffit plus à attribuer l’analyse à Katsuyu.

Les preuves des investigations sont accessibles dans un bloc dépliable, avec
opération ou source, date, état de collecte, erreur et résultat structuré fourni
par Agent. La décision abrégée de la liste est complétée uniquement par un
événement diagnostic du dossier portant la même date. Une ancienne analyse ne
fournit pas les hypothèses de la décision courante. Aucun contrat Agent modifié.

Chaque réparation présente proposition, autorisation ou refus, report,
exécution ou tentative et résultat daté. Les noms tiennent compte du contrat :
`authorized_at` peut dater un refus ; `verified_at` peut dater un échec ou une
expiration, sans preuve de vérification réussie. Seul le statut `succeeded`
est présenté comme une vérification Shikamaru réussie.

Les régressions couvrent la provenance absente, les contradictions, les lacunes,
la troncature, l’échappement HTML, le rapprochement des décisions par date,
le refus, le report, l’échec, l’expiration et la vérification en attente.
Validation locale finale : 477 tests web passent ; Ruff (lint et format) sur
les tests modifiés et contrôle des diffs sans erreur.
L’aperçu local utilise des données fictives et le véritable composant Vision :
les cas hypothèse IA, réparation réussie et réparation refusée ont été inspectés.
La recette bureau/mobile complète, les mesures de performance et les cas réels
restent au lot 4. Aucun déploiement ni publication.

## Lot 4 — Qualification locale, 2 et 3 octobre

Le scénario `incident-dossier` utilise le serveur HTTP Agent, sa base SQLite
et Vision/Uvicorn réels. Le Supervisor est simulé ; le diagnostic IA est une
fixture explicite, sans inférence. Il couvre la téléinformation réparée et
vérifiée, la santé de l'hôte avec investigation expirée et proposition sans
exécution, une hypothèse contradictoire avec contexte insuffisant et collecte
tronquée, puis un dossier borné à 1 000 événements.

Neuf contrôles réussissent. Les requêtes au proxy Vision ont un p95 de 26,77 à
54,63 ms (20 mesures par cas). La génération HTML du contrôleur a un p95 de
0,03 à 3,46 ms (100 mesures après échauffement). Ces mesures locales excluent
le coût DOM, le réseau de production et l'inférence IA. Le dossier long reste
borné ; son historique n'est pas présenté comme exhaustif.

La recette visuelle bureau et mobile couvre les preuves, hypothèses, limites
et la réparation vérifiée. Le contrôle mobile à 390 × 844 a révélé un débordement
des blocs internes, corrigé et remesuré sans dépassement de leur largeur.
La suite Vision complète réussit : 932 tests ; Ruff et contrôle des diffs passent.
Les scénarios `teleinformation-supervisor-cycle`, `catalogue-repair-cycle`,
`ambiguous-katsuyu-cycle` et `followup-evidence-cycle` réussissent également.

La publication prévue compose Vision 1.36.0 avec Platform 1.0.139, sans changer
Agent. La confirmation réelle d'un dossier représentatif et d'un cycle IA
reste distincte de cette qualification locale.
