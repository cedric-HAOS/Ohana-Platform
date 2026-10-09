# Reconstruction INFRA-01 et réplication DNS des réservations DHCP

La composition Platform 1.0.140 fournit Agent 1.45.0, Vision 1.36.0 et Shizune
0.5.0. Elle ajoute la commande `ohana-agent-adguard-reservations` sans activer
automatiquement les unités de synchronisation ou le DHCP.

Les seuls noms des réservations DHCP `ohana.lan` sont publiés sur ZWAVE-01 ; le
service existant `adguardhome-sync` les réplique ensuite vers LINKY-01. ESP-03
reste le futur DHCP de secours ESPHome et conserve ses températures piscine.

## Restauration de l'ancienne sauvegarde

Le restaurateur réinstalle les versions exactes présentes dans le manifeste de
la sauvegarde. Il faut donc restaurer avant de mettre à jour vers Platform
1.0.140. Cette évolution ne modifie ni le format des archives ni la liste des
fichiers requis pour restaurer une sauvegarde ancienne. Le DHCP reste désactivé
à l'issue de la restauration jusqu'à sa réactivation explicite.

Le nouveau fichier de configuration AdGuard et son registre sont placés sous
`/etc/ohana-agent`, déjà sauvegardé et autorisé à la restauration. Ils seront
présents dans les prochaines archives, pas ajoutés rétroactivement aux anciennes.

Après restauration, exécuter `ohana update --platform-version 1.0.140`, contrôler
les réservations, vérifier les adresses réelles et renseigner les identifiants
AdGuard avant d'installer et d'activer le timer.

Les modèles, la prévisualisation, les requêtes DNS et le retour arrière sont
décrits dans [Ohana-House 2.2.0](https://github.com/cedric-HAOS/Ohana-House/blob/v2.2.0/docs/INFRA-01/Capacites/DNS/Synchroniser-Reservations-DHCP.md).
La publication de cette composition ne constitue pas une installation ou une
validation DNS en production sur INFRA-01.
