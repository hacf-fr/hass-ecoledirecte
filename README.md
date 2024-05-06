# Integration Ecole directe pour Home Assistant

![Version](https://img.shields.io/github/v/release/hacf-fr/hass-ecoledirecte?label=version) [![HACS: Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

- [Installation](#Installation)
  - [Installation via l'interface utilisateur via HACS](#Installation-via-linterface-utilisateur-via-hacs)
  - [Installation manuelle](<#Installation-manuelle>)
- [Configuration](#Configuration)
- [Utilisation](#Utilisation)


## Installation


### Installation via l'interface utilisateur via HACS

1. Depuis [HACS](https://hacs.xyz/) (Home Assistant Community Store), sélectionner `Intégrations`. Puis ouvrez le menu en haut à droite et utiliser l'option `Dépôts personnalisés` pour ajouter le dépôt de l'intégration.

2. Ajoutez l'adresse <https://github.com/hacf-fr/hass-ecoledirecte> avec pour catégorie `Intégration`, et faire `AJOUTER`. Le dépôt apparaît dans la liste.

3. La carte de ce `nouveau dépôt` va s'afficher, cliquez sur celle-ci puis `Télécharger` en bas à droite.

4. Laisser le choix de la dernière version et utiliser l'option `Télécharger`.

5. Il faut ensuite redémarrer Home Assistant.


### Installation manuelle
Copier le répertoire ecole_directe de la dernière release dans le répertoire custom_components de votre répertoire config. Redémarrer Home Assistant

## Configuration

Cliquer sur ce boutton:  
[![Open your Home Assistant instance and start setting up a new integration of a specific brand.](https://my.home-assistant.io/badges/brand.svg)](https://my.home-assistant.io/redirect/brand/?brand=ecole_directe)  

Ou aller dans :  
Paramètres > Appareils et services > Intégrations > Ajouter une intégration, et chercher "Ecole Directe"

Utiliser votre identifiant et mot de passe password :

![Ecole directe config flow](doc/config_flow_username_password.png)

## Utilisation

Cette intégration fournit plusieurs entités, toujours prefixées avec `ecole_directe_PRENOM_NOM` (où `PRENOM` et `NOM` sont remplacé).


| Sensor | Description |
|--------|-------------|
| `sensor.ecole_directe_PRENOM_NOM` | informations basique de l'enfant |
| `[...]_homework` | devoirs |
| `[...]_grades` | notes |
| `[...]_lessons` | emploi du temps  (in progress)|

Les entités sont mises à jour toutes les 30 minutes.

