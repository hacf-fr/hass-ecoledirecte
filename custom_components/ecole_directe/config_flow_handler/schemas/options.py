"""
Options flow schemas.

Schemas for the options flow that allows users to modify settings
after initial configuration.

When adding many options, consider grouping them:
- basic_options.py: Common settings (update interval, debug mode)
- advanced_options.py: Advanced settings
- device_options.py: Device-specific settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.helpers import selector

from custom_components.ecole_directe.const import (
    DEFAULT_ENABLE_DEBUGGING,
    DEFAULT_LUNCH_BREAK_TIME,
    DEFAULT_REFRESH_INTERVAL,
    GRADES_TO_DISPLAY,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_options_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """
    Get schema for options flow.

    Args:
        defaults: Optional dictionary of current option values.

    Returns:
        Voluptuous schema for options configuration.

    """
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Optional(
                "refresh_interval",
                default=defaults.get("refresh_interval", DEFAULT_REFRESH_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=1440,
                    step=1,
                    unit_of_measurement="minutes",
                    mode=selector.NumberSelectorMode.BOX,
                ),
            ),
            vol.Optional(
                "lunch_break_time",
                default=defaults.get("lunch_break_time", DEFAULT_LUNCH_BREAK_TIME),
            ): str,
            vol.Optional(
                "decode_html",
                default=defaults.get("decode_html", False),
            ): bool,
            vol.Optional(
                "notes_affichees",
                default=defaults.get("notes_affichees", GRADES_TO_DISPLAY),
            ): int,
            vol.Optional(
                "enable_debugging",
                default=defaults.get("enable_debugging", DEFAULT_ENABLE_DEBUGGING),
            ): selector.BooleanSelector(),
        }
    )


__all__ = [
    "get_options_schema",
]
