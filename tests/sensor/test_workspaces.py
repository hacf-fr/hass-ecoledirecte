# Copyright (c) 2024-2026
# SPDX-License-Identifier: MIT

"""Tests for the ecole_directe workspace sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er

from custom_components.ecole_directe.const import DOMAIN, EVENT_TYPE
from custom_components.ecole_directe.sensor.workspaces import (
    EDWorkspaceSensor,
    _get_workspace_id,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def sample_workspace() -> dict:
    """Fixture for a sample workspace item."""
    return {
        "id": 101,
        "titre": "Mathématiques 4ème",
        "description": "Espace de travail de mathématiques",
        "ouvert": True,
        "estMembre": True,
    }


@pytest.fixture
def sample_activities() -> list[dict]:
    """Fixture for sample workspace activities."""
    return [
        {
            "id": 1,
            "descriptif": "Nouvelle ressource ajoutée",
            "date": "2026-10-30 10:00:00",
        },
        {
            "id": 2,
            "descriptif": "Exercice déposé",
            "date": "2026-10-30 11:00:00",
        },
    ]


@pytest.fixture
def sample_postits() -> list[dict]:
    """Fixture for sample workspace post-its."""
    return [
        {
            "id": 10,
            "contenu": "Penser à réviser le chapitre 2",
            "dateCreation": "2026-10-30",
        }
    ]


@pytest.mark.unit
def test_workspace_sensor_initialization(sample_workspace: dict) -> None:
    """Test workspace sensor name, unique_id and device_info."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.config_entry.title = "Famille Dupont"

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace=sample_workspace,
        workspace_id="101",
    )

    assert sensor.name == "Mathématiques 4ème"
    assert sensor.unique_id == "test_entry_id_espace_101"
    assert sensor.device_info is not None
    identifiers = sensor.device_info.get("identifiers")
    assert identifiers is not None
    assert (DOMAIN, "ED - Famille Dupont") in identifiers


@pytest.mark.unit
def test_workspace_sensor_fallback_name() -> None:
    """Test workspace sensor fallback name when titre is missing."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.config_entry.title = "Famille Dupont"

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace={"id": 102},
        workspace_id="102",
    )

    assert sensor.name == "Espace 102"


@pytest.mark.unit
def test_workspace_sensor_native_value(
    sample_workspace: dict, sample_activities: list[dict]
) -> None:
    """Test workspace sensor native_value returns activity count."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.data = {
        "wk_activities": {
            "101": sample_activities,
        }
    }

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace=sample_workspace,
        workspace_id="101",
    )

    assert sensor.native_value == len(sample_activities)

    # When no activities exist
    mock_coordinator.data = {"wk_activities": {}}
    assert sensor.native_value == 0

    # When coordinator data is None
    mock_coordinator.data = None
    assert sensor.native_value == 0


@pytest.mark.unit
def test_workspace_sensor_attributes(
    sample_workspace: dict,
    sample_activities: list[dict],
    sample_postits: list[dict],
) -> None:
    """Test workspace sensor extra_state_attributes."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.data = {
        "workspaces": [sample_workspace],
        "wk_activities": {"101": sample_activities},
        "wk_postits": {"101": sample_postits},
    }

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace=sample_workspace,
        workspace_id="101",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["Espace de travail"] == sample_workspace
    assert attrs["Activités"] == sample_activities
    assert attrs["Post-it"] == sample_postits


@pytest.mark.unit
def test_workspace_sensor_attributes_stored_in_store(sample_workspace: dict) -> None:
    """Test workspace sensor stores attributes when too big."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.data = {
        "workspaces": [sample_workspace],
        "wk_activities": {"101": []},
        "wk_postits": {"101": []},
    }

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace=sample_workspace,
        workspace_id="101",
    )

    with patch(
        "custom_components.ecole_directe.sensor.workspaces.is_too_big",
        return_value=True,
    ):
        attrs = sensor.extra_state_attributes
        assert attrs["stored_in_store"] is True
        assert attrs["store_key"] == "test_entry_id_espace_101"
        mock_coordinator.async_save_attributes.assert_called_once()


@pytest.mark.unit
def test_workspace_sensor_availability(sample_workspace: dict) -> None:
    """Test workspace sensor availability."""
    mock_coordinator = MagicMock()
    mock_coordinator.config_entry.entry_id = "test_entry_id"
    mock_coordinator.last_update_success = True
    mock_coordinator.data = {
        "workspaces": [sample_workspace],
    }

    sensor = EDWorkspaceSensor(
        coordinator=mock_coordinator,
        workspace=sample_workspace,
        workspace_id="101",
    )

    assert sensor.available is True

    # Unavailable when last_update_success is False
    mock_coordinator.last_update_success = False
    assert sensor.available is False

    # Unavailable when workspace removed from data
    mock_coordinator.last_update_success = True
    mock_coordinator.data = {"workspaces": []}
    assert sensor.available is False


@pytest.mark.unit
def test_get_workspace_id_keys() -> None:
    """Test _get_workspace_id identifier resolution across fallback keys."""
    assert _get_workspace_id({"id": 101}) == "101"
    assert _get_workspace_id({"idEspace": 102}) == "102"
    assert _get_workspace_id({"espaceId": 103}) == "103"
    assert _get_workspace_id({"workspaceId": 104}) == "104"
    assert _get_workspace_id({}) is None


@pytest.mark.integration
async def test_workspace_sensors_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    sample_workspace: dict,
    sample_activities: list[dict],
    sample_postits: list[dict],
) -> None:
    """Test setting up workspace sensor platform from config entry."""
    mock_api_client.get_workspaces.return_value = [sample_workspace]
    mock_api_client.get_workspace_activities.return_value = sample_activities
    mock_api_client.get_workspace_postits.return_value = sample_postits

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    unique_id = f"{mock_config_entry.entry_id}_espace_101"
    entry = entity_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entry is not None

    state = hass.states.get(entry)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert int(state.state) == len(sample_activities)
    assert "Espace de travail" in state.attributes
    assert "Activités" in state.attributes
    assert "Post-it" in state.attributes


@pytest.mark.integration
async def test_workspace_events_fired(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    sample_workspace: dict,
    sample_activities: list[dict],
    sample_postits: list[dict],
) -> None:
    """Test that events are fired on workspace changes, new activities and new postits."""
    events = []
    hass.bus.async_listen(EVENT_TYPE, lambda event: events.append(event.data))

    # First update: 1 workspace, 1 activity, 1 post-it
    mock_api_client.get_workspaces.return_value = [sample_workspace]
    mock_api_client.get_workspace_activities.return_value = sample_activities[:1]
    mock_api_client.get_workspace_postits.return_value = sample_postits[:1]

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    # Initial load should not trigger differential events
    assert len(events) == 0

    # Second update: status change on workspace, add new activity and new post-it
    updated_workspace = dict(sample_workspace)
    updated_workspace["ouvert"] = False

    expected_postit_id = 11
    new_postit = {
        "id": expected_postit_id,
        "contenu": "Nouveau post-it",
        "dateCreation": "2026-10-31",
    }
    mock_api_client.get_workspaces.return_value = [updated_workspace]
    mock_api_client.get_workspace_activities.return_value = (
        sample_activities  # now 2 activities
    )
    mock_api_client.get_workspace_postits.return_value = [*sample_postits, new_postit]

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    activity_events = [e for e in events if e.get("type") == "new_activity"]
    postit_events = [e for e in events if e.get("type") == "new_postit"]

    assert len(activity_events) == 1
    assert activity_events[0]["data"]["id"] == sample_activities[1]["id"]

    assert len(postit_events) == 1
    assert postit_events[0]["data"]["id"] == expected_postit_id


@pytest.mark.integration
async def test_dynamic_workspace_discovery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    sample_workspace: dict,
) -> None:
    """Test dynamically discovered workspace adds a new sensor without reloading."""
    mock_api_client.get_workspaces.return_value = [sample_workspace]
    mock_api_client.get_workspace_activities.return_value = []
    mock_api_client.get_workspace_postits.return_value = []

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    entry1 = entity_reg.async_get_entity_id(
        "sensor", DOMAIN, f"{mock_config_entry.entry_id}_espace_101"
    )
    assert entry1 is not None

    # Discover a second workspace on refresh
    second_workspace = {
        "id": 202,
        "titre": "Histoire 4ème",
        "ouvert": True,
        "estMembre": True,
    }
    mock_api_client.get_workspaces.return_value = [sample_workspace, second_workspace]

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entry2 = entity_reg.async_get_entity_id(
        "sensor", DOMAIN, f"{mock_config_entry.entry_id}_espace_202"
    )
    assert entry2 is not None
    state2 = hass.states.get(entry2)
    assert state2 is not None
    assert state2.attributes["Espace de travail"]["titre"] == "Histoire 4ème"
