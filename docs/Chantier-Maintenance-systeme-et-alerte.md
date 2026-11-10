# Chantier — Maintenance du système et alerte indépendante

Ouvert le 04/11/2026 à la demande de l'utilisateur, après un tour d'horizon de
ce qui manque à l'univers Ohana. Quatre axes retenus : l'alerte indépendante
d'INFRA-01 (1), les échéances périmables (4), la simplification (6) et une page
Vision « Mise à jour système ». Le point 5 (énergie Linky/Tempo) a été écarté
par l'utilisateur.

## Constat du 04/11/2026 sur INFRA-01

Lecture seule par ssh (Debian 13 « trixie », noyau 6.18.50+rpt-rpi-v8, démarré
depuis 3 semaines) :

- aucun paquet `unattended-upgrades` ; aucun fichier
  `/etc/apt/apt.conf.d/10periodic` ni `20auto-upgrades` ;
- les minuteurs `apt-daily` et `apt-daily-upgrade` tournent, mais sans
  `APT::Periodic::Update-Package-Lists` ils ne font rien ;
- les listes de paquets datent du 09/10 (installation sur la nouvelle carte SD) ;
  `apt list --upgradable` répond donc **0** alors que l'état réel est inconnu ;
- dernière opération apt : installation de `dnsutils` le 09/10 ;
- pas de `reboot-required`.

Le système n'est donc pas maintenu à jour, et rien ne le signale.

## Décisions de l'utilisateur

- Page « Mise à jour système » : **statut + bouton confirmé** (pas de mise à jour
  automatique, aucun redémarrage automatique).
- Alerte indépendante : **HA-01 + application Home Assistant de l'iPhone**
  (HA-01 est une autre machine ; aucun service externe).
- Point 5 : abandonné.

## Lots

### Lot 1 — lecture (publié : Agent 1.54.0, Vision 1.43.0)

- Agent : `ohana_agent/host/system_updates.py`, `GET /v1/system/updates`,
  opération `system.updates.read`. Lecture sans privilège : `apt-get -s` simule,
  les autres faits sont des fichiers publics de Debian. Verdicts : `up_to_date`,
  `updates_available`, `security_updates`, `reboot_required`, `stale_lists`.
- Vision : vue « Mise à jour système » (`system_updates.js`), route
  `/api/administration/agent/system-updates`.
- Tests : Agent 2110 réussis, Vision 949 réussis, aperçu navigateur vérifié sur
  une réponse simulée. Sandbox pas encore étendue.

### Lot 2 — actions (publié : Agent 1.54.0, Installer 1.18.0, Vision 1.43.0)

Première mise à jour du système d'INFRA-01 réalisée, selon la déclaration de
l'utilisateur du 10/11/2026 ; relevé (paquets, noyau, redémarrage) à consigner.
Le texte ci-dessous est celui de l'écriture du lot, le 04/11.

Le privilège root ne revient jamais à l'Agent : même modèle que
`ohana-chrony-restart` (demande dans `/run/ohana-agent`, unité de chemin, service
`oneshot` root de l'Installer), avec **deux assistants distincts** pour que la
demande n'ait rien à décider.

- Installer : `ohana-system-refresh` (`apt-get update`) et `ohana-system-upgrade`
  (`apt-get -y --with-new-pkgs`, `--force-confold`, jamais `dist-upgrade`, jamais
  de redémarrage), chacun avec son unité de chemin. Provisionnés si l'Agent est en
  1.54.0 ou plus et qu'`apt-get` existe. `/etc/apt/apt.conf.d/20ohana-lists`
  rafraîchit les listes chaque jour (sans mise à jour automatique des paquets).
- Agent : `SystemUpdateRequester` (écrit la demande, lit l'avancement par
  `systemctl show`), `POST /v1/system/updates/refresh|apply`. Refus si les listes
  sont périmées ou si rien n'est en attente ; demande ignorée (`busy`) si un
  assistant tourne déjà (verrou apt).
- Vision : boutons « Actualiser les listes » et « Mettre à jour », confirmation
  avant l'installation, avancement suivi toutes les 4 s.
- Pas de garde sur les incidents critiques ni sur les sauvegardes en cours : la
  question restait ouverte, le verrou apt et la confirmation de l'utilisateur sont
  les seules protections.
- Tests : Agent, Installer (375) et Vision (951) verts. Pas encore de scénario
  Sandbox ; à écrire avant la release. Rien n'a été exécuté sur INFRA-01 : les
  assistants n'existent qu'après `ohana update` avec l'Installer livré.
- Après déploiement : lancer « Actualiser » (premier vrai `apt-get update`), relire
  la liste, puis « Mettre à jour » avec les correctifs de sécurité en tête. Un
  nouveau noyau demande un redémarrage manuel d'INFRA-01 (jamais automatique).

### Lot 3 — échéances périmables (point 4) (publié : Agent 1.54.0)

Trois règles préventives de la Phase 4 (Agent, `tsunade/preventive_expiry.py`),
sans incident ni réparation. Un échantillonneur d'arrière-plan (30 minutes)
garde le dernier relevé du jour par source (`record_snapshot`) ; les règles ne
lisent que ces relevés. L'ancienneté est le nombre de jours consécutifs de
relevés, donc installer les mises à jour la remet à zéro.

| Règle | Source | Seuils |
|---|---|---|
| `system_updates` | simulation apt (lot 1) | sécurité en attente depuis 7 j (urgent 14 j) ; redémarrage requis depuis 7 j ; listes périmées aussitôt |
| `tls_certificates` | sonde TLS d'Ohana-Bank (`127.0.0.1:443`, `bank.ohana.lan`) et fichiers du listener et de la CA Ohana | expire sous 30 j (urgent 7 j ou expiré) |
| `ha_updates` | entités `update.*` à `on` dans `/api/states` (accès du plugin de télémétrie) | proposée depuis 14 j |

- Constats du 04/11 : certificat de Bank valable jusqu'au 21/01/2029, certificat
  du listener Agent jusqu'au 22/11/2028 ; rien ne sera signalé avant fin 2028.
- Aucun listener de l'Agent n'est sondé (bruit de journal) : ses certificats sont
  lus dans leurs fichiers.
- iCloud : la règle `icloud_session` existe déjà (alerte dès la session expirée).
  Elle ne prévient pas avant l'expiration, que rclone ne publie pas ; non traité.
- Tests : 14 nouveaux (règles, sonde TLS locale, échantillonneur, mises en
  sourdine). Vision affiche les règles et leurs constats sans modification.
- Pas de scénario Sandbox pour ces règles : à écrire avant la release.

### Lot 4 — alerte indépendante d'INFRA-01 (point 1) (installé sur HA-01)

Paquet installé sur HA-01 et essai de panne réalisé, selon la déclaration de
l'utilisateur du 10/11/2026.
Le texte ci-dessous est celui de l'écriture du lot, le 04/11.

- Ohana-House : `config/home-assistant/ohana-veille.yaml` (paquet HA) et
  `docs/home-assistant/Veille-Ohana.md`. HA-01 interroge
  `http://192.168.1.10:8000/api/runtime/vitals` (adresse IP, pas de DNS, sans
  authentification, vérifié en lecture seule le 04/11) et en tire deux capteurs :
  Vision en service, Agent actif vu par Vision. Une notification `mobile_app` part
  si l'un est `off` ou `unavailable` 5 minutes, si
  `sensor.ohana_platform_alertes_actives` dépasse 0 pendant 10 minutes ou reste
  `unavailable` 10 minutes. Une étiquette unique remplace la notification, et le
  retour à la normale la retire.
- Tests : `tests/home-assistant/test_ohana_veille.py` (structure, déclencheurs,
  rendu du texte de l'alerte avec jinja2, à lancer avec un interpréteur qui a
  `pyyaml` et `jinja2`, par exemple `.esphome-esp03-venv`). Non validé dans Home
  Assistant lui-même.
- À faire par l'utilisateur : copier le paquet sur HA-01, choisir le service
  `notify.mobile_app_*` de l'iPhone, redémarrer HA, puis l'essai réel (arrêt de
  Vision puis de l'Agent, procédure dans le document).

### Lot 5 — simplification (point 6) (fait : rapport rendu)

Audit sans suppression : [Audit-Simplification-2026-11.md](Audit-Simplification-2026-11.md).
Principaux constats : bruit d'incidents concentré sur quelques sources (DNS de
LINKY-01 en tête), fuite mémoire de l'Agent (+10,9 Mo par jour) toujours non
résolue, grosses classes (`service.py`, `incidents.js`), code de compatibilité à
confirmer avant retrait, base de la roadmap périmée. L'utilisateur tranche
chaque point.
