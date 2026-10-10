# Supervision de la synchronisation AdGuard

Disponible avec Platform 1.0.142 : Agent 1.46.0, Vision 1.37.0 et Shizune 0.5.0.

## Après la mise à jour

1. Dans Vision, ouvrir **Configuration → Plugins → Synchronisation AdGuard**.
2. Activer la surveillance ; régler l’intervalle, le délai API/DNS, l’âge maximal
   du cycle et le nom DNS stable à résoudre par les deux instances.
3. Enregistrer puis tester ; vérifier le résultat des contrôles.
4. Dans Shizune, vérifier **Services essentiels → Synchro AdGuard**.

Le service local est préparé automatiquement au démarrage de production d’Agent
avec l’administration activée. L’Installer distribue le modèle désactivé et
préserve les fichiers existants ; Vision peut créer un fichier absent.
Les unités `adguardhome-sync.service` et son timer, ainsi que leurs accès dans
`/etc/ohana-agent/adguardhome-sync.yaml`, doivent déjà être installés et lisibles
par `ohana-agent`. Aucun mot de passe n’est saisi dans le formulaire du plugin.

## Résultat

La santé vérifiée exige un cycle récent réussi, des sections répliquées identiques
et un DNS fonctionnel sur les deux IP. Un cycle en cours diffère la comparaison.
Une configuration incompatible ou illisible donne un résultat inconnu. Shizune
présente une surveillance désactivée, une mesure absente ou de plus de quinze
minutes comme non vérifiée. Le plugin ne synchronise ni ne répare automatiquement.

Les tests locaux utilisent des API et unités simulées ; la publication ne vaut
pas confirmation du déploiement ni preuve de synchronisation réelle.
Le [guide Agent](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/adguard-sync-supervision.md)
détaille les sections comparées et les limites. Le
[guide Vision](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/docs/Administration.md)
décrit l’administration ; le
[guide Shizune](https://github.com/cedric-HAOS/Ohana-Shizune/blob/main/docs/PWA.md)
décrit la tuile.
