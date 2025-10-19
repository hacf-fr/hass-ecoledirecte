# Integration Ecole directe pour Home Assistant

![Version](https://img.shields.io/github/v/release/hacf-fr/hass-ecoledirecte?label=version) [![HACS: Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) <a href="https://www.buymeacoffee.com/giga77" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="30" width="120"></a>

- [Installation](#Installation)
  - [Installation via l'interface utilisateur via HACS](#Installation-via-linterface-utilisateur-via-hacs)
  - [Installation manuelle](<#Installation-manuelle>)
- [Configuration](#Configuration)
- [Utilisation](#Utilisation)


## Installation

### Installation via l'interface utilisateur via HACS

1. Cliquez sur ce lien : [HACS: Ecole Directe](https://my.home-assistant.io/redirect/hacs_repository/?owner=hacf-fr&repository=hass-ecoledirecte)
2. Cliquez sur le bouton `Open link`.
3. Cliquez sur le bouton `Télécharger` en bas à droite, puis une deuxième fois sur `Télécharger`.
5. Il faut ensuite redémarrer Home Assistant.

### Installation manuelle
Copier le répertoire ecole_directe de la dernière release dans le répertoire custom_components de votre répertoire config. Redémarrer Home Assistant

## Configuration

Cliquer sur ce bouton:
[![Open your Home Assistant instance and start setting up a new integration of a specific brand.](https://my.home-assistant.io/badges/brand.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecole_directe)

Ou aller dans :
Paramètres > Appareils et services > Intégrations > Ajouter une intégration, et chercher "Ecole Directe"

Utiliser votre identifiant et mot de passe :

![Ecole directe config flow](doc/config_flow_username_password.png)

Le fichier qcm permet de sauvegarder les questions et respectives réponses pour la double authentification requise par Ecole Directe. Il est créé automatiquement dans le répertoire Config de Home Assistant.
L'option "Envoi de notifications" permet d'envoyer une notification lorsqu'il y a une nouvelle question dans le fichier qcm. Il est aussi possible de créer une automatisation à partir de l'événement "ecole_directe_event" de type "new_qcm.
Exemple:
```
alias: Ecole Directe - notification nouvelle question QCM
description: Notification en cas de nouvelle question QCM dans le fichier qcm
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_qcm
action:
  - service: notify.persistent_notification
    data:
      message: >
        Nouvelle question : {{ trigger.event.data.question }} Il faut vérifier
        le fichier qcm
      title: Nouvelle question qcm Ecole Directe
mode: queued
max: 10
```

## Utilisation

Cette intégration fournit plusieurs entités, toujours préfixées avec `ecole_directe_PRENOM_NOM` (où `PRENOM` et `NOM` sont remplacé).
Les entités sont mises à jour toutes les 30 minutes.
| Entité | Description |
|--------|-------------|
| `sensor.ecole_directe_PRENOM_NOM` | informations basique de l'enfant |
| `[...]_homeworks` | devoirs |
| `[...]_homeworks_today` | devoirs du jour |
| `[...]_homeworks_tomorrow` | devoirs du lendemain |
| `[...]_homeworks_next_day` | devoirs du jour ouvré suivant (ex: si on consulte le vendredi, il doit y avoir les devoirs du lundi )|
| `[...]_homeworks_1` | devoirs de la semaine en cours |
| `[...]_homeworks_2` | devoirs de la semaine suivante |
| `[...]_homeworks_3` | devoirs de la semaine suivante suivante :D |
| `[...]_grades` | notes |
| `[...]_evaluations` | evaluations |
| `[...]_timetable_today` | emploi du temps du jour |
| `[...]_timetable_tomorrow` | emploi du temps du lendemain |
| `[...]_timetable_next_day` | emploi du temps du jour ouvré suivant (ex: si on consulte le vendredi, il doit y avoir l'emploi du temps du lundi )|
| `[...]_timetable_1` | emploi du temps de la semaine en cours |
| `[...]_timetable_2` | emploi du temps de la semaine suivante |
| `[...]_timetable_3` | emploi du temps de la semaine suivante suivante :D |
| `[...]_absences` | absences |
| `[...]_retards` | retards |
| `[...]_sanctions` | sanctions |
| `[...]_encouragements` | encouragements |

Il y a des événements qui sont déclenché sous certaines conditions. Ils peuvent être utiliser comme déclencheur dans des automatisations.
| Evénement | Description |
|--------|-------------|
| `new_formulaires` | nouveau formulaire |
| `new_homework` | nouveau devoir |
| `new_grade` | nouvelle note |
| `new_absence` | nouvelle absence |
| `new_retard` | nouveau retard |
| `new_sanction` | nouvelle sanction |
| `new_encouragement` | nouvel encouragement |
| `new_qcm` | nouveau qcm |

