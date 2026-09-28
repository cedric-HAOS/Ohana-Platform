# Phase 3 — Mémoire opérationnelle de Tsunade

## Cadre — 27 septembre 2026

Phase démarrée après la clôture de la Phase 2 (10/10). Référence :
[roadmap commune](../ROADMAP.md). Choix de l'utilisateur : la résolution
manuelle se déclare d'abord dans Vision (Shizune plus tard).

Livraison en trois lots, publiés ensemble le 28 septembre 2026 dans
Platform 1.0.130 (Agent 1.38.0, Vision 1.29.0) :

- lot 1 : historique par réparation connue (tentatives, réussites, échecs,
  dernières dates) et cycle de vie actif, désactivé ou obsolète ;
- lot 2 : une proposition du catalogue cite la réparation connue active qui
  partage le symptôme, la preuve confirmée et l'action ;
- lot 3 : résolution manuelle déclarée dans Vision, confirmée par Shikamaru
  et conservée seulement après accord, comme une note jamais exécutable.

Sandbox : `known-repair-history`, `manual-resolution` et `--full-stack`.

## Clôture — 28 septembre 2026

**Phase 3 clôturée le 28 septembre 2026 : les critères de sortie démontrés
en réel sur Konoha et dans Sandbox.** Une seule panne a été provoquée,
l'arrêt de l'add-on teleinfo2mqtt sur LINKY-01 (données Linky interrompues
quelques minutes).

| Critère | Réel (Konoha, 28 septembre) |
| --- | --- |
| Réparation connue retrouvée à partir de symptômes et de preuves explicites | **acquis** : essai 1, critères « même symptôme, même preuve (Supervisor), même action » |
| Tentatives, réussites, échecs et dernière réussite historisés | **acquis** : teleinfo2mqtt 1/1 → 2/2, dernière réussite 11:18:14 |
| Proposition sans exécution automatique | **acquis** : essais 1 et 2, rien exécuté avant la décision |
| Résolution manuelle déclarable | **acquis** : essai 3, déclarée à 11:40:54 |
| Retour à l'état sain confirmé par Shikamaru | **acquis** : confirmé à 11:41:14 |
| Confirmation demandée avant de capitaliser | **acquis** : rien n'est retenu avant « Conserver comme piste connue » |
| Proximité temporelle jamais présentée comme preuve | **acquis** : absente des critères (essai 1), avertissement explicite (essai 3) |
| Commande libre jamais exécutable | **acquis** : `ha apps restart …` conservée comme `{kind: manual}`, sans opération ni cible |
| Réparation désactivable ou rendue obsolète | **acquis** : teleinfo2mqtt désactivée, Mosquitto obsolète puis réactivée |
| Autorisations de la Phase 2 respectées | **acquis** : autorisation (essai 1), refus sans reproposition (essai 2) |

Le compteur d'échecs n'a pas bougé pendant ces essais ; l'échec historisé
repose sur la validation réelle de la Phase 2 (chrony masqué, 26 septembre).

## Essais réels — 28 septembre 2026

Platform 1.0.130 déployée à 10:21. Départ : cinq réparations connues actives,
teleinfo2mqtt à 1 tentative et 1 réussite.

### Essai 1 — proposition fondée sur la réparation connue

| Étape | Heure |
| --- | --- |
| Add-on arrêté, incident `teleinformation.freshness` ouvert | 11:15:24 |
| Proposition `teleinfo2mqtt.restart`, risque faible, `known_repair` cité | 11:16:05 |
| Autorisation de l'utilisateur | 11:17:47 |
| Exécution | 11:17:54 |
| Shikamaru confirme l'état sain, incident résolu | 11:18:14 |

La proposition citait l'historique (1 réussite, 0 échec sur 1 tentative) et
les trois critères partagés, sans avertissement ni mention de proximité dans
le temps. Compteurs après l'essai : 2 tentatives, 2 réussites.

### Essai 2 — cycle de vie et refus

- Mosquitto : obsolète à 11:30:32, réactivée à 11:35:44 ; historique conservé.
- teleinfo2mqtt : désactivée à 11:30:56.
- Add-on arrêté : incident ouvert à 11:34:31, proposition à 11:35:03 **sans**
  `known_repair`, autorisation toujours exigée ; refusée, jamais exécutée, et
  rien de reproposé jusqu'à la résolution.

### Essai 3 — résolution manuelle

Premier passage manqué : l'add-on redémarré avant la déclaration, l'incident
s'est fermé (11:37:33) avant qu'elle arrive ; rien enregistré. Second passage
dans l'ordre « déclarer, puis démarrer » :

| Étape | Heure |
| --- | --- |
| Incident ouvert | 11:39:42 |
| Proposition de redémarrage refusée | 11:40:53 |
| Action déclarée : `ha apps restart 6fc079ce_teleinfo2mqtt_ohana` | 11:40:54 |
| Shikamaru confirme l'état sain, incident résolu | 11:41:14 |
| « Conserver comme piste connue » | 11:42:12 |

La candidate posait la question attendue et avertissait que la proximité dans
le temps ne prouve pas la cause et que la piste resterait une note. La piste
enregistrée n'a ni opération ni cible. teleinfo2mqtt a ensuite été
réactivée ; six entrées actives en fin d'essai.

## Constats pour le durcissement continu

- Vision : la section « Réparations connues » est repliée dans « Contrôles et
  bilan » et affiche « Aucune réparation connue. » tant que la vue Tsunade
  n'a pas fini de charger (plusieurs secondes sur INFRA-01) ; la page n'a pas
  permis de faire défiler jusqu'au bouton « Réactiver ».
- Résolution manuelle : une action faite avant sa déclaration échoue si
  l'incident se ferme entre-temps ; permettre la déclaration juste après la
  résolution.
- La piste manuelle conservée compte 1 tentative et 1 réussite, datée de son
  enregistrement plutôt que de la vérification de Shikamaru.
