"""
Config flow schemas.

Schemas for the main configuration flow steps:
- User setup
- Reconfiguration
- Reauthentication

When this file grows too large (>300 lines), consider splitting into:
- user.py: User setup schemas
- reauth.py: Reauthentication schemas
- reconfigure.py: Reconfiguration schemas
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector

from custom_components.ecole_directe.const import (
    DEFAULT_ALLOW_NOTIFICATION,
    FILENAME_QCM,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_user_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """
    Get schema for user step (initial setup).

    Args:
        defaults: Optional dictionary of default values to pre-populate the form.

    Returns:
        Voluptuous schema for user credentials input.

    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, vol.UNDEFINED),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
            vol.Optional("qcm_filename", default=FILENAME_QCM): str,
            vol.Optional(
                "allow_notification",
                default=DEFAULT_ALLOW_NOTIFICATION,
            ): bool,
        },
    )


def get_reconfigure_schema(username: str) -> vol.Schema:
    """
    Get schema for reconfigure step.

    Args:
        username: Current username to pre-fill in the form.

    Returns:
        Voluptuous schema for reconfiguration.

    """
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=username,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(
                CONF_PASSWORD,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
            vol.Optional("qcm_filename", default=FILENAME_QCM): str,
            vol.Optional(
                "allow_notification",
                default=DEFAULT_ALLOW_NOTIFICATION,
            ): bool,
        },
    )


def get_reauth_schema(username: str) -> vol.Schema:
    """
    Get schema for reauthentication step.

    Args:
        username: Current username to pre-fill in the form.

    Returns:
        Voluptuous schema for reauthentication.

    """
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=username,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            ),
            vol.Required(
                CONF_PASSWORD,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                ),
            ),
            vol.Optional("qcm_filename", default=FILENAME_QCM): str,
        },
    )


__all__ = [
    "get_reauth_schema",
    "get_reconfigure_schema",
    "get_user_schema",
]
