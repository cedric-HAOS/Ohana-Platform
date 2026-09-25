# Ohana Sandbox

Bac à sable d'intégration permettant de valider les comportements
de l'écosystème Ohana directement depuis les checkouts locaux.

Aucune release n'est nécessaire.

Aucun accès à l'infrastructure de production n'est effectué par les
scénarios sauf mention explicite contraire.

## Principe

Le Sandbox utilise directement :

- `../Ohana-Agent/src`
- `../Ohana-Katsuyu` pour `run --exercise-logs`
- et les autres composants nécessaires.

Les bases SQLite et autres données de scénario sont créées dans un
répertoire temporaire supprimé après chaque exécution.

## Pré-requis

Utiliser un environnement Python disposant déjà des dépendances
d'Ohana-Agent.

Par exemple, activer le même environnement virtuel que celui utilisé
pour lancer les tests d'Ohana-Agent.

## Lister les scénarios

```powershell
python .\sandbox\runner.py list
```

## Exécuter les validations locales

Le cycle de travail est : développement sur les checkouts locaux → validation
Sandbox → release → déploiement → vérification du comportement réel.
La publication n'est pas un prérequis à l'exercice des journaux.

```powershell
# Agent + analyseur Katsuyu + traitement Tsunade locaux
.\sandbox\run.ps1 run --exercise-logs

# Scénarios existants et exercice des journaux
.\sandbox\run.ps1 run all --exercise-logs

# Reproduction à partir d'un journal UTF-8 (source ha-01, fenêtre de 24 h)
.\sandbox\run.ps1 run --exercise-logs --logs-file C:\Temp\ha.log --window-end "2026-09-21T12:00:00+02:00"
```

Sans fichier, trois entrées sont exercées : journal sain, anomalie répétée et
collecte tronquée. Le véritable `LogsHealthCheckHandler` de Katsuyu traite une
source locale inline, puis le résultat retourne dans la file Agent et Tsunade.
Le parcours vérifie la projection de données destinée à Vision, les doublons,
la reprise SQLite et l'absence de nouveau contrôle. Les bases sont temporaires.
Le lanceur installe les dépendances Katsuyu dans le venv Sandbox ; `--katsuyu`
permet de sélectionner un autre checkout. Pour une invocation Python directe,
installer au préalable les dépendances des deux dépôts dans cet environnement.

Un fichier est analysé dans une fenêtre de 24 heures se terminant maintenant,
ou à `--window-end` pour un journal historique (fuseau obligatoire). La collecte
est bornée aux 4096 derniers octets. Le résumé affiche le nombre de lignes et
d'anomalies, sans afficher le contenu du journal. PASS indique le bon traitement
du cycle, y compris si Katsuyu trouve des anomalies.

Ce parcours n'exécute pas encore la boucle réseau du worker, un modèle IA ou le
rendu navigateur Vision. Il constitue un socle d'intégration avant release,
à étendre pour couvrir ces composants. Il ne contacte pas INFRA-01.
`post-deploy agent VERSION --exercise-logs` reste le parcours distinct de recette
réelle après déploiement, avec déclenchement d'un travail sur l'infrastructure.

Depuis la racine d'Ohana-Platform :

```powershell
.\sandbox\run.ps1 run all
.\sandbox\run.ps1 run teleinformation-supervisor-cycle
.\sandbox\run.ps1 run followup-restart
.\sandbox\run.ps1 run local-diagnosis-worker-unavailable
.\sandbox\run.ps1 run followup-evidence-cycle
```

Le lanceur initialise `sandbox/.venv` si nécessaire et active le mode UTF-8
de Python pour afficher les résultats dans les terminaux Windows.
Avec un environnement déjà prêt :

```powershell
python -X utf8 .\sandbox\runner.py run all
```

`teleinformation-supervisor-cycle` exerce le cycle Téléinformation `direct_http`
avec des observations et une inspection Supervisor simulées sur LINKY-01. Ses
27 vérifications couvrent l'add-on `teleinfo2mqtt` arrêté : diagnostic `CONFIRMED`
par Supervisor, décision déterministe `investigate` et aucun appel IA.
La preuve Supervisor doit être persistée dans le dossier avant le diagnostic.
Trois observations dont seul l'âge des trames augmente conservent le même diagnostic.
La reprise SQLite conserve intégralement le dossier. Un changement du seuil de
fraîcheur invalide l'analyse ; une réévaluation explicite la confirme à nouveau.
Une observation saine résout le même incident, y compris après une seconde
reprise, sans job IA ni collecte complémentaire. Aucune sonde réelle ni aucun
arrêt/redémarrage d'add-on n'est effectué. Ce scénario ne remplace pas la
requalification de la panne contrôlée sur Konoha après déploiement.

`recurring-log-review` passe trois contrôles quotidiens de HA-01 par le véritable
`LogsHealthCheckHandler` de Katsuyu, avec des horodatages sans fuseau en heure de
Paris comme dans Home Assistant. Il vérifie que ces lignes tombent dans la
fenêtre, qu'un contrôle retrouvant les mêmes anomalies (compteur et date
différents, sans référence comparable) ne relance pas d'expertise, et qu'une
aggravation nette en relance une. La réponse IA est simulée. Rejoué contre
Agent 1.31.0 et Katsuyu 0.8.15, il échoue sur les deux défauts corrigés.

`vision-unavailable` rejoue « Ohana-Vision indisponible » par la santé d'hôte :
le vrai moniteur, le rapporteur, le bus d'événements, le gestionnaire Tsunade,
le magasin d'incidents et l'exécuteur d'investigations traitent un
`ohana-vision.service` inactif (seules les réponses `systemctl` sont simulées).
L'incident est confirmé par la sonde `service.status` sans IA, la répétition ne
relance rien et le retour du service le résout.

`supervised-repair-cycle` rejoue la réparation de référence dnsmasq avec le
véritable exécuteur de l'Agent, dont la demande de redémarrage est écrite dans
un fichier temporaire : proposition automatique après diagnostic confirmé,
report depuis Vision, reprise SQLite, autorisation, vérification Shikamaru et
expérience apprise ; refus depuis Shizune ; échec d'exécution ; vérification
non confirmée dans le délai (réduit à une seconde) ; proposition expirée à la
résolution de l'incident. Aucun service réel n'est redémarré.

Le parcours `--full-stack` clique aussi « Plus tard », « Autoriser depuis
Vision » et « Refuser » dans Vision (Chromium), jusqu'à l'exécuteur dnsmasq de
l'Agent et à la vérification Shikamaru.

`followup-restart` ferme et rouvre les deux bases SQLite puis reconstruit les
services Agent. Il couvre l'expiration pendant l'arrêt et la reprise après un
échec déjà traité : preuves conservées, aucune relance et lectures idempotentes.
Il simule une reconstruction des services, pas un arrêt brutal du processus.

`local-diagnosis-worker-unavailable` conserve une collecte distante en attente,
puis exerce un diagnostic DNS déterministe et son retour sain pendant l'absence
du worker. Les observations et les réponses de sondes sont simulées ; le moteur
Shikamaru et les équipements réels ne sont pas exécutés.

L'horloge accélérée pilote les délais de la file de jobs. Les décisions Agent
utilisent encore l'heure système ; les nouvelles observations du scénario de
diagnostic local sont donc datées à cette même heure, en Europe/Paris.

`followup-evidence-cycle` exerce trois variantes de collecte sans anomalie
reconnue (zéro ligne, 239 lignes, puis collecte tronquée). Il vérifie la
conservation du dossier initial, la fidélité des limites de collecte malgré
un résumé IA contradictoire et l'arrêt après une seule collecte autorisée.
Les résultats reçus en double et la reconstruction des services depuis SQLite
ne créent ni événements supplémentaires ni nouveau travail. Les réponses IA
sont simulées : ce scénario ne mesure pas la qualité d'un modèle réel.
