# Sauvegarder les HAOS vers iCloud

La composition Platform 1.0.44 associe Ohana-Agent 1.12.4 et Ohana-Vision
1.11.3 pour protéger HA-01, LINKY-01 et ZWAVE-01.

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

Installer et configurer rclone avec un remote nommé `icloud`, puis placer sa
configuration dans `/etc/ohana-agent/rclone.conf` avec le propriétaire
`root:ohana-agent` et le mode `0640`.

Créer `/etc/ohana-agent/backup.env` avec les six secrets :

```text
OHANA_BACKUP_HA_01_TOKEN=...
OHANA_BACKUP_HA_01_PASSWORD=...
OHANA_BACKUP_LINKY_01_TOKEN=...
OHANA_BACKUP_LINKY_01_PASSWORD=...
OHANA_BACKUP_ZWAVE_01_TOKEN=...
OHANA_BACKUP_ZWAVE_01_PASSWORD=...
```

Les jetons sont des jetons d'accès longue durée d'administrateurs Home
Assistant. Les mots de passe chiffrent les sauvegardes et doivent également
être conservés hors d'INFRA-01 dans la procédure de reconstruction.

```bash
sudo chown root:ohana-agent /etc/ohana-agent/backup.env \
  /etc/ohana-agent/rclone.conf
sudo chmod 0640 /etc/ohana-agent/backup.env \
  /etc/ohana-agent/rclone.conf
sudo -u ohana-agent rclone lsd \
  --config /etc/ohana-agent/rclone.conf icloud:
```

## Configurer depuis Vision

Ouvrir **Configuration → Plugins → Sauvegardes HAOS**. Pour chaque cible :

1. renseigner une URL complète, par exemple
   `http://ha-01.ohana.lan:8123` ;
2. choisir l'heure quotidienne et le délai maximal ;
3. conserver la vérification TLS pour les URL HTTPS ;
4. vérifier que Vision indique le jeton et le mot de passe comme présents ;
5. pour ZWAVE-01, valider le script `script.ohana_backup_zwave_nvm`, qui doit
   attendre la fin réelle de l'export NVM.

La destination par défaut est `icloud:Ohana/Backups`. Agent reste propriétaire
du YAML et applique la nouvelle planification dès la confirmation du formulaire.

## Activer progressivement

1. laisser le plugin globalement désactivé pendant la préparation ;
2. utiliser **Tester maintenant** pour vérifier les accès sans écriture ;
3. activer HA-01 seul et contrôler l'archive, le SHA-256 et une restauration ;
4. activer LINKY-01 et répéter la validation ;
5. valider l'export NVM puis activer ZWAVE-01 ;
6. vérifier qu'une seule sauvegarde Ohana récente reste sur chaque HAOS.

Le déploiement de Platform n'active aucune sauvegarde automatiquement. Il
installe uniquement le plugin et sa configuration désactivée.
