# Installer et mettre à jour Ohana-Platform

Ce guide est le point d'entrée pour la production Linux/systemd. Le
[guide de développement](getting-started/Installer-Ohana-Platform.md) concerne
les dépôts sources et les environnements locaux.

## Préparer Installer et choisir la composition

Installer Ohana-Installer selon [son guide officiel](https://github.com/cedric-HAOS/Ohana-Installer/blob/main/docs/Installation.md).
La restauration INFRA-01 requiert au minimum Installer **1.15.6**, avec le
correctif de propriétaire et de permissions iCloud. Vérifier Linux/systemd,
Python 3.13 ou supérieur et la commande :

```bash
ohana --version
ohana versions
```

La composition recommandée est l'entrée `default_platform_version` du
[catalogue](../release-catalog.yaml). Le [manifeste](../release-manifest.yaml)
décrit les versions, assets, configurations et services de cette composition.
Les deux fichiers publiés sont la référence ; une ancienne version citée dans
un CHANGELOG ne devient pas la version attendue d'une installation neuve.

## Installer la composition recommandée

```bash
sudo ohana install
```

Lire les versions choisies et le plan avant confirmation. `--yes` exprime
l'acceptation explicite du plan pour une installation automatisée.
Pour choisir une autre composition, utiliser la version exacte affichée par
`ohana versions`. Exemple historique, qui n'est pas la recommandation courante :

```bash
sudo ohana install --platform-version 1.0.20
```

Le choix par `--agent-version` et `--vision-version` doit correspondre à une
entrée publiée du catalogue. Le menu propose une fenêtre de compositions
supportées ; les entrées `legacy` restent accessibles par version exacte pour
restaurer d'anciennes archives.

## Vérifier le résultat

```bash
sudo systemctl is-active ohana-agent.service ohana-vision.service
/opt/ohana-agent/venv/bin/ohana-agent --version
/opt/ohana-vision/venv/bin/ohana-vision --version
ohana --version
```

Les versions installées doivent correspondre à la composition sélectionnée,
pas à un exemple historique du guide. Ouvrir Vision sur
`http://ADRESSE_DU_SERVEUR:8000`, vérifier la topologie et une observation récente.
Les guides [Agent](Guides/Déployer-Ohana-Agent.md) et
[Vision](Guides/Déployer-Ohana-Vision.md) détaillent leurs fichiers et contrôles.

## Mettre à jour

Sauvegarder les configurations et données, puis lancer :

```bash
sudo ohana update
```

Vérifier le plan et confirmer. Installer conserve les configurations locales,
réconcilie les unités et conserve les packages déjà à la version cible.
Contrôler ensuite services, versions, ingestion et capacités essentielles.
Les sauvegardes logiques INFRA-01 restaurent la composition inscrite dans leur
manifeste ; une mise à jour ultérieure est une opération distincte.

Une rétrogradation explicite utilise `--allow-downgrade`. Préparer sa sauvegarde
et vérifier la compatibilité des schémas avant de l'appliquer : conserver un
fichier de configuration ne prouve pas qu'une ancienne version sait le lire.

## Réseau INFRA-01

Les options de provisionnement réseau sont disponibles dans Installer. Exemple
de cible Hashirama, à adapter aux adresses réellement déployées :

```bash
sudo ohana install \
  --network-interface eth0 \
  --network-address 192.168.1.10/24 \
  --network-gateway 192.168.1.1 \
  --network-dns 192.168.1.11 \
  --network-dns 192.168.1.12
```

Garder une console locale et confirmer la transaction réseau. Le DHCP principal
n'est activé qu'après arrêt du serveur précédent et vérification d'un nouveau
bail. Consulter [Operations](Operations.md) et [Troubleshooting](Troubleshooting.md).
