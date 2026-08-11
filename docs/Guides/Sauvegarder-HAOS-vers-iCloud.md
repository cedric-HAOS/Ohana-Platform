# Sauvegarder les HAOS vers iCloud

La composition Platform 1.0.48 associe Ohana-Agent 1.12.6 et Ohana-Vision
1.11.7 pour protéger HA-01, LINKY-01 et ZWAVE-01.

Agent demande une sauvegarde complète et chiffrée à chaque HAOS, la transmet
directement à iCloud avec rclone et publie une somme SHA-256. L'archive ne doit
jamais être stockée sur la carte microSD d'INFRA-01 : les tampons rclone restent
sur `/run`, qui doit être monté en `tmpfs`.

## Garanties de conservation

- une sauvegarde Ohana reste conservée localement sur chaque HAOS ;
- l'ancienne sauvegarde locale n'est supprimée qu'après validation distante de
  la nouvelle archive et de son fichier `.sha256` ;
- les sauvegardes manuelles ne sont jamais supprimées ;
- un échec HAOS, réseau, rclone, iCloud ou checksum conserve l'ancienne copie ;
- le test lancé depuis Vision est en lecture seule.

## Préparer INFRA-01

Ohana-Installer installe automatiquement une version de rclone dont l'archive
officielle et la somme SHA-256 sont épinglées. Cette version contient le backend
`iclouddrive`. Aucune commande rclone manuelle ni création préalable de
`rclone.conf` n'est nécessaire.

Les jetons sont des jetons d'accès longue durée créés par des administrateurs
Home Assistant. Les mots de passe de chiffrement des sauvegardes doivent aussi
être conservés hors d'INFRA-01 dans le gestionnaire de mots de passe et la
procédure de reconstruction.

## Configurer depuis Vision

Ouvrir **Configuration → Plugins → Sauvegardes HAOS**.

Dans **Connexion iCloud** :

1. saisir l'identifiant Apple et le mot de passe Apple normal ;
2. approuver la demande sur un appareil de confiance ;
3. saisir le code 2FA dans Vision ;
4. choisir le dossier, par défaut `Ohana/Backups`.

Les mots de passe spécifiques aux applications Apple ne sont pas acceptés par
rclone. Le jeton de confiance doit être renouvelé périodiquement avec le bouton
**Reconnecter iCloud**.

Pour chaque cible HAOS :

1. renseigner une URL complète, par exemple
   `http://ha-01.ohana.lan:8123` ;
2. choisir l'heure quotidienne et le délai maximal ;
3. conserver la vérification TLS pour les URL HTTPS ;
4. saisir directement le jeton Home Assistant et la clé de chiffrement des
   sauvegardes dans les champs masqués ; cette clé est disponible dans
   **Home Assistant → Paramètres → Système → Sauvegardes** ; laisser un
   champ vide conserve la valeur déjà enregistrée ;
5. pour ZWAVE-01, valider le script `script.ohana_backup_zwave_nvm`, qui doit
   attendre la fin réelle de l'export NVM.

Agent protège les secrets enregistrés, ne renvoie jamais leur valeur à Vision
et applique la nouvelle planification dès la confirmation du formulaire.
L'ancien fichier `backup.env` reste accepté uniquement pour migration.

Les champs Apple ne sont pas requis pour appliquer les réglages HAOS. Après
toute modification, cliquer sur **Appliquer** avant **Tester maintenant** ;
Vision signale explicitement une configuration non encore appliquée.

## Déclencher une sauvegarde immédiatement

Dans la vue d'ensemble, ouvrir la fiche de l'équipement HAOS puis utiliser le
bouton **Sauvegarder** placé en haut de la carte. Il n'apparaît que lorsque le
plugin et la cible correspondante sont activés. La correspondance utilise
l'identifiant technique exact : la fiche HA-01 (`ha-01`) lance exclusivement
la cible `ha-01`, et il en va de même pour LINKY-01 et ZWAVE-01.

Après confirmation, Vision indique que la sauvegarde a démarré en arrière-plan.
Le bouton est alors remplacé par **Backup in progress** jusqu'à la fin réelle
de la tâche Agent, ce qui interdit les clics multiples même après avoir fermé
et rouvert la fiche.
Agent poursuit alors le même flux que pour la planification quotidienne :
création complète et chiffrée, envoi iCloud, validation distante, puis rotation
locale. Une demande ne contourne aucune garantie de conservation et une cible
déjà en cours ne peut pas être relancée simultanément.

## Activer progressivement

1. laisser le plugin globalement désactivé pendant la préparation ;
2. utiliser **Tester maintenant** pour vérifier les accès sans écriture ;
3. activer HA-01 seul et contrôler l'archive, le SHA-256 et une restauration ;
4. activer LINKY-01 et répéter la validation ;
5. valider l'export NVM puis activer ZWAVE-01 ;
6. vérifier qu'une seule sauvegarde Ohana récente reste sur chaque HAOS.

Le déploiement de Platform n'active aucune sauvegarde automatiquement. Il
installe uniquement le plugin et sa configuration désactivée.
