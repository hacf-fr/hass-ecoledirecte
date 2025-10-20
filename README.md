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

Cette intégration fournit plusieurs entités, toujours préfixées avec `ed_PRENOM_NOM` (où `PRENOM` et `NOM` sont remplacé).
Les entités sont mises à jour toutes les 30 minutes.
| Entité | Description |
|--------|-------------|
| `sensor.ed_PRENOM_NOM` | informations basique de l'enfant |
| `[...]_devoirs` | devoirs |
| `[...]_devoirs_aujourd_hui` | devoirs du jour |
| `[...]_devoirs_demain` | devoirs du lendemain |
| `[...]_devoirs_jour_suivant` | devoirs du jour ouvré suivant (ex: si on consulte le vendredi, il doit y avoir les devoirs du lundi )|
| `[...]_devoirs_semaine_en_cours` | devoirs de la semaine en cours |
| `[...]_devoirs_semaine_suivante` | devoirs de la semaine suivante |
| `[...]_devoirs_semaine_apres_suivante` | devoirs de la semaine suivante suivante :D |
| `[...]_notes` | notes |
| `[...]_evaluations` | evaluations |
| `[...]_emploi_du_temps_aujourd_hui` | emploi du temps du jour |
| `[...]_emploi_du_temps_demain` | emploi du temps du lendemain |
| `[...]_emploi_du_temps_jour_suivant` | emploi du temps du jour ouvré suivant (ex: si on consulte le vendredi, il doit y avoir l'emploi du temps du lundi )|
| `[...]_emploi_du_temps_semaine_en_cours` | emploi du temps de la semaine en cours |
| `[...]_emploi_du_temps_semaine_suivante` | emploi du temps de la semaine suivante |
| `[...]_emploi_du_temps_semaine_apres_suivante` | emploi du temps de la semaine suivante suivante :D |
| `[...]_absences` | absences |
| `[...]_retards` | retards |
| `[...]_sanctions` | sanctions |
| `[...]_encouragements` | encouragements |

Il y a des événements qui sont déclenché sous certaines conditions. Ils peuvent être utiliser comme déclencheur dans des automatisations.
| Evénement | Description |
|--------|-------------|
| `new_formulaire` | nouveau formulaire |
| `new_devoir` | nouveau devoir |
| `new_note` | nouvelle note |
| `new_evaluation` | nouvelle evaluation |
| `new_absence` | nouvelle absence |
| `new_retard` | nouveau retard |
| `new_sanction` | nouvelle sanction |
| `new_encouragement` | nouvel encouragement |
| `new_qcm` | nouveau qcm |

