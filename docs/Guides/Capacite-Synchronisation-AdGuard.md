# Capacité de synchronisation AdGuard gérée par Installer

Platform 1.0.144 compose Agent 1.47.0, Vision 1.38.0 et Shizune 0.5.0.
Installer **1.16.0** est nécessaire pour provisionner cette capacité.
La commande `ohana update` met d’abord Installer à jour avant la composition.

Le profil INFRA-01 déclare `adguard-sync` en activation explicite. Installer
prépare le moteur officiel 0.9.4 avec vérification SHA-256, la configuration,
le service et le timer. Les fichiers et unités existants sont conservés ;
une installation neuve reste inactive.

Dans Vision, ouvrir **Configuration → Plugins → Synchronisation AdGuard** :
configurer et vérifier les accès, puis activer le moteur. Activer séparément
la surveillance pour obtenir le résultat dans les services essentiels Shizune.
Les mots de passe existants sont masqués et conservés lorsqu’un champ reste vide.

L’archive INFRA-01 inclut la configuration et le choix durable d’activation.
Installer reconstruit les unités et le binaire ; il restaure un choix actif
uniquement après validation des deux API. Une ancienne sauvegarde sans ce choix
reste inactive. DHCP conserve son activation explicite indépendante.

Voir [le guide Installer](https://github.com/cedric-HAOS/Ohana-Installer/blob/main/docs/AdGuard-Sync.md)
pour les commandes, les permissions, la conservation et le retour arrière.
La publication ne confirme pas le déploiement sur INFRA-01.
