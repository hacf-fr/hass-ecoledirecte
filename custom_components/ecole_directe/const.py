"""Constants for the Ecole Directe integration."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "ecole_directe"
EVENT_TYPE = DOMAIN + "_event"
FILENAME_QCM = "ecoledirecte_qcm.json"
INTEGRATION_PATH = "/custom_components/" + DOMAIN + "/"
PLATFORMS = [Platform.SENSOR]

# default values for options
DEFAULT_REFRESH_INTERVAL = 30
GRADES_TO_DISPLAY = 15
VIE_SCOLAIRE_TO_DISPLAY = 10
HOMEWORK_DESC_MAX_LENGTH = 125
DEFAULT_ALLOW_NOTIFICATION = False
DEFAULT_LUNCH_BREAK_TIME = "13:00"
MAX_STATE_ATTRS_BYTES = 16384
AUGUST = 8

DEFAULT_ENABLE_DEBUGGING = False
FAKE_ON = False
