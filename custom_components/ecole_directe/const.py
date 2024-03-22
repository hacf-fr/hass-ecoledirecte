"""Constants for the Ecole Directe integration."""

from homeassistant.const import Platform

DOMAIN = "ecole_directe"
EVENT_TYPE = "ecole_directe_event"
PLATFORMS = [Platform.SENSOR]

# default values for options
DEFAULT_REFRESH_INTERVAL = 30
GRADES_TO_DISPLAY = 15
HOMEWORK_DESC_MAX_LENGTH = 125
