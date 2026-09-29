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
| 2 — Fiabilité du Wake-on-LAN | mesure du succès, réveil resté sans réponse, relances, échec explicite | codé, non publié (Agent, Vision) |
| 3 — Reprise et IA indisponible | jobs interrompus, échec explicite, absence de conclusion artificielle | codé, non publié (Agent) |
| 4 — Sandbox, documentation, validations réelles | scénarios, parcours réel avec Bubule | Sandbox et documentation faits ; validations réelles après déploiement |

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

### Lot 2 — fiabilité du Wake-on-LAN

Constat : l'Agent envoyait la rafale de paquets et notait seulement
l'échéance de l'attente. Aucune trace d'un réveil resté sans réponse, aucune
relance, aucune mesure de fiabilité.

**Agent** (`jobs/workers.py`, `api/service.py`) :

- Un réveil dont l'attente (180 s) s'écoule sans connexion écrit
  `wake_timeout` (daté à l'échéance, avec le numéro de tentative). Détecté par
  le passage périodique du planificateur (toutes les 5 s) et à la lecture.
- Tant que du travail attend pour ce worker, un PC resté muet est réveillé de
  nouveau 10 minutes après (`wake_sent`, `trigger: retry`), jusqu'à **trois
  tentatives**. La troisième sans réponse écrit `wake_abandoned` (échec
  explicite) : plus de tentative, les travaux suivent leur propre délai. Le lot
  suivant du lendemain repart à la tentative 1. Sans travail en attente (test
  manuel), aucune relance.
- Une connexion peu après l'échéance (moins de 30 min) est notée `late` : elle
  compte comme réponse tardive, mais Ohana ne possède plus le cycle et
  n'arrête pas le PC. Une connexion bien plus tard est notée `manual` : un PC
  démarré à la main n'est ni une réponse ni arrêté par Ohana.
- `wake_stats` par worker, calculé sur le journal conservé (200 événements) :
  tentatives, à l'heure, en retard, sans réponse, abandons, envois impossibles,
  délai médian et maximal.
- Réglages du service, sans option YAML : `wake_unanswered_retry_seconds`
  (600), `wake_max_unanswered_attempts` (3). Un PC muet reste **informatif** :
  aucun incident ni réparation.

**Vision** : « Fiabilité du réveil » (réveils suivis d'une connexion, médiane,
maximum, retards, sans-réponse, abandons) et, par cycle, les tentatives,
« Réveil abandonné », « Connecté en retard », « PC démarré à la main ».

**Sandbox** : `katsuyu-wake-cycle` étendu : PC muet (tentative initiale puis
deux relances, abandon, pas de quatrième tentative), démarrage manuel tardif
qui exécute le travail en attente sans arrêt, statistiques (5 réveils : 2 à
l'heure, 3 sans réponse, 1 abandon).

### Lot 3 — reprise des jobs interrompus et IA indisponible

Audit : un job dont le worker disparaissait était remis en file indéfiniment,
jusqu'à son délai maximal (jusqu'à plusieurs heures). Un job qui fait tomber le
PC à chaque fois (mémoire, plantage) aurait été rejoué en boucle. Côté IA, le
repli de Tsunade existait déjà (`record_ai_failure` : décision « surveiller »,
statut épistémique `none`, aucune action corrective) mais n'était démontré que
pour un Katsuyu absent, pas pour un runtime IA absent avec un Katsuyu vivant ni
pour un job abandonné.

**Agent** (`jobs/repository.py`) : `max_attempts` (3 par défaut, 1 à 10). Une
interruption remet le job en file (« attempt 1/3 ») ; à la troisième, il passe
en `FAILED` avec `worker.interrupted` et un message lisible. Les travaux IA et
d'investigation abandonnés sont repris par le traitement des résultats
(`completion_processed`) : repli sans conclusion.

**Rien à changer dans Katsuyu.** Un worker redémarré se réinscrit et prend le
travail dès l'expiration du bail ; les handlers déterministes ne dépendent pas
du runtime IA (le runtime absent est déclaré `missing` avec sa cause).

**Sandbox** : `katsuyu-resilience`. Partie A : job IA interrompu trois fois,
échec explicite, repli sans conclusion, aucune réparation ni nouveau job.
Partie B : vrai worker Katsuyu en HTTP, job repris à la tentative 2 après la
disparition de son prédécesseur, travail déterministe exécuté sans runtime IA,
job IA impossible en échec avec sa cause et sans conclusion.

### Lot 4 — Sandbox, documentation, validations

Couverture Sandbox des dix critères (tous les scénarios sont rejoués avant
chaque publication) :

| Critère | Preuve Sandbox |
| --- | --- |
| Bubule optionnel | `katsuyu-unavailable`, `local-diagnosis-worker-unavailable`, `katsuyu-resilience` (traitement déterministe sans runtime IA) |
| Wake-on-LAN fiable | `katsuyu-wake-cycle` (relances, abandon, connexion tardive ou manuelle, statistiques) |
| Worker disponible réutilisé | `katsuyu-wake-cycle` (aucun nouveau réveil) |
| Plusieurs jobs, un cycle | `katsuyu-wake-cycle` (deux jobs, un seul réveil et un seul arrêt) |
| Arrêt selon les conditions | `katsuyu-wake-cycle` (arrêt après file vide, permission consommée) |
| Pas d'arrêt si usage | `katsuyu-wake-cycle` (veto de session) et vraie requête de sessions Windows |
| Job interrompu repris ou échec | `katsuyu-resilience` (reprise à la tentative 2, échec explicite à la 3ᵉ) |
| Déterministe sans IA | `katsuyu-resilience` |
| Pas de conclusion artificielle | `katsuyu-resilience`, `katsuyu-unavailable` |
| Vision explique réveil et exécution | `katsuyu-wake-cycle` (journal) et `ohana-self-supervision` (rendu dans Chromium) |

## Validation réelle (après publication et déploiement)

Déployer l'Agent avant Katsuyu ; Katsuyu 0.13.0 s'installe sur Bubule
(`KatsuyuSetup.exe` ou mise à jour automatique). À faire avec Bubule :

1. **Cycle complet sans session.** Bubule éteint, aucune session ouverte
   après le démarrage : créer du travail (test de réveil depuis Vision, ou
   contrôle des journaux à 05:00) et vérifier dans la vue Ohana le motif, le
   délai de connexion, le travail exécuté et l'arrêt. *(Point d'attention : si Windows
   ouvre automatiquement une session au démarrage (connexion automatique),
   l'arrêt sera toujours refusé et Bubule restera allumé après chaque réveil.
   C'est le comportement demandé — session seulement —, mais à vérifier tôt
   sur Bubule ; désactiver la connexion automatique ou passer à un critère
   d'inactivité serait alors le remède.)*
2. **Veto de session.** Même cycle avec une session ouverte sur Bubule : le PC
   reste allumé, la ligne dit « session Windows ouverte », Katsuyu reste
   disponible et le prochain travail est traité sans nouveau réveil.
3. **Réveil sans réponse.** Débrancher le réseau de Bubule (ou désactiver le
   réveil dans son BIOS) puis demander un contrôle : trois tentatives à dix
   minutes d'écart, puis « Réveil abandonné », aucun incident.
4. **Job interrompu.** Arrêter Katsuyu (ou éteindre Bubule) au milieu d'un
   contrôle : reprise à la tentative suivante ; interrompu trois fois,
   échec `worker.interrupted` visible dans l'activité de Katsuyu.
5. **IA impossible.** Renommer temporairement le modèle IA : le runtime
   passe « absent », un job IA échoue avec sa cause, l'incident reste sous
   surveillance sans conclusion, les contrôles déterministes continuent.
6. **Fiabilité.** Relever « Fiabilité du réveil » après quelques cycles réels
   (réveils suivis d'une connexion, délai médian).

La Phase 6 se clôt quand ces essais sont faits et cochés dans la roadmap.
