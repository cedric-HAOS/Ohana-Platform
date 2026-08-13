Pour Platform 1.0.54, les versions recommandées sont Agent 1.14.1, Vision 1.13.0 et
Installer 1.9.4.

# Dépannage Ohana

## Vérifier les services

```bash
sudo systemctl status ohana-agent.service --no-pager
sudo systemctl status ohana-vision.service --no-pager
```

## Lire les journaux

```bash
sudo journalctl -u ohana-agent.service -n 100 --no-pager
sudo journalctl -u ohana-vision.service -n 100 --no-pager
```

## Vérifier les versions

```bash
/opt/ohana-agent/venv/bin/ohana-agent --version
/opt/ohana-vision/venv/bin/ohana-vision --version
ohana --version
```

## Vision ne communique pas avec Agent

1. vérifier que les deux services sont actifs ;
2. vérifier `agent.administration_url` dans `/etc/ohana-vision/vision.yaml` ;
3. vérifier la présence et les droits du secret partagé ;
4. consulter les journaux des deux services.

## Une réservation DHCP est refusée

Les noms d’hôte DNS n’acceptent pas les espaces ni le caractère `_`. Utiliser
un tiret, par exemple `esp-lave-vaiselle` à la place de
`esp-lave_vaiselle`. Ohana-Vision 1.9.0 effectue ce contrôle directement dans
le formulaire.

## Une configuration est refusée

Agent valide les documents avant écriture. Pour DHCP, il exécute également la
commande de validation dnsmasq configurée. Le détail du refus apparaît dans
Vision et dans le journal Agent.

## Réconcilier l'installation

```bash
sudo ohana update
```

La commande conserve les configurations locales, réinstalle les composants qui
ne correspondent pas au manifeste et réconcilie les unités systemd.


## Couple introuvable

Exécuter `ohana versions` et vérifier que la version Platform ou le couple
Agent/Vision figure dans `release-catalog.yaml`. Installer refuse volontairement
les combinaisons non publiées.
