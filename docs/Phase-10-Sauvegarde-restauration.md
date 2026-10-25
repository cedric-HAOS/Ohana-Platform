# Phase 10 — Sauvegarde et restauration

Démarrée le 25 octobre 2026. Objectif : considérer une sauvegarde comme fiable
uniquement lorsqu'elle peut **réellement être restaurée**. L'existence du
fichier n'est pas une validation.

Suivi des critères : [ROADMAP](../ROADMAP.md#phase-10--sauvegarde-et-restauration).

## Point de départ

Relevé du 25 octobre 2026 (lecture seule, `sandbox/run.ps1 live jobs-report`) :
`backup.infra` a réussi chaque jour du 19 au 25 octobre ; l'archive est chiffrée
par Katsuyu avec `age` puis publiée dans iCloud, le manifeste en dernier
(`docs/Backup.md` dans Ohana-Agent). Les sauvegardes HAOS sont créées et
chiffrées par HA-01, LINKY-01 et ZWAVE-01. Aucune restauration n'était
consignée : Ohana savait *quand* une sauvegarde avait été faite, jamais *si elle
avait été restaurée*.

## Principe retenu

Une restauration est une opération réelle sur une vraie machine. Ohana ne la
déduit donc jamais et ne la lance pas seul. Il tient le **registre des
restaurations que l'utilisateur déclare**, et en tire un état par cible :

| État | Sens |
| --- | --- |
| `never_tested` | cible sauvegardée, aucune restauration déclarée |
| `verified` | dernière restauration réussie, de moins de 180 jours |
| `stale` | dernière restauration réussie plus ancienne que 180 jours |
| `last_failed` | dernière restauration partielle ou échouée (urgent) |

Les cibles connues sont celles dont une observation `backup.run` a réussi. Une
sauvegarde échouée ne crée pas de cible et ne compte pas.

## Lot 1 — registre des restaurations (Agent 1.49.0, Vision 1.39.0)

- **Agent** : règle préventive `backup_restore` (`tsunade/preventive_backup.py`),
  tables `tsunade_backup_runs` et `tsunade_restore_tests` dans la base de contrôle.
  `GET /v1/backups/restore-tests` donne l'état par cible et l'historique ;
  `POST /v1/backups/restore-tests/declare` enregistre un test (cible, résultat
  `ok` / `partial` / `failed`, date, archive utilisée, note). Une restauration
  partielle ou échouée exige une note ; une date future est refusée.
- **Vision** : bloc « Sauvegardes restaurées » dans l'onglet « À surveiller »
  de la page Tsunade, avec le formulaire de déclaration.
- **Shizune** : les cibles jamais testées apparaissent dans la carte « Prévention »
  sans changement de l'application (elles sont des éléments à surveiller).
- La règle ne crée ni incident ni réparation : elle signale, comme les autres
  règles préventives. Un élément peut être ignoré 30 jours depuis Vision.
- **Sandbox** : scénario `backup-restore-evidence` (échoue sur Agent 1.48.0) et
  recette `--full-stack` : déclaration depuis Vision dans Chromium, refus d'une
  restauration partielle sans note, conservation par l'Agent.

## Lot 2 — intégrité des archives (Agent, Vision, non publié)

Les archives iCloud étaient contrôlées une seule fois, à leur publication.
L'Agent les relit maintenant de façon indépendante :

- **Quoi** : l'archive la plus récente de chaque cible (INFRA-01 et les HAOS
  activés), relue en flux par `rclone cat` : rien n'est écrit sur la microSD,
  rien n'est déchiffré, aucun secret n'est lu.
- **Comparaison** : taille et SHA-256 contre le manifeste (INFRA-01) ou le fichier
  `.sha256` (HAOS) ; pour INFRA-01, l'en-tête `age` confirme le chiffrement.
- **Quand** : une passe par jour (30 minutes après le démarrage de l'Agent) ;
  une archive n'est relue qu'une fois, puis une fois par semaine. Vision peut
  lancer un contrôle immédiat (`POST /v1/backups/archives/verify`).
- **Verdicts** : archive absente, taille ou empreinte différente, chiffrement
  absent = **urgent** ; remote illisible (session iCloud expirée) = non urgent,
  car rien n'est prouvé sur l'archive ; dernier contrôle de plus de 14 jours =
  à surveiller. Le contrôle ne modifie ni ne supprime aucune archive.
- **Essai réel en lecture seule (25/10)** : le code du vérificateur, exécuté sur
  INFRA-01 contre iCloud, a relu l'archive INFRA-01 du 25/10 (16 Mo, 20 s :
  conforme, chiffrée `age`) et les dernières archives LINKY-01 et ZWAVE-01
  (70 Mo, environ 30 s chacune : conformes). Les archives HA-01 (450 Mo) n'ont
  pas été relues pour cet essai.
- **Sandbox** : scénario `backup-archive-integrity` (octet altéré sans changer la
  taille, remote illisible, rétablissement) et recette `--full-stack`
  (« Vérifier maintenant » depuis Vision).
- **Planificateur** : une tâche cron à heure fixe ne se déclenche plus deux fois
  dans l'heure répétée du changement d'heure ; HA-01 avait été sauvegardé deux
  fois (00:00 et 01:00 UTC) le 25/10.

## Lot 3 — état de la session iCloud (Agent, Vision, non publié)

Le contrôle horaire de rclone (session ouverte, expirée, injoignable) n'était
publié que vers Home Assistant. Tsunade le conserve maintenant avec la date
depuis laquelle l'état dure :

- **Agent** : règle préventive `icloud_session`. Une session expirée est
  **urgente** (les prochaines sauvegardes échoueront), un iCloud injoignable ou en
  erreur depuis plus de 3 heures est signalé, un relevé de plus de 3 heures n'est
  pas une preuve. L'état est servi avec les restaurations (`icloud`).
- **Vision** : le bloc « Sauvegardes restaurées » affiche la session, la date de
  son dernier contrôle, depuis quand elle est dans cet état et sa dernière
  session valide, avec le chemin de reconnexion.
- **Shizune** : l'alerte apparaît dans la carte « Prévention ».
- **Sandbox** : scénario `preventive-infra-health` et recette `--full-stack`.

## Audit des dix critères

Légende : **Sandbox** = démontré avec de vrais composants hors production ;
**réel** = démontré sur Konoha ; **à faire** = aucun travail ou preuve.

| Critère | État |
| --- | --- |
| Restauration HAOS documentée et vérifiée | à faire : aucune restauration d'une sauvegarde HAOS n'a été déclarée |
| Restauration INFRA-01 documentée et vérifiée | procédure en place (`ohana restore`, guide House) ; la reconstruction après la carte SD du 9 octobre en est une occurrence, à déclarer par l'utilisateur s'il la juge complète |
| Date du dernier test conservée | Sandbox (Agent 1.49.0) ; réel dès la première déclaration |
| Intégrité vérifiable indépendamment de la création | Sandbox (lot 2) ; essai réel en lecture seule le 25/10 sur INFRA-01, LINKY-01 et ZWAVE-01 ; actif après déploiement |
| Sauvegarde jamais testée identifiable | Sandbox (Agent 1.49.0, Vision 1.39.0) ; visible après déploiement |
| Versions nécessaires à la restauration | acquis : le manifeste publié porte la composition Agent/Vision ; non retravaillé |
| Restauration échouée ou incomplète : état explicite | Sandbox : l'état `last_failed` est urgent ; les échecs de `ohana restore` ne sont pas encore enregistrés automatiquement |
| Chiffrement vérifiable sans exposer les secrets | INFRA-01 : en-tête `age` relu avec l'empreinte (lot 2) ; HAOS : chiffrement natif de Home Assistant, non contrôlé |
| Sauvegarde distante réussie seulement si l'archive existe | acquis : taille contrôlée après l'envoi, manifeste publié en dernier ; réel : sept sauvegardes INFRA-01 réussies du 19 au 25/10 |
| État exploitable par Tsunade | Sandbox : règles préventives `backup_restore` et `icloud_session` ; l'état iCloud est aussi lisible dans Vision |

## Lots suivants

1. **Échecs de `ohana restore`** : Installer écrit un compte rendu que l'Agent
   lit et enregistre comme test échoué ou partiel.
2. **Essai réel HAOS** : restaurer une sauvegarde HA-01 sur une instance de
   test. Cet essai appartient à l'utilisateur.
