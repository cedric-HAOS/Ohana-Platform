# Exploitation de la plateforme

## Mise à jour

Ohana-Installer télécharge le catalogue de la dernière release stable
d'Ohana-Platform, sélectionne la composition demandée et compare
les versions installées au manifeste :

```bash
sudo ohana update
```

Un composant déjà à la version cible est conservé sans téléchargement, arrêt ni
réinstallation. Ohana-Installer lui-même se met à jour séparément.

## Administration

Ouvrir `http://ADRESSE_DU_SERVEUR:8000`, puis **Configuration**.

- utiliser **Réseau Agent** pour consulter l’interface d’INFRA-01 et appliquer
  une nouvelle configuration IPv4 avec retour automatique ;
- utiliser **Baux DHCP** pour le serveur dnsmasq ;
- utiliser **Architecture > Déplacer** pour organiser la grille ;
- utiliser **Architecture > Relier** pour créer les connexions ;
- cliquer sur un équipement pour gérer ses services ;
- cliquer sur une ligne pour éditer la liaison.

Les modifications ne deviennent persistantes qu'après confirmation de
l'application. Les journaux utiles sont :

```bash
sudo journalctl -u ohana-agent.service -n 100 --no-pager
sudo journalctl -u ohana-vision.service -n 100 --no-pager
```


### Modification réseau sécurisée

Lors d’une modification de l’adresse d’INFRA-01, Agent sauvegarde la connexion
NetworkManager actuelle et programme sa restauration. Après reconnexion à la
nouvelle adresse, confirmer la transaction dans Vision. Sans confirmation dans
le délai choisi, l’ancienne adresse est restaurée automatiquement.

La première adresse statique peut être provisionnée pendant l’installation :

```bash
sudo ohana install --yes \
  --network-interface eth0 \
  --network-address 192.168.1.10/24 \
  --network-gateway 192.168.1.1 \
  --network-dns 192.168.1.11 \
  --network-dns 192.168.1.12
```


## Sauvegardes HAOS

La page **Configuration → Plugins → Sauvegardes HAOS** règle l'activation, les
adresses et les heures quotidiennes des trois HAOS. Les secrets restent dans
`/etc/ohana-agent/backup.env` et le diagnostic immédiat est en lecture seule.

La préparation de rclone, la protection de la carte microSD et la validation
progressive sont décrites dans
[Sauvegarder les HAOS vers iCloud](Guides/Sauvegarder-HAOS-vers-iCloud.md).

## Sélection d’une composition

```bash
ohana versions
sudo ohana install --platform-version 1.0.20
```

Chaque entrée du catalogue pointe vers le manifeste immuable de sa propre release
Platform. Un couple absent du catalogue n’est pas installable.
