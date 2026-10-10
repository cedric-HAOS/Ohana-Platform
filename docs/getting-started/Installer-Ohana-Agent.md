# Installer Ohana-Agent

Ce guide décrit l'installation d'**Ohana-Agent** en environnement de développement.

À l'issue de cette procédure, vous disposerez d'un agent fonctionnel capable d'exécuter des capacités, de produire des observations et de les publier vers Ohana-Vision.

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
git clone https://github.com/cedric-HAOS/Ohana-Agent.git

cd Ohana-Agent
```

Vérifier le contenu du dépôt :

```bash
dir
```

Vous devez notamment retrouver :

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

Activation sous Windows :

```powershell
.\.venv\Scripts\Activate.ps1
```

Activation sous Linux :

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

Installer Ohana-Agent :

```bash
pip install -e ".[development]"
```

Vérifier que l'installation est correcte :

```bash
ohana-agent --help
```

La commande doit afficher les options disponibles.

---

# Étape 4 — Vérifier l'installation

Exécuter les contrôles qualité.

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

# Étape 5 — Démarrer Ohana-Agent

Depuis la racine du dépôt Agent, dans un terminal Bash avec son environnement
virtuel activé, lancer l'agent avec la configuration locale :

```bash
ohana-agent \
    --config config/shikamaru.yaml \
    --infrastructure config/infrastructure.yaml \
    --dns-config config/plugins/dns.yaml \
    --mqtt-config config/plugins/mqtt.yaml \
    --ntp-config config/plugins/ntp.yaml
```

Sous PowerShell, depuis cette même racine, utiliser les continuations propres
à PowerShell et l'exécutable de l'environnement Agent :

```powershell
& .\.venv\Scripts\ohana-agent.exe `
    --config config/shikamaru.yaml `
    --infrastructure config/infrastructure.yaml `
    --dns-config config/plugins/dns.yaml `
    --mqtt-config config/plugins/mqtt.yaml `
    --ntp-config config/plugins/ntp.yaml
```

Conserver ce terminal pour Agent ; démarrer Vision dans un autre terminal avec
son propre environnement. Adapter les cibles de configuration au laboratoire.

Au démarrage, le journal doit confirmer le chargement de la configuration et l'initialisation des plugins.

---

# Vérification

L'agent doit démarrer sans erreur.

Arrêter l'exécution avec :

```text
CTRL+C
```

---

# Mise à jour

Depuis le répertoire du projet :

```bash
git pull
```

Puis réinstaller la version courante :

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

## La commande `ohana-agent` est introuvable

Vérifier que l'environnement virtuel est activé.

Réinstaller le projet :

```bash
pip install -e .
```

---

## Les dépendances ne s'installent pas

Mettre pip à jour :

```bash
pip install --upgrade pip
```

Puis relancer :

```bash
pip install -e .
```

---

## Les tests échouent

Vérifier que vous utilisez une version de Python compatible et que toutes les dépendances ont été installées correctement.

---

## Étape suivante

Une fois l'installation terminée, vous pouvez installer **Ohana-Vision** afin de visualiser les observations produites par l'agent.
