# Cartes Lovelace Ecole Directe

L'intégration fournit des cartes Lovelace personnalisées intégrées automatiquement pour afficher les données scolaires dans votre tableau de bord Home Assistant.

## Carte Emploi du temps (`ecole_directe-emploi_temps-card`)

La carte emploi du temps permet de visualiser l'agenda des cours d'un élève au format liste ou carrousel (slider).

### Nouvelles fonctionnalités

#### 1. Affichage multi-semaines
La carte permet désormais d'afficher plusieurs semaines de cours (`semaine_en_cours`, `semaine_suivante`, `semaine_apres_suivante`) sur une seule et même carte :
- **Résolution automatique** : En sélectionnant le capteur de la semaine en cours (ex: `sensor.ed_prenom_nom_emploi_du_temps_semaine_en_cours`), la carte peut automatiquement retrouver et charger les cours de la semaine suivante et/ou de la semaine d'après.
- **Navigation continue (slider)** : Lorsque le slider est activé, vous pouvez naviguer d'un jour à l'autre sans interruption d'une semaine sur l'autre (par exemple, passer du vendredi de la semaine en cours au lundi de la semaine suivante avec les flèches).
- **Support des entités multiples** : Vous pouvez également définir explicitement une liste d'entités via la clé `entities`.

#### 2. Gestion des cours passés (`ended_lessons`)
Une option unique permet de choisir comment traiter les cours dont l'heure de fin est dépassée :
- **Normal (`none`)** : Les cours passés restent affichés normalement sans distinction.
- **Dim (`dim`)** *(par défaut)* : Les cours passés sont estompés avec une opacité réduite.
- **Caché (`hide`)** : Les cours passés sont complètement masqués :
  - Les cours en cours de déroulement restent visibles.
  - La pause déjeuner (« Repas ») et les créneaux libres (« Pas de cours ») passés sont également masqués.
  - Les journées entièrement passées sont masquées, permettant au tableau de bord ou au slider de démarrer directement sur les cours restants.
  - Si tous les cours de la période sont passés, le message « Pas d'emploi du temps à afficher » apparaît.

---

### Options de configuration

| Option | Type | Défaut | Description |
| --- | --- | --- | --- |
| `entity` | string | **Requis\*** | Entité capteur d'emploi du temps de base (ex: `sensor.ed_lucas_emploi_du_temps_semaine_en_cours`). |
| `entities` | list | optionnel | Liste d'entités d'emploi du temps à agréger (alternative ou complément à `entity`). |
| `display_next_week` | boolean | `false` | Affiche les cours de la semaine suivante (`semaine_suivante`). |
| `display_week_after_next` | boolean | `false` | Affiche les cours de la semaine après suivante (`semaine_apres_suivante`). |
| `ended_lessons` | string | `dim` | Gestion des cours passés : `none` (normal/rien), `dim` (estompé), ou `hide` (caché). |
| `enable_slider` | boolean | `false` | Active la vue carrousel/slider pour afficher un seul jour à la fois avec des flèches `←` et `→`. |
| `switch_to_next_day` | boolean | `false` | En mode slider, passe automatiquement au jour suivant une fois les cours de la journée terminés. |
| `display_header` | boolean | `true` | Affiche l'en-tête de la carte avec le prénom de l'élève. |
| `display_classroom` | boolean | `true` | Affiche le numéro de salle. |
| `display_teacher` | boolean | `true` | Affiche le nom du professeur. |
| `display_day_hours` | boolean | `true` | Affiche les heures de début et fin de journée dans l'en-tête de chaque jour. |
| `display_lunch_break` | boolean | `true` | Affiche une ligne pour la pause déjeuner (« Repas »). |
| `display_free_time_slots` | boolean | `true` | Affiche une ligne (« Pas de cours ») pour les trous de plus de 30 minutes entre deux cours. |

\* *Au moins une entité doit être spécifiée via `entity` ou `entities`.*

---

### Exemples de configuration YAML

#### Affichage standard de la semaine avec cours passés masqués
```yaml
type: custom:ecole_directe-emploi_temps-card
entity: sensor.ed_lucas_dupont_emploi_du_temps_semaine_en_cours
ended_lessons: hide
```

#### Affichage multi-semaines (semaine en cours + suivante + après suivante) en mode slider
```yaml
type: custom:ecole_directe-emploi_temps-card
entity: sensor.ed_lucas_dupont_emploi_du_temps_semaine_en_cours
display_next_week: true
display_week_after_next: true
enable_slider: true
switch_to_next_day: true
ended_lessons: dim
```

#### Configuration avec liste explicite d'entités
```yaml
type: custom:ecole_directe-emploi_temps-card
entities:
  - sensor.ed_lucas_dupont_emploi_du_temps_semaine_en_cours
  - sensor.ed_lucas_dupont_emploi_du_temps_semaine_suivante
  - sensor.ed_lucas_dupont_emploi_du_temps_semaine_apres_suivante
enable_slider: true
ended_lessons: hide
```
