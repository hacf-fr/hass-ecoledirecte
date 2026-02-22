"""Custom types for ecole_directe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import EDApiClient
    from .coordinator import EDDataUpdateCoordinator


type EDConfigEntry = ConfigEntry[EDData]


@dataclass
class EDData:
    """Data for ecole_directe."""

    session: EDApiClient
    coordinator: EDDataUpdateCoordinator
    integration: Integration
