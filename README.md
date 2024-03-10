# Ecole directe integration for Home Assistant

### Manual install

Copy the `ecole_directe` folder from latest release to the `custom_components` folder in your `config` folder.
Restart Home Assistant

## Configuration

Click on the following button:  
[![Open your Home Assistant instance and start setting up a new integration of a specific brand.](https://my.home-assistant.io/badges/brand.svg)](https://my.home-assistant.io/redirect/brand/?brand=ecole_directe)  

Or go to :  
Settings > Devices & Sevices > Integrations > Add Integration, and search for "Ecole Directe"

Use your username and password :
![Ecole directe config flow](doc/config_flow_username_password.png)

## Usage

This integration provides several sensors, always prefixed with `ecole_directe_FIRSTNAME_LASTNAME` (where `FIRSTNAME` and `LASTNAME` are replaced).


| Sensor | Description |
|--------|-------------|
| `sensor.ecole_directe_FIRSTNAME_LASTNAME` | basic informations about your child |
| `[...]_homework` | homework |
| `[...]_evaluations` | evaluations |

The sensors are updated every 30 minutes.
