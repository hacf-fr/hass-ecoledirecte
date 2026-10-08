"""Fixtures for ecole_directe tests."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure custom_components is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ecole_directe.api.client import EDEleve
from custom_components.ecole_directe.const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    """Enable custom integrations in Home Assistant."""
    return


@pytest.fixture
def mock_eleve() -> EDEleve:
    """Fixture for a mock student with homeworks module."""
    return EDEleve(
        modules=["CAHIER_DE_TEXTES"],
        data=None,
        establishment="College Victor Hugo",
        eleve_id="2232",
        first_name="Benjamin",
        last_name="No Name",
        classe_id="12",
        classe_name="4EME A",
        account_id_login=2232,
    )


@pytest.fixture
def mock_eleve_no_homeworks() -> EDEleve:
    """Fixture for a mock student without homeworks module."""
    return EDEleve(
        modules=["NOTES"],
        data=None,
        establishment="College Victor Hugo",
        eleve_id="2233",
        first_name="Arthur",
        last_name="No Name",
        classe_id="12",
        classe_name="4EME A",
        account_id_login=2233,
    )


@pytest.fixture
def sample_homeworks() -> list[dict]:
    """Fixture for sample homework items."""
    tomorrow = datetime.now(UTC).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=1)
    return [
        {
            "devoir_id": 2641,
            "date": tomorrow,
            "matiere": "HISTOIRE-GEOGRAPHIE",
            "short_description": "Apprendre la leçon",
            "description": "Apprendre la leçon sur la Première Guerre Mondiale",
            "effectue": False,
            "interrogation": False,
            "documents": [],
        },
        {
            "devoir_id": 2868,
            "date": tomorrow + timedelta(days=1),
            "matiere": "MATHEMATIQUES",
            "short_description": "Exercice 12 page 45",
            "description": "Faire les exercices 12 et 13 page 45",
            "effectue": True,
            "interrogation": False,
            "documents": [],
        },
        {
            "devoir_id": 2664,
            "date": tomorrow + timedelta(days=2),
            "matiere": "TECHNOLOGIE",
            "short_description": "Finir le projet",
            "description": "Terminer la modélisation 3D",
            "effectue": False,
            "interrogation": True,
            "documents": [],
        },
    ]


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Fixture for a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ecole Directe",
        data={
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            "account_type": "Famille",
        },
        options={
            "refresh_interval": 30,
            "decode_html": False,
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_api_client(mock_eleve: EDEleve) -> Generator[MagicMock]:
    """Fixture for a mocked EDApiClient."""
    with (
        patch(
            "custom_components.ecole_directe.EDApiClient",
            autospec=True,
        ) as mock_client_cls,
        patch(
            "custom_components.ecole_directe.coordinator.base.EDApiClient",
            new=mock_client_cls,
        ),
    ):
        mock_instance = mock_client_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.login = AsyncMock(
            return_value={"code": 200, "token": "test_token"}
        )
        mock_instance.close = AsyncMock()
        mock_instance.post_homework = AsyncMock(return_value=True)
        mock_instance.identifiant = "test_user"
        mock_instance.modules = ["CAHIER_DE_TEXTES"]
        mock_instance.eleves = [mock_eleve]
        mock_instance.current_account_id_login = 2232
        mock_instance.get_homeworks = AsyncMock(return_value=[])
        yield mock_instance
