# Evénements de l'intégration Ecole directe pour Home Assistant

Il y a des événements qui sont déclenché sous certaines conditions. Ils peuvent être utiliser comme déclencheur dans des automatisations.

Voici la liste des évenements:

Evénement | Description
--------- | -----------
`new_formulaire` | nouveau formulaire
`new_devoir` | nouveau devoir
`new_note` | nouvelle note
`new_evaluation` | nouvelle evaluation
`new_absence` | nouvelle absence
`new_retard` | nouveau retard
`new_sanction` | nouvelle sanction
`new_encouragement` | nouvel encouragement
`new_qcm` | nouveau qcm

## new_formulaire

```yaml
alias: Ecole Directe - notification nouveau formulaire
description: Notification en cas de nouveau formulaire sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_formulaire
condition: []
action:
  - service: notify.persistent_notification
    data:
      message: >
      title: Nouveau formulaire
mode: single

```

## new_devoir

```yaml
alias: Ecole Directe - notification nouveau devoir
description: Notification en cas de nouveau devoir sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_devoir
condition: []
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.subject }} pour le {{
        trigger.event.data.data.date }}
      title: Nouveau devoir pour {{ trigger.event.data.child_name }}
mode: single
```

## new_note

```yaml
alias: Ecole Directe - notification nouvelle note
description: Notification en cas de nouvelle note sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_note
action:
  - service: notify.persistent_notification
    data:
      message: >-
        {{ trigger.event.data.data.subject }} : {{
        trigger.event.data.data.grade_out_of }} ({{
        trigger.event.data.data.comment }})
      title: Nouvelle note pour {{ trigger.event.data.child_name }}
```

## new_evaluation

```yaml
alias: Ecole Directe - notification nouvelle évaluation
description: Notification en cas de nouvelle évaluation sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_evaluation
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.subject }} : {{ trigger.event.data.data.name }}
      title: Nouvelle évaluation pour {{ trigger.event.data.child_name }}
mode: single
```

## new_absence

```yaml
alias: Ecole Directe - notification nouvelle absence
description: Notification en cas de nouvelle absence sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_absence
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.display_date }} - {{ trigger.event.data.data.commentaire }}
      title: Nouvelle absence pour {{ trigger.event.data.child_name }}
mode: single
```

## new_retard

```yaml
alias: Ecole Directe - notification nouveau retard
description: Notification en cas de nouveau retard sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_retard
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.display_date }} - {{ trigger.event.data.data.commentaire }}
      title: Nouveau retard pour {{ trigger.event.data.child_name }}
mode: single
```

## new_sanction

```yaml
alias: Ecole Directe - notification nouvelle sanction
description: Notification en cas de nouvelle sanction sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_sanction
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.display_date }} - {{ trigger.event.data.data.commentaire }}
      title: Nouvelle sanction pour {{ trigger.event.data.child_name }}
mode: single
```

## new_encouragement

```yaml
alias: Ecole Directe - notification nouvel encouragement
description: Notification en cas de nouvel encouragement sur Ecole Directe
trigger:
  - platform: event
    event_type: ecole_directe_event
    event_data:
      type: new_encouragement
action:
  - service: notify.persistent_notification
    data:
      message: >
        {{ trigger.event.data.data.display_date }} - {{ trigger.event.data.data.commentaire }}
      title: Nouvel encouragement pour {{ trigger.event.data.child_name }}
mode: single
```

## new_qcm

```yaml
alias: Ecole Directe - notification nouvelle question QCM
description: Notification en cas de nouvelle question QCM
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
        une nouvelle entité
      title: Nouvelle question qcm Ecole Directe
mode: queued
max: 10
```
