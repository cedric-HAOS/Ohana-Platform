# Couleurs — référence du Design System Ohana

Référence documentaire consolidée le 10 octobre 2026. La palette de l'interface
Vision est définie par les tokens du
[fichier CSS chargé](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/src/ohana_vision/web/static/design-system.css).
Ce fichier est la référence des valeurs effectivement utilisées ; les composants
utilisent ses variables et les alias de `styles/foundations.css`.

## Palette du thème sombre livré

| Usage | Token | Valeur |
|---|---|---|
| Fond général | `--ohana-background-canvas` | `#071014` |
| Sidebar | `--ohana-background-sidebar` | `#091419` |
| Surface | `--ohana-background-surface` | `#0d1a20` |
| Surface élevée | `--ohana-background-surface-raised` | `#112229` |
| Accent principal | `--ohana-brand-primary` | `#28d7c0` |
| Accent survolé | `--ohana-brand-primary-hover` | `#4de0cd` |
| Accent actif | `--ohana-brand-primary-active` | `#20bda9` |
| Texte principal | `--ohana-text-primary` | `#f1f7f7` |
| Texte secondaire | `--ohana-text-secondary` | `#a9b9bc` |
| Texte atténué | `--ohana-text-muted` | `#718489` |
| Bordure | `--ohana-border-default` | `#294149` |
| Sain | `--ohana-health-healthy` | `#28d7c0` |
| Dégradé | `--ohana-health-degraded` | `#f2b84b` |
| Critique | `--ohana-health-critical` | `#ef6464` |
| Inconnu | `--ohana-health-unknown` | `#718489` |

Le turquoise identifie l'accent et l'état sain ; l'ambre indique une dégradation,
le rouge un état critique et le gris un état inconnu. Associer un libellé et une
icône à l'état pour que la couleur ne soit pas l'unique moyen de compréhension.
Une absence de mesure récente conserve un état non vérifié.

## Usage dans les composants

```css
.example-panel {
  color: var(--ohana-text-primary);
  background: var(--ohana-background-surface);
  border: 1px solid var(--ohana-border-default);
}
```

Réutiliser les tokens sans recopier des couleurs dans chaque composant.
Les variantes `*-soft` et les surfaces overlay sont définies dans le même CSS.
Les alias historiques `--background`, `--surface`, `--accent` et `--healthy`
servent la transition des composants existants ; ils ne définissent pas une
palette indépendante.

## Applicabilité des anciennes palettes

Les anciennes tables `--color-background` / `--color-surface` et la palette
cyan de la charte Vision sont des propositions historiques. Elles ne doivent
plus prescrire les valeurs d'une interface nouvelle. Les exemples anciens des
autres pages Design illustrent leur mise en page ; traduire leurs couleurs en
tokens actuels avant utilisation.

Une évolution des tokens nécessite une validation de contraste, des états,
des composants et des usages mobile/bureau. Une correction documentaire ne
modifie pas automatiquement le CSS ni les interfaces en production.

Voir [Brand](Brand.md), [Components](Components.md), [Widgets](Widgets.md) et
[la charte d'intégration Vision](https://github.com/cedric-HAOS/Ohana-Vision/blob/main/BRAND-GUIDELINES.md).
