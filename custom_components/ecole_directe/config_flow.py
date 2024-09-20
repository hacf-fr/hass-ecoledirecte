"""Config flow for Ecole Directe integration."""

from __future__ import annotations

import json
import os.path
import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback

from .ecole_directe_helper import (
    check_ecoledirecte_session,
)

from .const import (
    DEFAULT_ALLOW_NOTIFICATION,
    DEFAULT_LUNCH_BREAK_TIME,
    DOMAIN,
    DEFAULT_REFRESH_INTERVAL,
    FILENAME_QCM,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA_UP = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional("qcm_filename", default=FILENAME_QCM): str,
        vol.Optional(
            "allow_notification",
            default=DEFAULT_ALLOW_NOTIFICATION,
        ): bool,
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
                self._user_inputs.update(user_input)
                path = (
                    self.hass.config.config_dir
                    + "/"
                    + self._user_inputs["qcm_filename"]
                )
                if not os.path.isfile(path):
                    with open(
                        path,
                        "w",
                        encoding="utf-8",
                    ) as f:
                        json.dump({}, f, ensure_ascii=False, indent=4)

                await self.async_set_unique_id(self._user_inputs["username"])
                self._abort_if_unique_id_configured()

                session = await self.hass.async_add_executor_job(
                    check_ecoledirecte_session,
                    self._user_inputs,
                    self.hass.config.config_dir,
                    self.hass,
                )

                if not session:
                    raise InvalidAuth

                return self.async_create_entry(
                    title=self._user_inputs["username"], data=self._user_inputs
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA_UP, errors=errors
        )

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
    """Configuration of integration options"""

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
                    vol.Optional(
                        "refresh_interval",
                        default=self.config_entry.options.get(
                            "refresh_interval", DEFAULT_REFRESH_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        "lunch_break_time",
                        default=self.config_entry.options.get(
                            "lunch_break_time", DEFAULT_LUNCH_BREAK_TIME
                        ),
                    ): str,
                    vol.Optional(
                        "decode_html",
                        default=self.config_entry.options.get("decode_html", False),
                    ): bool,
                }
            ),
        )
