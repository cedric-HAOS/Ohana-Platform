# Installer Ohana Platform

Ce guide décrit l'installation complète d'une plateforme **Ohana** en environnement de développement.

À l'issue de cette procédure, vous disposerez des composants suivants :

* Ohana-Agent
* Ohana-Vision

---

# Prérequis

Les versions suivantes sont recommandées.

| Logiciel           | Version recommandée     |
| ------------------ | ----------------------- |
| Git                | 2.45+                   |
| Python             | 3.13+                   |
| pip                | Dernière version        |
| Navigateur moderne | Chrome, Edge ou Firefox |

Vérifier les versions installées :

```bash
git --version

python --version

pip --version
```

---

# Étape 1 — Récupérer les projets

Créer un répertoire de travail :

```bash
mkdir Ohana
cd Ohana
```

Cloner les dépôts :

```bash
git clone https://github.com/cedric-HAOS/Ohana-Agent.git

git clone https://github.com/cedric-HAOS/Ohana-Vision.git
```

Vérifier :

```bash
dir
```

Le dossier doit contenir :

```text
Ohana-Agent
Ohana-Vision
```

---

# Étape 2 — Installer Ohana-Agent

Accéder au dépôt :

```bash
cd Ohana-Agent
```

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Activer l'environnement :

### Windows

```powershell
.venv\Scripts\activate
```

### Linux

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install --upgrade pip

pip install -e .
```

Vérifier :

```bash
ohana-agent --help
```

Quitter le projet :

```bash
cd ..
```

---

# Étape 3 — Installer Ohana-Vision

Accéder au dépôt :

```bash
cd Ohana-Vision
```

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Activer l'environnement :

### Windows

```powershell
.venv\Scripts\activate
```

### Linux

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install --upgrade pip

pip install -e .
```

Vérifier :

```bash
ohana-vision --help
```

Quitter le projet :

```bash
cd ..
```

---

# Étape 4 — Démarrer Ohana-Agent

Depuis le répertoire **Ohana-Agent** :

```bash
ohana-agent \
    --config config/shikamaru.yaml \
    --infrastructure config/infrastructure.yaml \
    --dns-config config/plugins/dns.yaml
    --ntp-config config/plugins/ntp.yaml
    --mqtt-config config/plugins/mqtt.yaml
```

Le journal doit indiquer que l'agent est démarré.

---

# Étape 5 — Démarrer Ohana-Vision

Depuis le répertoire **Ohana-Vision** :

```bash
ohana-vision \
    --config config/vision.yaml
```

Le serveur démarre par défaut sur :

```text
http://127.0.0.1:8000
```

---

# Étape 6 — Vérifier le fonctionnement

Ouvrir l'interface :

```text
http://127.0.0.1:8000/ui/
```

Contrôler que :

* l'application est accessible ;
* les informations de runtime sont affichées ;
* les observations remontent correctement lorsque l'agent en publie.

---

# Mise à jour

Pour mettre à jour les composants :

```bash
git pull
```

Puis réinstaller le projet :

```bash
pip install -e .
```

Effectuer cette opération dans chacun des dépôts.

---

# Dépannage

## La commande `ohana-agent` est introuvable

Vérifier que l'environnement virtuel est activé.

Réinstaller ensuite le projet :

```bash
pip install -e .
```

---

## La commande `ohana-vision` est introuvable

Vérifier que l'environnement virtuel est activé.

Réinstaller ensuite le projet :

```bash
pip install -e .
```

---

## L'interface web n'est pas accessible

Vérifier que **Ohana-Vision** est démarré et qu'aucune autre application n'utilise le port configuré.

---

## Aller plus loin

Les guides suivants complètent cette procédure :

* Installer-Ohana-Agent.md
* Installer-Ohana-Vision.md
* Guide de déploiement
* Guide de développement
* Guide de contribution
