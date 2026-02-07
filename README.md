# Integration Ecole directe pour Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

[![BuyMeCoffee][buymecoffeebadge]][giga77]

**✨ Develop in the cloud:** Want to contribute or customize this integration? Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Giga77/hass-ecoledirecte?quickstart=1)

- [Installation](#Installation)
  - [Installation via l'interface utilisateur via HACS](#Installation-via-linterface-utilisateur-via-hacs)
  - [Installation manuelle](<#Installation-manuelle>)
- [Configuration](#Configuration)
- [Utilisation](#Utilisation)

- **Easy Setup**: Simple configuration through the UI - no YAML required
- **Reconfigurable**: Change credentials anytime without removing the integration
- **Options Flow**: Adjust settings like update interval after setup
- **Custom Services**: Advanced control with built-in service calls

## 🚀 Installation

### Installation via l'interface utilisateur via HACS

1. Cliquez sur ce lien : [HACS: Ecole Directe](https://my.home-assistant.io/redirect/hacs_repository/?owner=hacf-fr&repository=hass-ecoledirecte)
2. Cliquez sur le bouton `Open link`.
3. Cliquez sur le bouton `Télécharger` en bas à droite, puis une deuxième fois sur `Télécharger`.
5. Il faut ensuite redémarrer Home Assistant.

### Installation manuelle
Copier le répertoire ecole_directe de la dernière release dans le répertoire custom_components de votre répertoire config. Redémarrer Home Assistant

## ✨ Configuration

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
Dans vos dashboards, vous pouvez utiliser les cartes [EcoleDirecteHACards](https://github.com/hacf-fr/EcoleDirecteHACards).
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

## Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ecole_directe: debug
```

## Custom Services

The integration provides services for advanced automation:

### `ecole_directe.example_action`

Perform a custom action (customize this for your needs).

**Example:**

```yaml
service: ecole_directe.example_action
data:
  # Add your parameters here
```

### `ecole_directe.reload_data`

Manually refresh data from the API without waiting for the update interval.

**Example:**

```yaml
service: ecole_directe.reload_data
```

Use these services in automations or scripts for more control.

## Configuration Options

### During Setup

Name | Required | Description
-- | -- | --
Username | Yes | Your account username
Password | Yes | Your account password

### After Setup (Options)

You can change these anytime by clicking **Configure**:

Name | Default | Description
-- | -- | --
Update Interval | 1 hour | How often to refresh data
Enable Debugging | Off | Enable extra debug logging

## Troubleshooting

### Authentication Issues

#### Reauthentication

If your credentials expire or change, Home Assistant will automatically prompt you to reauthenticate:

1. Go to **Settings** → **Devices & Services**
2. Look for **"Action Required"** or **"Configuration Required"** message on the integration
3. Click **"Reconfigure"** or follow the prompt
4. Enter your updated credentials
5. Click Submit

The integration will automatically resume normal operation with the new credentials.

#### Manual Credential Update

You can also update credentials at any time without waiting for an error:

1. Go to **Settings** → **Devices & Services**
2. Find **Ecole Directe**
3. Click the **3 dots menu** → **Reconfigure**
4. Enter new username/password
5. Click Submit

#### Connection Status

Monitor your connection status with the **API Connection** binary sensor:

- **On** (Connected): Integration is receiving data normally
- **Off** (Disconnected): Connection lost or authentication failed
  - Check the binary sensor attributes for diagnostic information
  - Verify credentials if authentication failed
  - Check network connectivity

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ecole_directe: debug
```

### Common Issues

#### Authentication Errors

If you receive authentication errors:

1. Verify your username and password are correct
2. Check that your account has the necessary permissions
3. Wait for the automatic reauthentication prompt, or manually reconfigure
4. Check the API Connection binary sensor for status

#### Device Not Responding

If your device is not responding:

1. Check the **API Connection** binary sensor - it should be "On"
2. Check your network connection
3. Verify the device is powered on
4. Check the integration diagnostics (Settings → Devices & Services → Ecole Directe → 3 dots → Download diagnostics)

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you have suggestions or improvements.

### 🛠️ Development Setup

Want to contribute or customize this integration? You have two options:

#### Cloud Development (Recommended)

The easiest way to get started - develop directly in your browser with GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Giga77/hass-ecoledirecte?quickstart=1)

- ✅ Zero local setup required
- ✅ Pre-configured development environment
- ✅ Home Assistant included for testing
- ✅ 60 hours/month free for personal accounts

#### Local Development

Prefer working on your machine? You'll need:

- Docker Desktop
- VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Then:

1. Clone this repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted

Both options give you the same fully-configured development environment with Home Assistant, Python 3.13, and all necessary tools.

---

## 🤖 AI-Assisted Development

> **ℹ️ Transparency Notice**
>
> This integration was developed with assistance from AI coding agents (GitHub Copilot, Claude, and others). While the codebase follows Home Assistant Core standards, AI-generated code may not be reviewed or tested to the same extent as manually written code.
>
> AI tools were used to:
>
> - Generate boilerplate code following Home Assistant patterns
> - Implement standard integration features (config flow, coordinator, entities)
> - Ensure code quality and type safety
> - Write documentation and comments
>
> Please be aware that AI-assisted development may result in unexpected behavior or edge cases that haven't been thoroughly tested. If you encounter any issues, please [open an issue](../../issues) on GitHub.
>
> *Note: This section can be removed or modified if AI assistance was not used in your integration's development.*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@Giga77][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/hacf-fr/hass-ecoledirecte.svg?style=for-the-badge
[commits]: https://github.com/hacf-fr/hass-ecoledirecte/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/hacf-fr/hass-ecoledirecte.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40Giga77-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/hacf-fr/hass-ecoledirecte.svg?style=for-the-badge
[releases]: https://github.com/hacf-fr/hass-ecoledirecte/releases
[user_profile]: https://github.com/Giga77

[buymecoffee]: https://www.buymeacoffee.com/giga77
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
