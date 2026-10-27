# Dépannage Ohana

Commencer par des contrôles en lecture seule. Pour chaque symptôme, conserver
la cible, l'heure Europe/Paris, les versions installées, la fenêtre de mesure
et le résultat observé. Les états proposés, autorisés, exécutés et vérifiés
restent distincts. Une erreur historique ne prouve pas une panne actuelle.

## Repères et versions

```bash
sudo systemctl status ohana-agent.service ohana-vision.service --no-pager
sudo journalctl -u ohana-agent.service -u ohana-vision.service -b -n 100 --no-pager
/opt/ohana-agent/venv/bin/ohana-agent --version
/opt/ohana-vision/venv/bin/ohana-vision --version
ohana --version
ohana versions
```

Comparer les versions au manifeste de la composition sélectionnée, selon
[le guide nominal](Installer-Ohana-Platform.md). Ne pas attendre la version
d'un ancien exemple. Écarter les secrets et les URL authentifiées des extraits
partagés ; ne pas afficher les fichiers de jetons, clés ou rclone.

## Index des symptômes

| Symptôme | Premiers contrôles | Preuve attendue et limite |
|---|---|---|
| Vision indisponible | Services, journal Vision, adresse/port configurés | Disponibilité HTTP et vitaux ; Agent peut continuer à observer |
| Observations anciennes ou file de livraison en retard | Dates mesure/ingestion dans Vision, vitaux de livraison Agent, messages de retry | Une livraison restaurée est une reprise, pas la cause du délai |
| Vision ne communique pas avec Agent | `agent.administration_url`, droits du secret partagé, journaux des deux services | API locale accessible avec l'autorisation prévue ; ne pas publier le secret |
| Job en attente ou expiré | État du job, dates, tentative, lease, dernier heartbeat et disponibilité worker dans Vision | Distinguer `WAITING_WORKER`, `RUNNING`, `TIMEOUT`, `FAILED` et traitement du résultat |
| Katsuyu absent ou Wake-on-LAN sans réponse | Dernier enregistrement, cycles de réveil, MAC déclarée, origine du démarrage, menu/logs locaux Katsuyu | `wake_sent` ne prouve pas le réveil ; `worker_online` démontre une connexion |
| Bubule reste allumé | Motif d'arrêt/veto et session Windows dans le cycle | Veto utilisateur attendu ; accord Agent ne prouve pas l'arrêt Windows |
| Shizune ne se synchronise plus | Dernière synchronisation, accès Vision sur LAN/VPN, état de l'association et réseau iPhone | Perte/reprise explicitement datée ; un écran en cache ne prouve pas l'accès Agent |
| Journaux Linky/HAOS hors délai | Source précise, étape du job, délai du client, fenêtre et volume de collecte, état Supervisor | Le minimum INFRA-01 de 45 s ne s'applique pas aux autres sources |
| MQTT indisponible ou résumé ancien | Résolution du broker depuis INFRA-01, port/configuration, logs et date du résumé retenu | `online` et une synthèse récente avec mesure fonctionnelle ; un port ouvert ne suffit pas |
| Téléinformation ancienne | Date des trames, source, port série et état de l'add-on, sorties HTTP/MQTT séparées | Une panne MQTT n'explique pas à elle seule l'arrêt de la sortie HTTP |
| Sauvegarde/iCloud en échec | État iCloud, résultat du job, taille/hash, manifeste distant et permissions rclone | Job de compression réussi et archive complètement publiée sont deux preuves distinctes |
| Réservation DHCP/configuration refusée | Message de validation Agent et logs ; format du nom d'hôte et contrôle dnsmasq | Une validation refusée n'est pas une configuration appliquée |

## Vision et livraison durable

L'observation locale continue en l'absence de Vision. Examiner la synchronisation
de topologie et la livraison séparément. Vision garde le snapshot courant en
mémoire ; Agent le rafraîchit. Une file durable permet le rattrapage, dans ses
limites configurées ; elle ne garantit pas une rétention infinie.
Voir [l'intégration](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/INTEGRATION.md)
et [l'auto-supervision](Phase-5-Ohana-supervise-Ohana.md).

## Jobs, Katsuyu et réveil

Dans Vision, consulter la vue Ohana/Workers et le dossier de l'incident. Lire
l'état courant du job et sa progression datée, puis le cycle worker associé.
Un état terminal technique peut précéder le traitement du résultat par Tsunade ;
vérifier la décision suivante avant de conclure à une résolution.
Un job interrompu peut recevoir une nouvelle tentative : ne pas relancer ou
purger la file pour masquer l'état précédent.

Sur Bubule, l'icône donne la connexion, la dernière activité et l'accès aux logs
dans `C:\ProgramData\Ohana\Katsuyu\logs`. Comparer l'empreinte de confiance et
l'autorisation worker via les interfaces prévues, sans sortir le jeton.
Pour un réveil sans connexion, relever `wake_sent`, `wake_timeout`,
`wake_abandoned` ou `worker_online` et leur délai. Un veto `interactive_session` ou
`session_check_failed` garde le PC allumé ; ne pas contourner cette protection.
Voir [Katsuyu](https://github.com/cedric-HAOS/Ohana-Katsuyu/blob/main/README.md),
[Phase 6](Phase-6-Katsuyu.md) et
[le contrat jobs](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/Administration.md).

## Shizune

Vérifier d'abord Vision sur le même réseau de confiance, puis l'association
dans Configuration → Compagnons. Les données dynamiques ne sont pas garanties
hors ligne ; le service worker statique n'est pas actif en HTTP sur Safari.
Comparer dernière synchronisation, expiration/révocation et résultat d'une
reconnexion. Une nouvelle association modifie une autorisation ; ne l'effectuer
que lorsque le diagnostic la justifie.
Voir [le guide PWA](https://github.com/cedric-HAOS/Ohana-Shizune/blob/main/docs/PWA.md)
et [la recette réelle restant en Phase 7](Phase-7-Shizune.md).

## Collecte des journaux et investigations

« Contrôler les journaux » utilise la fenêtre `window_hours` configurée du
contrôle général. « Approfondir les journaux » correspond à une investigation
ciblée, bornée à deux heures (24 heures après autorisation explicite du bouton
« étendre aux 24 h précédentes » d'un dossier terminé). Ces actions créent des jobs et peuvent alimenter
des incidents : ce ne sont pas les premiers contrôles passifs de ce guide.

Depuis Katsuyu 0.13.2, seule la source `infra-01` attend au moins 45 secondes,
afin de couvrir la lecture système Agent bornée à 30 secondes. Pour Linky,
identifier l'accès Supervisor, le délai HTTP et le volume demandé ; ne pas
attribuer son échec à ce correctif INFRA-01 sans preuve. Distinguer horodatage
de collecte, date des lignes, lignes correspondantes, anomalies et troncature.
Une collecte vide ou `findings=[]` ne prouve pas la résolution d'un incident.
Voir [le cycle journaux](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/tsunade-worker-cycle.md),
[les investigations bornées](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/read-only-investigations.md)
et [le dossier Tsunade](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/docs/tsunade-priorities.md).

## MQTT, HAOS et Téléinformation

Lire les logs sur la cible qui porte le service et les mesures depuis INFRA-01.
Une connexion testée depuis INFRA-01 ne prouve pas un accès depuis HA-01.
Contrôler séparément le broker HA-01, les trames directes LINKY-01 vers Agent
et la publication MQTT. Utiliser les vues Supervisor pour l'état des add-ons
et du matériel série sans ouvrir le port série déjà utilisé.
Voir [teleinfo2mqtt](https://github.com/cedric-HAOS/Ohana-hassio-addons/blob/main/teleinfo2mqtt/DOCS.md)
et [les contrats MQTT](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/Protocols/MQTT-Convention.md).

## iCloud, restauration et mise à jour défaillante

Vérifier `rclone.conf` sans lire son contenu : propriétaire
`ohana-agent:ohana-agent`, mode `600`, lisible et modifiable par Agent. Une
session expirée exige la reconnexion iCloud/2FA via Vision ; une lecture distante
réussie ne démontre pas tous les renouvellements futurs. Suivre le résultat de
la prochaine sauvegarde et la publication du manifeste final.

En cas d'échec de mise à jour, conserver le message, les versions installées et
l'étape du plan échouée. Avant toute action, vérifier la sauvegarde et le
périmètre de restauration. Une rétrogradation peut rencontrer des schémas plus
récents ; ne pas la présenter comme un retour arrière universel.
Les actions `ohana update`, `ohana restore` et reconnexion sont des opérations
distinctes à préparer selon [Operations](Operations.md),
[le guide Installer](https://github.com/cedric-HAOS/Ohana-Installer/blob/main/docs/Installation.md)
et [Restaurer INFRA-01](https://github.com/cedric-HAOS/Ohana-House/blob/main/docs/INFRA-01/Sauvegarde/Restaurer-INFRA-01.md).

## DHCP et validation des configurations

Les noms DNS refusent les espaces et `_` ; utiliser un tiret. Agent valide le
document avant écriture et applique le contrôle dnsmasq configuré. Lire le
détail du refus dans Vision et le journal Agent. Pour une composition introuvable,
comparer la version/couple demandé à `ohana versions` : les combinaisons absentes
du catalogue sont volontairement refusées.
