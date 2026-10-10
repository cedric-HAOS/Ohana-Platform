# Supervision de la synchronisation AdGuard

Disponible avec Platform 1.0.145 : Agent 1.48.0, Vision 1.38.1 et Shizune 0.5.0.

## Après la mise à jour

1. Dans Vision, ouvrir **Configuration → Plugins → Synchronisation AdGuard**.
2. Activer la surveillance ; régler l’intervalle, le délai API et l’âge maximal
   du cycle.
3. Enregistrer puis tester ; vérifier le résultat des contrôles.
4. Dans Shizune, vérifier **Services essentiels → Synchro AdGuard**.

Le service local est préparé automatiquement au démarrage de production d’Agent
avec l’administration activée. L’Installer distribue le modèle désactivé et
préserve les fichiers existants ; Vision peut créer un fichier absent.
Les unités `adguardhome-sync.service` et son timer, ainsi que leurs accès dans
`/etc/ohana-agent/adguardhome-sync.yaml`, doivent déjà être installés et lisibles
par `ohana-agent`. Aucun mot de passe n’est saisi dans le formulaire du plugin.

## Résultat

La santé vérifiée exige un cycle récent réussi et des sections répliquées identiques.
La disponibilité DNS relève du plugin DNS. Un cycle en cours diffère la comparaison.
Une configuration incompatible ou illisible donne un résultat inconnu. Shizune
présente une surveillance désactivée, une mesure absente ou de plus de quinze
minutes comme non vérifiée. Le plugin ne synchronise ni ne répare automatiquement.
Lorsque la synchronisation est saine et la fin du cycle connue, la tuile
affiche son âge : **Dernière synchro il y a 3 min**. La mesure correspond
à la fin du dernier cycle réussi, même lorsqu’aucun paramètre n’a changé.

Les tests locaux utilisent des API et unités simulées ; la publication ne vaut
pas confirmation du déploiement ni preuve de synchronisation réelle.
Le [guide Agent](https://github.com/cedric-HAOS/Ohana-Agent/blob/main/docs/adguard-sync-supervision.md)
détaille les sections comparées et les limites. Le
[guide Vision](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/docs/Administration.md)
décrit l’administration ; le
[guide Shizune](https://github.com/cedric-HAOS/Ohana-Shizune/blob/main/docs/PWA.md)
décrit la tuile.

## Gestion complète depuis Platform 1.0.144

Installer 1.16.0 installe et reconstruit désormais le moteur et les unités.
Agent 1.47.0 et Vision 1.38.0 permettent de configurer les accès et d’activer
le moteur depuis cette même fiche, séparément de la surveillance. Le choix
d’activation est sauvegardé et restauré après validation. Voir
[la capacité gérée par Installer](Capacite-Synchronisation-AdGuard.md).
