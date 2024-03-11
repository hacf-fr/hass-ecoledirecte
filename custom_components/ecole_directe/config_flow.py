"""Config flow for Ecole Directe integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from datetime import time

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback

from .ecoleDirecte_helper import *

from .const import (
    DOMAIN,
    DEFAULT_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA_UP = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("account_type"): vol.In({'famille': 'Famille', 'eleve': 'Elève'})
    }
)

@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecole Directe."""

    VERSION = 1
    ecoleDirecte_session = None

    def __init__(self) -> None:
        self._user_inputs: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("ED - Setup process initiated by user.")
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _LOGGER.debug("ED - User Input: %s", user_input)
                self._user_inputs.update(user_input)
                session = await self.hass.async_add_executor_job(get_ecoledirecte_session, self._user_inputs)

                if session is None:
                    raise InvalidAuth

                _LOGGER.debug(f"ED - User Inputs UP: {self._user_inputs} - identifiant: [{session.identifiant}]")
                return self.async_create_entry(title=session.identifiant, data=self._user_inputs)
            except InvalidAuth:
                errors["base"] = "invalid_auth"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA_UP, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("refresh_interval", default=self.config_entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)): int,
                }
            ),
        )