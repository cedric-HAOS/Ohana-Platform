# Installer Ohana-Vision

Ce guide décrit l'installation d'**Ohana-Vision** en environnement de développement.

À l'issue de cette procédure, vous disposerez d'une interface web fonctionnelle permettant de visualiser l'état de santé d'une infrastructure, les observations, la timeline et la topologie en temps réel.

---

# Prérequis

Les versions suivantes sont recommandées.

| Logiciel | Version recommandée |
| -------- | ------------------- |
| Git      | 2.45+               |
| Python   | 3.13+               |
| pip      | Dernière version    |

Vérifier les versions installées :

```bash
git --version

python --version

pip --version
```

---

# Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/cedric-HAOS/Ohana-Vision.git

cd Ohana-Vision
```

Vérifier le contenu du dépôt :

```text
config/
src/
tests/
pyproject.toml
README.md
```

---

# Étape 2 — Créer un environnement virtuel

Créer l'environnement Python :

```bash
python -m venv .venv
```

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux

```bash
source .venv/bin/activate
```

Vérifier :

```bash
python --version

pip --version
```

---

# Étape 3 — Installer les dépendances

Mettre pip à jour :

```bash
pip install --upgrade pip
```

Installer Ohana-Vision :

```bash
pip install -e ".[dev]"
```

Vérifier l'installation :

```bash
ohana-vision --help
```

La commande doit afficher les options disponibles.

---

# Étape 4 — Vérifier l'installation

Lancer les contrôles qualité.

Analyse statique :

```bash
python -m ruff check
```

Tests unitaires :

```bash
python -m pytest
```

Tous les tests doivent réussir.

---

# Étape 5 — Démarrer Ohana-Vision

Depuis le répertoire du projet :

```bash
ohana-vision \
    --config config/vision.yaml
```

Le serveur démarre par défaut sur :

```text
http://127.0.0.1:8000
```

Le journal doit afficher un message similaire à :

```text
Starting Ohana Vision
Listening on 127.0.0.1:8000
Application startup complete
```

---

# Étape 6 — Vérifier l'interface

Ouvrir le navigateur :

```text
http://127.0.0.1:8000/ui/
```

Vérifier que :

* l'interface se charge correctement ;
* les informations de runtime sont affichées ;
* la navigation fonctionne ;
* les différentes vues sont accessibles.

Si **Ohana-Agent** est également en fonctionnement, vérifier que les observations apparaissent en temps réel dans l'interface.

---

# Arrêter l'application

Depuis le terminal :

```text
CTRL+C
```

---

# Mise à jour

Depuis le répertoire du projet :

```bash
git pull
```

Réinstaller ensuite le projet :

```bash
pip install -e .
```

---

# Désinstallation

Désactiver l'environnement virtuel :

```bash
deactivate
```

Supprimer ensuite le répertoire du projet.

---

# Dépannage

## La commande `ohana-vision` est introuvable

Vérifier que l'environnement virtuel est activé.

Réinstaller le projet :

```bash
pip install -e .
```

---

## Impossible d'accéder à l'interface web

Vérifier que le serveur est bien démarré et qu'aucune autre application n'utilise le port configuré.

Contrôler également que l'URL utilisée est correcte :

```text
http://127.0.0.1:8000/ui/
```

---

## Les tests échouent

Vérifier que vous utilisez une version de Python compatible et que toutes les dépendances ont été installées correctement.

---

# Étape suivante

Une fois Ohana-Vision installé, vous pouvez installer et démarrer **Ohana-Agent** afin de recevoir et visualiser les observations de votre infrastructure en temps réel.
