# Phase 6 — Katsuyu

## Cadre — 29 septembre 2026

Phase démarrée après la clôture de la Phase 5. Référence :
[roadmap commune](../ROADMAP.md).

Objectif : garder Bubule comme **capacité de calcul optionnelle, robuste et
non critique**. Son extinction n'empêche aucune fonction essentielle de
Konoha ; une IA indisponible ne produit aucune conclusion artificielle ;
Vision explique pourquoi Katsuyu a été réveillé et ce qu'il a exécuté.

### Choix de l'utilisateur (29 septembre)

- **Veto d'arrêt : session Windows seulement.** Katsuyu n'éteint pas un PC sur
  lequel une session est ouverte (console ou bureau à distance, écran
  verrouillé compris). Pas de seuil d'inactivité clavier/souris, pas de
  détection de mise à jour Windows en attente, pas de nouvelle tentative
  d'arrêt : le PC reste allumé, le worker continue à travailler.
- **Ordre des lots** : 1 veto d'arrêt et traçabilité des cycles ; 2 fiabilité
  du Wake-on-LAN ; 3 reprise ou échec explicite des jobs interrompus et IA
  indisponible ; 4 Sandbox, documentation et validations réelles avec Bubule.

### Choix de conception

- **Le veto est local.** Seul Katsuyu voit les sessions Windows de Bubule.
  L'Agent accorde la permission d'arrêt selon la file (inchangé) ; Katsuyu
  peut la refuser. La permission est consommée à l'octroi : après un veto,
  l'Agent ne considère plus le PC comme « réveillé par Ohana », donc ne
  redemande pas l'arrêt à chaque sondage. Un PC laissé allumé est réutilisé
  sans réveil.
- **En cas de doute, le PC reste allumé.** Si les sessions ne peuvent pas être
  lues (`session_check_failed`), il n'y a pas d'arrêt : un PC inactif coûte un
  peu d'électricité, un arrêt inattendu coûte le travail de quelqu'un.
- **Le journal appartient à l'Agent.** Il connaît la file, l'horloge et les
  jobs exécutés ; Katsuyu n'ajoute que ce que lui seul sait (arrêt lancé, veto
  et sa raison). Le rapport est un effort raisonnable : si l'Agent n'est plus
  joignable, l'arrêt (ou le veto) a lieu quand même.
- **Aucun incident, aucune réparation.** Un PC éteint reste normal, comme en
  Phase 5. La Phase 6 explique, elle n'alerte pas.

## Audit des critères de sortie (29 septembre)

| Critère | État avant la Phase 6 | Lot |
| --- | --- | --- |
| Bubule reste optionnel | démontré en réel (Phase 5, Katsuyu arrêté) et en Sandbox (`katsuyu-unavailable`, `local-diagnosis-worker-unavailable`) ; à revalider avec chaque nouveau job | 4 |
| Wake-on-LAN fiable | envoi en rafale (3 paquets) et 2 nouvelles tentatives d'envoi ; aucune mesure du succès réel, aucune trace d'un réveil resté sans réponse | 2 |
| Worker disponible réutilisé | logique en place (`wake_candidate`), tests unitaires ; pas de preuve Sandbox de bout en bout | 1 (`katsuyu-wake-cycle`) |
| Jobs compatibles dans un même cycle | fenêtre de regroupement, tests unitaires | 4 |
| Arrêt selon les conditions prévues | octroi selon la file et `woken_by_ohana` (tests) ; aucune trace de l'issue | 1 |
| Pas d'arrêt si usage ou état bloquant | **absent** : `shutdown /s /t 0` sans vérification | 1 |
| Job interrompu repris ou échec explicite | bail expirant et nouvelle tentative (tests) ; à démontrer de bout en bout | 3 |
| Déterministe sans runtime IA | handlers indépendants ; runtime déclaré par capacité (Phase 5) | 3 |
| Pas de conclusion artificielle sans IA | comportement Phase 1 (`katsuyu-unavailable`) ; à revalider | 3 |
| Vision explique réveil et exécution | **absent** : ni raison du réveil ni historique des cycles | 1 |

## Lots

| Lot | Contenu | État |
| --- | --- | --- |
| 1 — Veto d'arrêt et cycles expliqués | veto de session côté Katsuyu, journal des réveils et arrêts dans l'Agent, lignes « Cycle de réveil » dans la vue Ohana | codé, non publié (Agent, Katsuyu 0.13.0, Vision) |
| 2 — Fiabilité du Wake-on-LAN | mesure du succès, réveil resté sans réponse, relances, échec explicite | à faire |
| 3 — Reprise et IA indisponible | jobs interrompus, échec explicite, absence de conclusion artificielle | à faire |
| 4 — Sandbox, documentation, validations réelles | scénarios, parcours réel avec Bubule | à faire |

### Lot 1 — veto d'arrêt et cycles expliqués

**Katsuyu** (`power.py`, `worker.py`) :

- `signed_in_sessions()` compte les sessions Windows où un utilisateur est
  connecté (`WTSEnumerateSessions` / `WTSQuerySessionInformation`, états
  active, connectée, déconnectée ; session 0 des services et écran de
  connexion exclus). Le worker tourne en SYSTEM : c'est la seule vue fiable.
- `session_shutdown_veto()` : `interactive_session` si au moins une session,
  `session_check_failed` si la lecture échoue, sinon pas de veto.
- Sur `shutdown_requested`, le worker interroge le veto. Veto : pas
  d'arrêt, `shutdown_vetoed` rapporté avec la raison et le nombre de sessions,
  la boucle continue. Sinon `shutdown_started` est rapporté, puis
  `shutdown.exe /s /t 0`.
- Rapport : `POST /v1/jobs/workers/power` ; un Agent antérieur (401/404) est
  ignoré, une erreur réseau n'empêche ni l'arrêt ni le veto.

**Agent** (`jobs/workers.py`, `jobs/schema.py`) — table
`distributed_worker_power_events` (200 événements par worker) :

| Événement | Quand | Détail |
| --- | --- | --- |
| `wake_sent` | Wake-on-LAN envoyé | `trigger` (`queued_jobs` ou `manual`), `pending_jobs` par type, `timeout_seconds` |
| `wake_failed` | envoi impossible | `trigger`, `error` |
| `worker_online` | première inscription après le réveil | `after_seconds` |
| `shutdown_granted` | file compatible vide | `executed` par type, `failed` |
| `shutdown_started` / `shutdown_vetoed` | rapport de Katsuyu | `reason`, `sessions` |

Les redémarrages du worker pendant un réveil ne répètent pas `worker_online`.
`GET /v1/jobs/workers` expose les 30 derniers événements (`power_events`,
heure de Paris).

**Vision** (`ohana.js`, carte Katsuyu) : une ligne « Cycle de réveil » par cycle
(trois derniers) : raison, délai de connexion, travaux exécutés, issue (PC
éteint, PC laissé allumé et pourquoi, sans réponse, réveil non envoyé).

**Sandbox** : `katsuyu-wake-cycle`. Agent HTTP et worker Katsuyu réels ;
Wake-on-LAN, arrêt Windows et sessions injectés, horloge de l'Agent pilotée.
Cycle complet (réveil pour deux jobs, connexion à 64 s, exécution, arrêt
accordé puis lancé), cycle avec session ouverte (pas d'arrêt, raison
journalisée, PC toujours disponible), réutilisation d'un worker disponible
sans nouveau réveil, requête de sessions Windows réelle.

## Validation réelle (après publication et déploiement)

À faire avec Bubule après déploiement de l'Agent puis de Katsuyu 0.13.0 :

1. Bubule éteint, créer du travail (test manuel ou contrôle des journaux),
   laisser l'Agent le réveiller : la ligne « Cycle de réveil » doit montrer
   le motif, le délai et l'arrêt.
2. Même cycle avec une session ouverte sur Bubule : le PC reste allumé, la
   ligne dit « session Windows ouverte ».
3. Vérifier qu'aucun incident ne s'ouvre pendant ces cycles.
