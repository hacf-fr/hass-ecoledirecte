"""Constants for the Ecole Directe integration."""

import json
from logging import Logger, getLogger
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN: Final[str] = "ecole_directe"
ATTRIBUTION: Final[str] = "Data provided by Ecole Directe API"
EVENT_TYPE: Final[str] = DOMAIN + "_event"
FILENAME_QCM: Final[str] = "ecoledirecte_qcm.json"
INTEGRATION_PATH: Final[str] = "/custom_components/" + DOMAIN + "/"
PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]

# default values for options
DEFAULT_REFRESH_INTERVAL: Final[int] = 30
GRADES_TO_DISPLAY: Final[int] = 15
VIE_SCOLAIRE_TO_DISPLAY: Final[int] = 10
HOMEWORK_DESC_MAX_LENGTH: Final[int] = 125
DEFAULT_ALLOW_NOTIFICATION: Final[bool] = False
DEFAULT_LUNCH_BREAK_TIME: Final[str] = "13:00"
MAX_STATE_ATTRS_BYTES: Final[int] = 16384
AUGUST: Final[int] = 8

DEFAULT_ENABLE_DEBUGGING: Final[bool] = False
FAKE_ON: Final[bool] = False

# Lire la version depuis manifest.json
MANIFEST_PATH: Final[Path] = Path(__file__).parent / "manifest.json"
with Path.open(MANIFEST_PATH, encoding="utf-8") as f:
    INTEGRATION_VERSION: Final[str] = json.load(f).get("version", "v0.0.0")

# URL de base pour les ressources frontend
URL_BASE: Final[str] = "/" + DOMAIN

# Liste des modules JavaScript à enregistrer
JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Ecole Directe Cards",
        "filename": "EcoleDirecteHACards.js",
        "version": INTEGRATION_VERSION,
    },
]
