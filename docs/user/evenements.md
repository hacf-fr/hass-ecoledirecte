# Événements et Automatisations Ecole Directe

L'intégration Ecole Directe émet des événements personnalisés sur le bus d'événements de Home Assistant (`hass.bus`). Ces événements permettent de créer des automatisations réactives (notifications mobiles, alertes vocales, affichages dynamiques, etc.) dès qu'une information scolaire est modifiée ou ajoutée.

---

## 📡 Le bus d'événements : `ecole_directe_event`

Tous les événements émis par l'intégration partagent le même type d'événement Home Assistant :

```text
ecole_directe_event
```

### Structure des données (`trigger.event.data`)

Lorsqu'un événement survient, la variable d'automatisation `trigger.event.data` contient les informations suivantes :

| Champ | Type | Description |
| --- | --- | --- |
| `type` | `string` | Identifiant du type d'événement (ex. `new_note`, `new_devoir`, `edt_changement`, etc.). |
| `child_name` | `string` \| `null` | Nom complet de l'élève concerné (ex. `"Lucas Dupont"`). Vaut `""` ou `null` pour les événements liés au compte global (formulaires, espaces de travail, QCM). |
| `data` | `dict` | Dictionnaire contenant les détails complets de l'élément (note, devoir, cours, absence...). *(Non présent pour `new_qcm`)* |
| `qcm_json` | `dict` | Présent uniquement pour l'événement `new_qcm`, contient les questions et réponses possibles. |

---

## 📋 Tableau récapitulatif des événements

| Type d'événement (`type`) | Cible | Déclenchement |
| --- | --- | --- |
| [`new_devoir`](#1-nouveau-devoir-new_devoir) | Élève | Un nouveau devoir à faire a été publié dans le cahier de textes. |
| [`new_note`](#2-nouvelle-note-new_note) | Élève | Une nouvelle note a été saisie par un enseignant. |
| [`new_evaluation`](#3-nouvelle-évaluation-new_evaluation) | Élève | Une nouvelle évaluation par compétences a été publiée. |
| [`edt_changement`](#4-changement-demploi-du-temps-edt_changement) | Élève | Un cours a été annulé, déplacé, modifié ou a changé de salle / enseignant. |
| [`new_absence`](#5-nouvelle-absence-new_absence) | Élève | Une absence a été enregistrée en vie scolaire. |
| [`new_retard`](#6-nouveau-retard-new_retard) | Élève | Un retard a été enregistré en vie scolaire. |
| [`new_sanction`](#7-nouvelle-sanction-new_sanction) | Élève | Une sanction (retenue, observation...) a été enregistrée. |
| [`new_encouragement`](#8-nouvel-encouragement-new_encouragement) | Élève | Une distinction (félicitations, encouragement...) a été attribuée. |
| [`new_formulaire`](#9-nouveau-formulaire-new_formulaire) | Compte | Un nouveau formulaire administratif est à remplir par la famille. |
| [`new_postit`](#10-nouveau-post-it-despace-de-travail-new_postit) | Compte | Un nouveau post-it a été épinglé dans un espace de travail. |
| [`new_activity`](#11-nouvelle-activité-despace-de-travail-new_activity) | Compte | Une nouvelle activité ou un nouveau fichier a été partagé dans un espace de travail. |
| [`new_qcm`](#12-double-authentification-qcm-new_qcm) | Compte | Une question de sécurité (2FA) est demandée lors de la connexion. |

---

## 🔍 Données détaillées par événement

### 1. Nouveau devoir (`new_devoir`)

Émis lorsque le coordinateur détecte un nouveau devoir qui n'était pas présent lors de la synchronisation précédente.

- **`child_name`** : Nom de l'élève (`"Lucas Dupont"`).
- **`data`** :
  - `devoir_id` (*int/str*) : Identifiant unique du devoir sur Ecole Directe.
  - `eleve_id` (*str*) : Identifiant de l'élève.
  - `date` (*datetime/string*) : Date pour laquelle le devoir est à rendre (format `YYYY-MM-DD`).
  - `matiere` (*str*) : Nom de la matière (ex. `"FRANCAIS"`, `"MATHEMATIQUES"`).
  - `short_description` (*str*) : Résumé court du travail (tronqué à 125 caractères).
  - `description` (*str*) : Contenu détaillé du travail à effectuer (décodé du HTML si l'option est active).
  - `effectue` (*bool*) : `true` si déjà marqué comme fait, sinon `false`.
  - `interrogation` (*bool*) : `true` s'il s'agit d'une évaluation / contrôle annoncé, sinon `false`.
  - `documents` (*list*) : Liste des pièces jointes associées au devoir.

```json
{
  "child_name": "Lucas Dupont",
  "type": "new_devoir",
  "data": {
    "devoir_id": 2664,
    "eleve_id": "2232",
    "date": "2026-11-12T00:00:00",
    "matiere": "HISTOIRE-GEOGRAPHIE",
    "short_description": "Apprendre la leçon sur la Première Guerre Mondiale",
    "description": "Apprendre la leçon pages 45 à 52 et préparer les définitions.",
    "effectue": false,
    "interrogation": true,
    "documents": []
  }
}
```

---

### 2. Nouvelle note (`new_note`)

Émis lors de la publication d'une nouvelle note.

- **`child_name`** : Nom de l'élève.
- **`data`** :
  - `date` (*str*) : Date de l'évaluation (`YYYY-MM-DD`).
  - `date_saisie` (*str*) : Date de saisie de la note par le professeur.
  - `matiere` (*str*) : Matière concernée.
  - `commentaire` (*str*) : Intitulé du devoir ou appréciation de l'enseignant.
  - `note` (*str*) : Valeur de la note obtenue (ex. `"16"`, `"14,5"`).
  - `sur` (*str*) : Barème de référence (ex. `"20"`).
  - `note_sur` (*str*) : Note au format complet (ex. `"16/20"`).
  - `coefficient` (*str*) : Coefficient appliqué à la note.
  - `moyenne_classe` (*str*) : Moyenne de la classe pour ce devoir.
  - `min` (*str*) : Note minimale de la classe.
  - `max` (*str*) : Note maximale de la classe.
  - `non_significatif` (*bool*) : `true` si la note ne compte pas dans la moyenne.
  - `elements_programme` (*list*) : Compétences évaluées associées.

```json
{
  "child_name": "Lucas Dupont",
  "type": "new_note",
  "data": {
    "date": "2026-11-06",
    "date_saisie": "2026-11-07",
    "matiere": "MATHEMATIQUES",
    "commentaire": "Contrôle fractions et géométrie",
    "note": "17",
    "sur": "20",
    "note_sur": "17/20",
    "coefficient": "2",
    "moyenne_classe": "12,4",
    "min": "06,5",
    "max": "19,5",
    "non_significatif": false,
    "elements_programme": []
  }
}
```

---

### 3. Nouvelle évaluation (`new_evaluation`)

Émis lorsqu'une évaluation par compétences est ajoutée.

- **`child_name`** : Nom de l'élève.
- **`data`** :
  - `devoir` (*str*) : Titre ou objet de l'évaluation.
  - `date` (*str*) : Date de l'évaluation (`YYYY-MM-DD`).
  - `date_saisie` (*str*) : Date de saisie.
  - `matiere` (*str*) : Matière concernée.
  - `elements_programme` (*list*) : Liste des compétences évaluées. Chaque élément contient :
    - `competence` (*str*) : Intitulé de la compétence.
    - `descriptif` (*str*) : Description détaillée.
    - `valeur` (*str*) : Code d'acquisition (`"1"`, `"2"`, `"3"`, `"4"`, ou `"-1"`, etc.).
    - `level` (*str*) : Libellé clair (`"Non atteint"`, `"Partiellement atteint"`, `"Atteint"`, `"Dépassé"`).

```json
{
  "child_name": "Lucas Dupont",
  "type": "new_evaluation",
  "data": {
    "devoir": "Expression orale en continu",
    "date": "2026-11-05",
    "date_saisie": "2026-11-07",
    "matiere": "ANGLAIS LV1",
    "elements_programme": [
      {
        "competence": "Prendre la parole en continu",
        "descriptif": "Présenter son projet à la classe",
        "valeur": "3",
        "level": "Atteint"
      }
    ]
  }
}
```

---

### 4. Changement d'emploi du temps (`edt_changement`)

Émis dès qu'une modification intervient dans les cours des trois prochaines semaines (cours annulé, cours déplacé, changement de salle ou de professeur).

- **`child_name`** : Nom de l'élève.
- **`data`** :
  - `id` (*int/str*) : Identifiant du cours.
  - `lesson` (*str*) : Nom du cours / matière (ex. `"FRANCAIS"`).
  - `start` (*datetime*) : Date et heure de début.
  - `end` (*datetime*) : Date et heure de fin.
  - `previous` (*dict \| null*) : État du cours avant la détection (avec `salle`, `prof`, `is_annule`, `is_modifie`, `start_at`, `end_at`).
  - `current` (*dict*) : Nouvel état du cours.
  - `changes` (*dict*) : Dictionnaire synthétique récapitulant chaque champ modifié sous la forme `{"champ": {"previous": ..., "current": ...}}`.

> [!TIP]
> Le dictionnaire `changes` permet de tester directement le type de changement dans les conditions ou modèles Jinja2, par exemple `{{ trigger.event.data.data.changes.is_annule.current }}`.

```json
{
  "child_name": "Lucas Dupont",
  "type": "edt_changement",
  "data": {
    "id": 14205,
    "lesson": "FRANCAIS",
    "start": "2026-11-09T08:00:00",
    "end": "2026-11-09T09:00:00",
    "previous": {
      "salle": "104",
      "prof": "Mme MARTIN",
      "is_annule": false,
      "is_modifie": false
    },
    "current": {
      "salle": "104",
      "prof": "Mme MARTIN",
      "is_annule": true,
      "is_modifie": true
    },
    "changes": {
      "is_annule": {
        "previous": false,
        "current": true
      },
      "is_modifie": {
        "previous": false,
        "current": true
      }
    }
  }
}
```

---

### 5. Vie scolaire : Absences, Retards, Sanctions, Encouragements

Les événements de vie scolaire partagent une structure similaire :

| Type | Description de `data.type_element` |
| --- | --- |
| `new_absence` | `"Absence"` |
| `new_retard` | `"Retard"` |
| `new_sanction` | `"Sanction"` |
| `new_encouragement` | `"Encouragement"` |

- **`child_name`** : Nom de l'élève.
- **`data`** :
  - `date` (*str*) : Date de l'événement.
  - `type_element` (*str*) : Type d'élément (`"Absence"`, `"Retard"`, `"Sanction"`, `"Encouragement"`).
  - `display_date` (*str*) : Libellé de la date et des horaires (ex. `"Le 10/11/2026 de 08:00 à 10:00"` ou `"Le 10/11/2026 à 08:15 (15 min)"`).
  - `justifie` (*bool*) : `true` si le motif est justifié ou régularisé, `false` sinon.
  - `motif` (*str*) : Motif déclaré ou mention accordée (ex. `"Maladie"`, `"Retenue"`, `"Félicitations"`).
  - `libelle` (*str*) : Libellé de l'élément.
  - `commentaire` (*str*) : Commentaire de la vie scolaire ou de l'administration.

```json
{
  "child_name": "Lucas Dupont",
  "type": "new_absence",
  "data": {
    "date": "2026-11-09",
    "type_element": "Absence",
    "display_date": "Le 09/11/2026 de 08:00 à 09:00",
    "justifie": false,
    "motif": "Non justifiée",
    "libelle": "Absence injustifiée",
    "commentaire": "Veuillez contacter le bureau de la vie scolaire."
  }
}
```

---

### 6. Espaces de travail et Formulaires

- **`new_formulaire`** :
  - `child_name` : `""`
  - `data` :
    - `titre` (*str*) : Intitulé du formulaire administratif.
    - `created` (*str*) : Date de création.

- **`new_postit`** :
  - `child_name` : `""`
  - `data` : Informations du post-it (`id`, `contenu`, `dateCreation`).

- **`new_activity`** :
  - `child_name` : `""`
  - `data` : Informations de l'activité (`id`, `titre`, `type`, `date`, `cloud_details`...).

---

### 7. Double authentification QCM (`new_qcm`)

Émis lorsque le serveur Ecole Directe réclame une réponse à une question de sécurité (2FA) pour finaliser la connexion.

- **`child_name`** : `null`
- **`qcm_json`** : Dictionnaire associant chaque question à la liste de ses réponses possibles.

---

## 💡 Exemples d'automatisations

Voici plusieurs exemples complets réutilisables dans votre fichier `automations.yaml` ou via l'interface utilisateur de Home Assistant.

### Exemple 1 : Notification lors d'une nouvelle note

Envoie une notification mobile aux parents avec la note, le commentaire et la moyenne de classe.

```yaml
alias: "Ecole Directe - Nouvelle note"
description: "Notifie les parents dès qu'une nouvelle note est publiée"
mode: parallel
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_note
action:
  - action: notify.notify
    data:
      title: "📝 Nouvelle note pour {{ trigger.event.data.child_name }}"
      message: >-
        {{ trigger.event.data.data.matiere }} : {{ trigger.event.data.data.note_sur }}
        {% if trigger.event.data.data.commentaire %}
        (Devoir : {{ trigger.event.data.data.commentaire }})
        {% endif %}
        Moyenne de classe : {{ trigger.event.data.data.moyenne_classe }}/20
        (Min : {{ trigger.event.data.data.min }} - Max : {{ trigger.event.data.data.max }})
```

---

### Exemple 2 : Notification lors d'un nouveau devoir (alerte si contrôle)

Notifie les devoirs à faire, avec une mention spéciale et une priorité haute s'il s'agit d'une interrogation ou d'un contrôle.

```yaml
alias: "Ecole Directe - Nouveau devoir"
description: "Alerte lors de l'ajout d'un devoir, avec surbrillance pour les contrôles"
mode: queued
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_devoir
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.data.interrogation == true }}"
        sequence:
          - action: notify.notify
            data:
              title: "⚠️ Contrôle annoncé pour {{ trigger.event.data.child_name }}"
              message: >-
                Matière : {{ trigger.event.data.data.matiere }}
                Pour le : {{ as_timestamp(trigger.event.data.data.date) | timestamp_custom('%d/%m/%Y') }}
                Sujet : {{ trigger.event.data.data.short_description }}
              data:
                push:
                  sound: "default"
                  interruption-level: "time-sensitive"
    default:
      - action: notify.notify
        data:
          title: "📚 Nouveau devoir ({{ trigger.event.data.child_name }})"
          message: >-
            {{ trigger.event.data.data.matiere }} pour le {{ as_timestamp(trigger.event.data.data.date) | timestamp_custom('%d/%m/%Y') }} :
            {{ trigger.event.data.data.short_description }}
```

---

### Exemple 3 : Alerte de changement d'emploi du temps (cours annulé ou salle modifiée)

Réagit immédiatement aux modifications de planning.

```yaml
alias: "Ecole Directe - Modification d'emploi du temps"
description: "Alerte si un cours est annulé, déplacé ou change de salle"
mode: queued
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: edt_changement
action:
  - choose:
      # Cas 1 : Cours annulé
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.data.changes.is_annule is defined and trigger.event.data.data.changes.is_annule.current == true }}"
        sequence:
          - action: notify.notify
            data:
              title: "🚫 Cours ANNULÉ - {{ trigger.event.data.child_name }}"
              message: >-
                Le cours de {{ trigger.event.data.data.lesson }} prévu le
                {{ as_timestamp(trigger.event.data.data.start) | timestamp_custom('%d/%m à %H:%M') }}
                a été annulé !

      # Cas 2 : Changement de salle
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.data.changes.salle is defined }}"
        sequence:
          - action: notify.notify
            data:
              title: "🔄 Changement de salle - {{ trigger.event.data.child_name }}"
              message: >-
                Le cours de {{ trigger.event.data.data.lesson }} passe de la salle
                {{ trigger.event.data.data.changes.salle.previous }} à la salle {{ trigger.event.data.data.changes.salle.current }}.

    default:
      # Cas général : Autre modification (heure, prof...)
      - action: notify.notify
        data:
          title: "📅 Emploi du temps modifié - {{ trigger.event.data.child_name }}"
          message: >-
            Modification sur le cours de {{ trigger.event.data.data.lesson }}
            le {{ as_timestamp(trigger.event.data.data.start) | timestamp_custom('%d/%m à %H:%M') }}.
```

---

### Exemple 4 : Alerte absence ou retard injustifié

Avertit rapidement les parents en cas d'absence ou de retard non justifié.

```yaml
alias: "Ecole Directe - Alerte Absence ou Retard"
description: "Notification parentale en cas d'absence ou retard"
mode: parallel
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_absence
    id: absence
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_retard
    id: retard
action:
  - action: notify.notify
    data:
      title: >-
        {% if trigger.id == 'absence' %}
          🚨 Absence constatée - {{ trigger.event.data.child_name }}
        {% else %}
          ⏱️ Retard signalé - {{ trigger.event.data.child_name }}
        {% endif %}
      message: >-
        {{ trigger.event.data.data.display_date }}
        {% if trigger.event.data.data.motif %}
        Motif : {{ trigger.event.data.data.motif }}
        {% endif %}
        Statut : {{ 'Justifié' if trigger.event.data.data.justifie else 'NON JUSTIFIÉ' }}
```

---

### Exemple 5 : Alerte de nouvelle sanction ou d'encouragement

```yaml
alias: "Ecole Directe - Sanctions et Encouragements"
description: "Notification de vie scolaire pour les sanctions ou récompenses"
mode: parallel
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_sanction
    id: sanction
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_encouragement
    id: encouragement
action:
  - choose:
      - conditions:
          - condition: trigger
            id: sanction
        sequence:
          - action: notify.notify
            data:
              title: "⚠️ Nouvelle sanction - {{ trigger.event.data.child_name }}"
              message: >-
                {{ trigger.event.data.data.libelle }} : {{ trigger.event.data.data.motif }}
                {{ trigger.event.data.data.commentaire | default('', true) }}

      - conditions:
          - condition: trigger
            id: encouragement
        sequence:
          - action: notify.notify
            data:
              title: "🎉 Félicitations - {{ trigger.event.data.child_name }}"
              message: >-
                {{ trigger.event.data.data.motif }} : {{ trigger.event.data.data.libelle }}
                {{ trigger.event.data.data.commentaire | default('', true) }}
```

---

### Exemple 6 : Alerte double authentification QCM requise

Alerte par notification persistante lorsqu'un challenge 2FA doit être renseigné pour reconnecter l'intégration.

```yaml
alias: "Ecole Directe - Défi QCM 2FA requis"
description: "Avertit l'administrateur qu'une validation QCM est attendue"
mode: single
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_qcm
action:
  - action: notify.persistent_notification
    data:
      title: "🔐 Double authentification Ecole Directe requise"
      message: >-
        Une nouvelle question de sécurité a été soumise par Ecole Directe.
        Veuillez vous rendre dans vos entités Ecole Directe pour sélectionner
        les réponses dans les entités 'select' correspondantes, puis recharger l'intégration.
```

---

### Exemple 7 : Automatisation centralisée multi-événements

Regroupe tous les événements de l'intégration dans une seule automatisation claire organisée par `trigger_id`.

```yaml
alias: "Ecole Directe - Gestionnaire centralisé d'événements"
description: "Rassemble toutes les notifications Ecole Directe en une seule règle"
mode: queued
trigger:
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_note
    id: note
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_devoir
    id: devoir
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: edt_changement
    id: edt
  - trigger: event
    event_type: ecole_directe_event
    event_data:
      type: new_formulaire
    id: formulaire
action:
  - choose:
      - conditions:
          - condition: trigger
            id: note
        sequence:
          - action: notify.notify
            data:
              title: "📝 Note ({{ trigger.event.data.child_name }})"
              message: "{{ trigger.event.data.data.matiere }} : {{ trigger.event.data.data.note_sur }}"

      - conditions:
          - condition: trigger
            id: devoir
        sequence:
          - action: notify.notify
            data:
              title: "📚 Devoir ({{ trigger.event.data.child_name }})"
              message: "{{ trigger.event.data.data.matiere }} : {{ trigger.event.data.data.short_description }}"

      - conditions:
          - condition: trigger
            id: edt
        sequence:
          - action: notify.notify
            data:
              title: "📅 Emploi du temps ({{ trigger.event.data.child_name }})"
              message: "Changement détecté pour le cours de {{ trigger.event.data.data.lesson }}."

      - conditions:
          - condition: trigger
            id: formulaire
        sequence:
          - action: notify.notify
            data:
              title: "📄 Nouveau formulaire administratif"
              message: "Un nouveau formulaire est disponible : {{ trigger.event.data.data.titre }}."
```

---

## 🛠️ Astuces et bonnes pratiques

### 1. Tester les événements en direct

Vous pouvez observer et tester les événements émis par l'intégration directement depuis l'interface Home Assistant :
1. Rendez-vous dans **Outils de développement** > **Événements**.
2. Dans le champ **Écouter les événements**, saisissez `ecole_directe_event`.
3. Cliquez sur **Commencer à écouter**.
4. Lors du prochain rafraîchissement des données (ou en forçant la mise à jour du coordinateur), les événements capturés s'afficheront en temps réel avec l'arborescence complète de leur charge utile JSON.

### 2. Filtrer par enfant en cas de fratrie

Si plusieurs enfants sont enregistrés sur le même compte, vous pouvez filtrer les automatisations sur un enfant spécifique en ajoutant une condition sur `child_name` :

```yaml
condition:
  - condition: template
    value_template: "{{ trigger.event.data.child_name == 'Lucas Dupont' }}"
```

### 3. Sécuriser les champs optionnels avec Jinja2

Certains champs (tels que `commentaire`, `documents`, `changes`) peuvent être absents ou vides selon les données renvoyées par l'établissement. Utilisez le filtre Jinja2 `default()` pour éviter toute erreur de template :

```jinja
{{ trigger.event.data.data.commentaire | default('Aucun commentaire', true) }}
```
