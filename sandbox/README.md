# Ohana Sandbox

Bac à sable d'intégration permettant de valider les comportements
de l'écosystème Ohana directement depuis les checkouts locaux.

Aucune release n'est nécessaire.

Aucun accès à l'infrastructure de production n'est effectué par les
scénarios sauf mention explicite contraire.

## Principe

Le Sandbox utilise directement :

- `../Ohana-Agent/src`
- puis, ultérieurement, `../Ohana-Katsuyu`
- et les autres composants nécessaires.

Les bases SQLite et autres données de scénario sont créées dans un
répertoire temporaire supprimé après chaque exécution.

## Pré-requis

Utiliser un environnement Python disposant déjà des dépendances
d'Ohana-Agent.

Par exemple, activer le même environnement virtuel que celui utilisé
pour lancer les tests d'Ohana-Agent.

## Lister les scénarios

```powershell
python .\sandbox\runner.py list