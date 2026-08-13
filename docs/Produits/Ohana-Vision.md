# Ohana-Vision

Ohana-Vision est l'interface web de supervision et d'administration de la
plateforme Ohana.

## Administration graphique 1.3.0

La section **Configuration** évite toute édition directe de YAML :

- **Baux DHCP** gère la plage dynamique, les options, les réservations et les
  baux actifs ;
- **Architecture** affiche les équipements sur une grille persistante ;
- **Déplacer** modifie les cellules logiques `row` / `column` par
  glisser-déposer ;
- **Relier** crée une liaison en sélectionnant sa source puis sa destination ;
- un clic sur une ligne permet d'en modifier les extrémités, la technologie, le
  sens, le débit et le libellé ;
- un clic sur un équipement donne accès à ses services.

Vision ne reçoit jamais de droit d'écriture direct sur les fichiers système.
Son backend utilise un secret partagé pour appeler l'API locale
d'Ohana-Agent. Agent reste responsable de la validation et des écritures
atomiques.

## Compatibilité

| Vision | Agent minimal | Installer recommandé | Platform |
|---|---|---|---|
| 1.12.0 | 1.13.0 | 1.8.0 | 1.0.51 |
| 1.11.8 | 1.12.7 | 1.7.3 | 1.0.50 |
| 1.11.7 | 1.12.7 | 1.7.3 | 1.0.49 |
| 1.11.7 | 1.12.6 | 1.7.3 | 1.0.48 |
| 1.11.6 | 1.12.5 | 1.7.3 | 1.0.47 |
| 1.10.2 | 1.11.5 | 1.7.0 | 1.0.28 |
| 1.10.1 | 1.11.5 | 1.7.0 | 1.0.27 |
| 1.10.1 | 1.11.3 | 1.6.1 | 1.0.25 |
| 1.10.1 | 1.11.2 | 1.6.1 | 1.0.24 |
| 1.10.0 | 1.11.1 | 1.6.1 | 1.0.23 |
| 1.10.0 | 1.11.0 | 1.5.0 | 1.0.22 |
| 1.10.0 | 1.11.0 | 1.0.13 | 1.0.21 |
| 1.9.0 | 1.10.0 | 1.0.12 | 1.0.20 |
| 1.8.0 | 1.9.0 | 1.0.11 | 1.0.19 |
| 1.7.1 | 1.8.1 | 1.0.10 | 1.0.18 |


## Téléinformation Linky

Ohana-Vision 1.8.0 configure le service Téléinformation du RPI-Linky, les
entités SINSTS, NTARF et EASF01 à EASF06, puis affiche les observations
produites par Agent.


Ohana-Vision 1.9.0 configure le récepteur Téléinformation direct, le compteur et
la source RPI-Linky. Il expose aussi les plages horaires des équipements et
l’état visuel **Suspendu**.


Ohana-Vision 1.10.0 ajoute la page Réseau Agent, la modification IPv4 avec
retour automatique et les actions de confirmation ou restauration.

Ohana-Vision 1.10.1 distingue le type Ethernet de sa capacité et anime les
liaisons selon leur débit déclaré ou négocié. Aucune saturation ni mesure de
trafic n’est estimée.

Ohana-Vision 1.10.2 utilise la même timeline pour la santé des services dans
la carte logique et dans la fiche équipement.

La page Plugins de Vision configure les sauvegardes HAOS : activation globale
et par cible, adresses, heures quotidiennes, TLS, jetons et mots de passe
masqués, connexion iCloud avec 2FA, dossier distant et préparation NVM. Les
valeurs enregistrées ne sont jamais renvoyées par Agent.

Ohana-Vision 1.11.6 distingue explicitement la clé de chiffrement du jeton
Home Assistant, préserve les saisies HAOS pendant la connexion iCloud/2FA,
permet d'appliquer ces réglages sans ressaisir les identifiants Apple et signale
les modifications non appliquées avant un test.

Ohana-Vision 1.11.7 ajoute le déclenchement immédiat depuis la fiche de chaque
équipement HAOS, affiche **Backup in progress** pendant l'exécution et accorde
un délai dédié au démarrage à froid des opérations iCloud.

Ohana-Vision 1.11.8 actualise les états de la topologie sans reconstruire la
carte. Pour ZWAVE-01, une action Home Assistant supprimée reste vide ; la
sauvegarde NVM planifiée dans Z-Wave JS UI avant l'heure HAOS est recommandée.

Ohana-Vision 1.12.0 configure la cible INFRA-01, son destinataire public `age`,
son horaire et sa rétention iCloud, puis permet son déclenchement depuis la
fiche de l'équipement.
