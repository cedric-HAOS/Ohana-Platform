# Phase 9 — Shikamaru

Audit du 25 octobre 2026. Objectif de la phase : renforcer la **qualité des
observations** plutôt que multiplier les capacités. Shikamaru observe ; il ne
remplace pas Tsunade dans le diagnostic.

Suivi des critères : [ROADMAP](../ROADMAP.md#phase-9--shikamaru).

Légende : **réel** = démontré sur Konoha ; **Sandbox** = démontré avec de vrais
composants hors production ; **ouvert** = pas démontré.

## Constat de départ

Du 9 au 24 octobre, Vision a conservé 88 incidents. Hors la panne de la carte SD du
9 octobre (une soixantaine de présences réseau ouvertes en même temps), les
incidents de fraîcheur de télémétrie dominaient : 11 sur 14 ne duraient qu'un
contrôle (5 minutes, une occurrence). Chacun lançait un contrôle de journaux et une
analyse IA. C'est la mesure qui a guidé le premier lot.

## Audit des neuf critères

| Critère | État et preuve |
| --- | --- |
| Observations assez stables pour être exploitées | ouvert : la télémétrie est stabilisée (ci-dessous) ; la présence réseau de certains appareils (VAC-01 : 6 incidents de 2 à 78 minutes les 13 et 14/10) ne l'est pas encore |
| Faux positifs connus réduits ou documentés | Sandbox : retard de relevé confirmé avant incident ; pause de protection AdGuard répliquée avec quelques secondes d'écart n'est plus une divergence ; réel (25/10) : l'ancienne divergence AdGuard venait de ce faux positif. Documenté : présence réseau d'un appareil qui dort |
| États transitoires distingués des pannes | Sandbox : un retard de relevé est `UNKNOWN` au premier contrôle, `UNHEALTHY` au second ; entité absente = `DEGRADED` pendant 10 minutes (redémarrage de Home Assistant) ; réplication AdGuard en cours = `running`, jamais divergente |
| Âge d'une observation | Sandbox : l'âge de la valeur (`age_seconds`) accompagne chaque relevé de télémétrie et décide du retard ; l'âge du dernier cycle AdGuard et des composants de l'Agent est publié ; réel : `ingestion_lag` et `silence_seconds` dans la vue Ohana |
| Panne du collecteur distinguée de la panne observée | réel (Phase 5) : composants de l'Agent (`agent_components`), sonde de Vision, `unverifiable` AdGuard ; une lecture impossible n'est jamais une panne (`unreadable` des archives, `UNKNOWN` de la télémétrie) |
| Dépendances objectives sans causalité inventée | Sandbox (Phase 4) : dépendances déclarées entre équipements, corrélations « liées sans cause affirmée » |
| Changements d'état historisés | réel : historique des incidents, fiche par équipement et frise de 30 jours dans Vision (Phase 3) ; observations conservées par Vision |
| Charge adaptée à INFRA-01 | réel : Agent environ 2 % d'un cœur, Vision moins de 1 % (29/09) ; 14 000 lignes de journal par jour supprimées (Agent 1.49.0) ; écriture de la nouvelle carte SD 17 à 20 ms, environ 5 Go par jour ; surveillée par la règle `storage_health` |
| Une capacité n'est ajoutée que si elle garantit une fonction utile | acquis : aucune capacité d'observation n'a été ajoutée depuis l'ouverture de la phase ; les ajouts du 25/10 sont des règles de maintenance préventive qui lisent des données existantes |

## Ce qui reste

1. **Présence réseau instable** : appliquer la confirmation de deux contrôles aux
   appareils dont la présence oscille (VAC-01 le 13/10 : 12, 42, 3, 30, 12, 78
   minutes), si l'utilisateur le juge utile. Cela retarde de 5 minutes la détection
   d'une vraie coupure.
2. **Mesurer l'effet réel** de la confirmation de télémétrie après déploiement :
   nombre d'incidents de fraîcheur par semaine (11 sur 14 jours avant).
3. **Phase non close** : les critères 1 et 2 attendent cette mesure.
