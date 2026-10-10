# Publication des releases Ohana

Depuis `C:\Users\cedri\Documents\GitHub`, avec `gh` authentifié :

```powershell
& .\Ohana-Agent\.venv\Scripts\python.exe .\Ohana-Platform\scripts\release_all.py
```

Le lancement du script démarre directement le workflow de publication. Il
n’existe ni option `--publish`, ni contournement des validations. Pour limiter
le traitement à un dépôt :

```powershell
& .\Ohana-Agent\.venv\Scripts\python.exe .\Ohana-Platform\scripts\release_all.py --repo agent
```

Dépôts disponibles : `agent`, `vision`, `katsuyu`, `shizune`, `platform` et
`installer`.

## Déroulement

Pour chaque dépôt, le script :

1. récupère les références GitHub et compare `main`, `origin/main` et le
   worktree ;
2. ignore le dépôt s’il n’existe aucun changement local ;
3. s’arrête si le dépôt est en retard ou divergent ;
4. demande si une release doit être créée ;
5. affiche les versions locale et GitHub, puis demande la nouvelle version ;
6. propage cette version dans les sources et tests déclarés ;
7. exécute les validations adaptées au dépôt ;
8. prépare et vérifie les assets ;
9. crée un commit `release: Ohana-Agent 1.26.14` (ou
   `release: compose Platform 1.0.X` pour une composition), pousse `main`, crée le tag
   `v1.26.14` et la release `Ohana-Agent 1.26.14` ;
10. retélécharge tous les assets et vérifie les hashes ainsi que
    `HEAD == origin/main == tag`.

Après une release Agent, Vision ou Shizune, sa nouvelle version est reportée
dans le manifeste Platform local. Le passage Platform crée ensuite une
nouvelle composition avec ces versions, conserve la composition précédente en
historique et synchronise les copies ainsi que les tests d’Installer.

Une réponse négative ignore le dépôt courant. Toute erreur de propagation,
Ruff, pytest, build, Git ou GitHub arrête immédiatement l’ensemble du
processus, avant les opérations suivantes. Les modifications réalisées avant
l’échec restent visibles pour permettre le diagnostic ; le script ne lance
aucun reset automatique.

## Affichage et logs

Le terminal affiche uniquement les questions et une ligne de progression par
dépôt, mise à jour sur place jusqu’au résultat final à 100 %. Les sorties
détaillées sont enregistrées dans
`C:\Users\cedri\Documents\GitHub\.release-logs` avec un fichier par dépôt.

## Contrats d’assets

- Agent : wheel, sdist, tous les `config/**/*.example.yaml` et `SHA256SUMS` ;
- Vision : wheel, sdist, `vision.example.yaml` et `SHA256SUMS` ;
- Installer : wheel, sdist et `SHA256SUMS` ;
- Katsuyu : `KatsuyuSetup.exe` et `SHA256SUMS` ;
- Shizune : archive PWA versionnée et `SHA256SUMS` ;
- Platform : `release-manifest.yaml`, `release-catalog.yaml` et
  `SHA256SUMS`.

Les anciens fichiers présents dans `dist` ne sont jamais transmis.

## Contrôle documentaire sans publication

Depuis la racine du workspace, le contrôle suivant lit les documents des huit
dépôts, leurs liens locaux (y compris les liens GitHub `main` correspondant à
ces dépôts), les exemples YAML/JSON, les continuations Bash, les SVG et les
deux copies du manifeste/catalogue Platform dans Installer :

```powershell
& .\Ohana-Agent\.venv\Scripts\python.exe -B .\Ohana-Platform\scripts\check_documentation.py
```

Il retourne un code non nul en cas d'écart. Il ne lance aucune commande d'un
exemple, ne contacte pas GitHub et ne publie rien. Les liens vers d'autres
sites ou des révisions historiques ne sont pas vérifiés sur le réseau. Une
option `--json chemin` conserve le résultat pour la recette. Ce contrôle
complète la relecture des contrats et procédures ; il ne prouve pas leur
exécution en production.

## Sources versionnées et tests

Les sources communes résident dans `Ohana-Platform/scripts`. Les dépôts Ohana
se placent côte à côte dans le workspace ; le script résout cette racine depuis
son emplacement, indépendamment du terminal courant. Les anciens lanceurs
locaux `scripts/*.py` peuvent déléguer à ces sources sans en conserver une copie.

Les tests de propagation utilisent les fichiers des dépôts locaux et des
répertoires temporaires ; ils simulent les commits et ne publient rien :

```powershell
& .\Ohana-Agent\.venv\Scripts\python.exe -B -m unittest discover `
  -s .\Ohana-Platform\scripts -p test_release_all.py
```
