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
| 1.7.0 | 1.8.0 | 1.0.8 | 1.0.16 |


## Téléinformation Linky

Ohana-Vision 1.7.0 configure le service Téléinformation du RPI-Linky, les
entités SINSTS, NTARF et EASF01 à EASF06, puis affiche les observations
produites par Agent.
