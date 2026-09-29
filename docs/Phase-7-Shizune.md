# Phase 7 — Shizune

## Cadre — 29 septembre 2026

Phase démarrée avant la clôture de la Phase 6 (validations réelles Bubule
encore en attente). Référence : [roadmap commune](../ROADMAP.md).

Objectif : garder Shizune comme **interface personnelle simple entre Tsunade et
l'utilisateur**, pas un second Vision. Shizune 0.4.0 est en production (PWA
servie par Vision en HTTP sur le LAN, passerelle `/api/shizune` vers le listener
compagnon de l'Agent, jeton dans IndexedDB).

### Choix de l'utilisateur (29 septembre)

- **Périmètre** : lots 1 à 3 tels que proposés ci-dessous.
- **Perte de synchronisation : écran d'erreur seul.** Pas de dernières
  données grisées avec bandeau ; l'écran « Connexion indisponible » est
  conservé et indique seulement l'heure de la dernière synchronisation
  réussie.

### Règle de la phase

Le critère 10 de la roadmap est contraignant : **aucune fonctionnalité sans
besoin réellement observé à l'usage**. Les lots ci-dessous corrigent des
écarts constatés à la lecture du code contre les critères ; toute autre idée
attend un constat d'usage.

## Audit des critères de sortie (29 septembre)

Constats faits par lecture de `Shizune/PWA/app.js`, `read_companion_summary`
(Agent `api/service.py`) et `web/routers/shizune.py` (Vision).

| Critère | État avant la Phase 7 | Lot |
| --- | --- | --- |
| PWA sans application native | acquis : PWA HTTP, sans service worker en HTTP ; association et usage réels (iPhone + Windows) | — |
| État général compréhensible | **écart** : `healthPresentation()` (« Konoha : Stable / Dégradé / Critique ») est définie mais jamais appelée ; l'accueil dit seulement « Aucun incident actif signalé » ou « Ce qui demande votre attention ». `konoha_state` n'est déduit que des incidents actifs | 1 |
| Incidents importants identifiés | un incident prioritaire mis en avant, les autres regroupés ; sévérité critique stylée. À confirmer à l'usage (libellés, tri) | 1 |
| Demande de décision compréhensible | question + contexte Agent affichés tels quels (`redact_sensitive_text`) ; le contexte peut rester technique (cite un `known_repair`, des critères). À relire sur les demandes réelles | 2 |
| Autoriser / refuser / reporter sans ambiguïté | trois boutons, aucun retour d'état de la demande après clic : `refresh()` seulement, la demande disparaît sans dire ce qui s'est passé | 2 |
| Résultat de la décision suivi | **écart** : seule l'« Activité » (événements `action`/`result`) le laisse deviner ; pas de rappel « Vous avez autorisé X → réparé / échoué / refusé » lié à la demande | 2 |
| Informations des contrats Agent, pas de logique parallèle | acquis : la PWA ne fait que mapper les contrats (`assessment`, `attention`, `preventive`). Point de vigilance : le regroupement en accueil (`stale`/`analyzing`/`watch`) est côté PWA | — |
| Perte de synchronisation explicite | **écart** : l'écran d'erreur ne dit pas depuis quand les données sont perdues (choix : écran d'erreur conservé, ancienneté ajoutée) | 1 |
| Pas d'administration technique | acquis : routes bornées (association, résumé, demandes, activité, réponse, diagnostic) ; test « aucune route système avec la session compagnon » | — |
| Besoin réel à l'usage | à alimenter par l'utilisateur ; aucune fonctionnalité ajoutée sans constat | — |

## Lots proposés

| Lot | Contenu | État |
| --- | --- | --- |
| 1 — État général et synchronisation | carte d'état de Konoha en tête de l'essentiel (une phrase, sans jargon) ; l'écran « Connexion indisponible » donne l'heure de la dernière synchronisation réussie | codé, non publié (Shizune) |
| 2 — Décision et suivi | message de confirmation après clic, report daté, section « Décisions récentes » (24 h) : réponse + issue tirée de l'activité de l'Agent ; relais Vision `GET /api/shizune/requests/recent` vers le contrat Agent existant `/v1/incidents/requests/all` (aucune logique métier ajoutée à la PWA) | codé, non publié (Shizune, Vision) |
| 3 — Sandbox, documentation, validation réelle | étapes ajoutées au full-stack (carte d'état sur le vrai résumé Agent, suivi de décision, perte puis reprise de synchronisation), plan de test PWA ; parcours réel sur iPhone après déploiement | Sandbox à confirmer ; validation réelle après déploiement |

**Lot 1 bis — accueil « ce qui va » et « ce qui ne va pas »** (demande de
l'utilisateur, maquette validée le 29 septembre) : l'accueil ne montrait que les
problèmes. Ordre validé : état de Konoha avec les icônes de Vision (bouclier
vert, orange, octogone rouge, réduites à 144 px : ~21 Ko au lieu de 600 Ko) ;
**Services essentiels** ; **Journaux par équipement** avec la date du dernier
contrôle ; **Prévention**. Choix de l'utilisateur : les autres problèmes ne
sont signalés que par l'icône de leur tuile (pas de bloc « À traiter »),
« Hôte INFRA-01 » est retiré (si Shizune s'affiche, l'hôte est en ligne), le
contrôle des journaux est une information du bloc journaux, sans décompte
« N équipements OK sur 4 ».

Contrat Agent (résumé compagnon) :

- `services` : une tuile par service essentiel *configuré* (DNS, DHCP, MQTT,
  Home Assistant, Z-Wave, Téléinformation ; type lu dans
  `infrastructure.yaml`), état = pire contrôle du type ; durée mesurée
  (`tsunade_capability_state.latency_ms`, migration additive) affichée « 4,6 ms »
  pour un service sain. Sans mesure de moins de 48 h : `unknown`, jamais sain.
- `logs` : dernier contrôle terminé et, par source (INFRA-01, LINKY-01,
  ZWAVE-01, HA-01), `decision` (demande en attente), `analyzing`, `attention`,
  `watch` (bruit accepté, « Bruit connu · N accepté(s) ») ou `ok`.

Ajout non demandé, à confirmer : le lien « Voir les décisions » dans la carte
d'état lorsqu'une décision attend, et « Voir tous les sujets suivis » en bas
de l'accueil, pour que les incidents et décisions qui ne sont pas des journaux
restent atteignables.

Contexte de demande lisible : non modifié. Les questions et contextes viennent
de l'Agent (`repair_catalog.py`) ; à relire sur les demandes réelles avant de
toucher au texte (critère 10).

## Hors périmètre

- Notifications : la réserve de la Phase 5 est couverte par l'automatisation
  Home Assistant « Santé Ohana-House ». À rouvrir uniquement si l'usage le
  justifie (critère 10).
- Fonctionnement hors ligne : seulement si un besoin concret apparaît.
- Application native, APNs : non requis (critère 1).
