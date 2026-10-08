"""Tests for the ecole_directe homeworks sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.ecole_directe.const import DOMAIN, EVENT_TYPE
from custom_components.ecole_directe.sensor.homeworks import (
    ENTITY_DESCRIPTIONS,
    EDHomeworksSensor,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ecole_directe.api.client import EDEleve


@pytest.mark.unit
def test_homeworks_sensor_naming(mock_eleve: EDEleve) -> None:
    """Test homeworks sensor name and unique_id according to suffixes."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"session": MagicMock(identifiant="test_user")}
    description = ENTITY_DESCRIPTIONS[0]

    suffix_expected_names = {
        "_1": "Devoirs - Semaine en cours",
        "_2": "Devoirs - Semaine suivante",
        "_3": "Devoirs - Semaine après suivante",
        "_today": "Devoirs - Aujourd'hui",
        "_tomorrow": "Devoirs - Demain",
        "_next_day": "Devoirs - Jour suivant",
        "": "Devoirs",
        "_unknown": "Devoirs",
    }

    for suffix, expected_name in suffix_expected_names.items():
        sensor = EDHomeworksSensor(
            coordinator=mock_coordinator,
            entity_description=description,
            eleve=mock_eleve,
            suffix=suffix,
        )
        assert sensor.name == expected_name
        assert sensor.unique_id == f"ed_benjamin_no_name_devoirs{suffix}"


@pytest.mark.unit
def test_homeworks_sensor_device_info(mock_eleve: EDEleve) -> None:
    """Test homeworks sensor device_info attributes."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"session": MagicMock(identifiant="test_user")}
    description = ENTITY_DESCRIPTIONS[0]

    sensor = EDHomeworksSensor(
        coordinator=mock_coordinator,
        entity_description=description,
        eleve=mock_eleve,
        suffix="_today",
    )

    device_info = sensor.device_info
    assert device_info is not None
    assert (DOMAIN, "ED - Benjamin No Name") in device_info["identifiers"]
    assert device_info["name"] == "ED - Benjamin No Name"
    assert device_info["manufacturer"] == "Ecole Directe"
    assert device_info["model"] == "ED - Benjamin No Name"


@pytest.mark.unit
def test_homeworks_sensor_native_value_and_availability(
    mock_eleve: EDEleve,
    sample_homeworks: list[dict],
) -> None:
    """Test sensor native_value and available property under various conditions."""
    mock_coordinator = MagicMock()
    mock_coordinator.last_update_success = True
    key = "benjamin_no_name_homeworks_today"
    mock_coordinator.data = {
        "session": MagicMock(identifiant="test_user"),
        key: sample_homeworks,
    }
    description = ENTITY_DESCRIPTIONS[0]

    sensor = EDHomeworksSensor(
        coordinator=mock_coordinator,
        entity_description=description,
        eleve=mock_eleve,
        suffix="_today",
    )

    # When key exists and data has the expected number of items
    assert sensor.native_value == len(sample_homeworks)
    assert sensor.available is True

    # When data list is None
    mock_coordinator.data[key] = None
    assert sensor.native_value == 0
    assert sensor.available is True

    # When key is not in coordinator.data
    del mock_coordinator.data[key]
    assert sensor.native_value == "unavailable"
    assert sensor.available is False

    # When coordinator update failed
    mock_coordinator.data[key] = sample_homeworks
    mock_coordinator.last_update_success = False
    assert sensor.available is False


@pytest.mark.unit
def test_homeworks_sensor_extra_state_attributes(
    mock_eleve: EDEleve,
    sample_homeworks: list[dict],
) -> None:
    """Test extra_state_attributes sorting and 'A faire' count."""
    mock_coordinator = MagicMock()
    key = "benjamin_no_name_homeworks_1"
    mock_coordinator.data = {
        "session": MagicMock(identifiant="test_user"),
        key: sample_homeworks,
    }
    description = ENTITY_DESCRIPTIONS[0]

    sensor = EDHomeworksSensor(
        coordinator=mock_coordinator,
        entity_description=description,
        eleve=mock_eleve,
        suffix="_1",
    )

    attrs = sensor.extra_state_attributes
    expected_incomplete_homeworks = 2
    assert attrs["prenom"] == "Benjamin"
    assert attrs["A faire"] == expected_incomplete_homeworks

    devoirs = attrs["Devoirs"]
    expected_devoir_count = len(sample_homeworks)
    assert len(devoirs) == expected_devoir_count
    # Check that devoirs are sorted by date
    assert devoirs[0]["date"] <= devoirs[1]["date"] <= devoirs[2]["date"]


@pytest.mark.unit
def test_homeworks_sensor_attributes_when_key_missing(
    mock_eleve: EDEleve,
) -> None:
    """Test attributes when homework key does not exist in coordinator data."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"session": MagicMock(identifiant="test_user")}
    description = ENTITY_DESCRIPTIONS[0]

    sensor = EDHomeworksSensor(
        coordinator=mock_coordinator,
        entity_description=description,
        eleve=mock_eleve,
        suffix="_tomorrow",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["prenom"] == "Benjamin"
    assert attrs["A faire"] == 0
    assert attrs["Devoirs"] == [
        {"Erreur": "benjamin_no_name_homeworks_tomorrow n'existe pas."}
    ]


@pytest.mark.unit
def test_homeworks_sensor_attributes_too_big(
    mock_eleve: EDEleve,
) -> None:
    """Test oversized attributes handling and saving to coordinator store."""
    mock_coordinator = MagicMock()
    key = "benjamin_no_name_homeworks"
    large_payload = [
        {
            "devoir_id": i,
            "date": f"2025-11-{i:02d}",
            "matiere": "MATHEMATIQUES",
            "short_description": "X" * 500,
            "description": "Y" * 2000,
            "effectue": False,
            "interrogation": False,
            "documents": [],
        }
        for i in range(1, 30)
    ]
    mock_coordinator.data = {
        "session": MagicMock(identifiant="test_user"),
        key: large_payload,
    }
    mock_coordinator.async_save_attributes = MagicMock()

    sensor = EDHomeworksSensor(
        coordinator=mock_coordinator,
        entity_description=ENTITY_DESCRIPTIONS[0],
        eleve=mock_eleve,
        suffix="",
    )

    attrs = sensor.extra_state_attributes
    mock_coordinator.async_save_attributes.assert_called_once_with(key, large_payload)
    assert attrs["Devoirs"] == [{"stored_in_store": True, "store_key": key}]
    expected_homework_count = 29
    assert attrs["A faire"] == expected_homework_count


@pytest.mark.integration
async def test_homeworks_sensors_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    mock_eleve: EDEleve,
    sample_homeworks: list[dict],
) -> None:
    """Test setting up ecole_directe config entry creates homework sensors."""
    mock_api_client.get_homeworks.return_value = sample_homeworks

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    # Verify device is registered
    device = device_reg.async_get_device(
        identifiers={(DOMAIN, "ED - Benjamin No Name")}
    )
    assert device is not None
    assert device.name == "ED - Benjamin No Name"
    assert device.manufacturer == "Ecole Directe"

    # Verify all 7 homework sensors exist in entity registry
    expected_suffixes = ["_1", "_2", "_3", "_today", "_tomorrow", "_next_day", ""]
    for suffix in expected_suffixes:
        unique_id = f"ed_benjamin_no_name_devoirs{suffix}"
        entry = entity_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entry is not None, f"Entity with unique_id {unique_id} not found"

        state = hass.states.get(entry)
        assert state is not None
        assert state.state != STATE_UNAVAILABLE
        assert "Devoirs" in state.attributes
        assert "A faire" in state.attributes
        assert state.attributes["prenom"] == "Benjamin"


@pytest.mark.integration
async def test_homeworks_sensors_not_created_without_module(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    mock_eleve_no_homeworks: EDEleve,
) -> None:
    """Test that student without CAHIER_DE_TEXTES module does not get homework sensors."""
    mock_api_client.eleves = [mock_eleve_no_homeworks]

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    for suffix in ["_1", "_2", "_3", "_today", "_tomorrow", "_next_day", ""]:
        unique_id = f"ed_arthur_no_name_devoirs{suffix}"
        entry = entity_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entry is None


@pytest.mark.integration
async def test_service_devoir_effectue_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test calling devoir_effectue service action marks homework as done."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "devoir_effectue",
        {
            "eleve_id": "2232",
            "devoir_id": 2641,
            "effectue": True,
        },
        blocking=True,
    )

    mock_api_client.post_homework.assert_called_once_with(
        eleve_id="2232",
        devoir_id=2641,
        effectue=True,
    )


@pytest.mark.integration
async def test_service_devoir_effectue_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test error handling when devoir_effectue service action fails."""
    mock_api_client.post_homework = AsyncMock(
        side_effect=Exception("API communication error")
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match="Failed to mark homework as done"):
        await hass.services.async_call(
            DOMAIN,
            "devoir_effectue",
            {
                "eleve_id": "2232",
                "devoir_id": 2641,
                "effectue": True,
            },
            blocking=True,
        )


@pytest.mark.integration
async def test_homeworks_event_fired_on_new_homework(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    mock_eleve: EDEleve,
    sample_homeworks: list[dict],
) -> None:
    """Test that ecole_directe_event is fired when a new homework is detected."""
    events = []
    hass.bus.async_listen(EVENT_TYPE, lambda event: events.append(event.data))

    # First update: 2 homeworks
    initial_homeworks = sample_homeworks[:2]
    mock_api_client.get_homeworks.return_value = initial_homeworks

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    # Second update: 3 homeworks (new homework added)
    mock_api_client.get_homeworks.return_value = sample_homeworks
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    new_devoir_events = [e for e in events if e.get("type") == "new_devoir"]
    assert len(new_devoir_events) == 1
    assert new_devoir_events[0]["child_name"] == "Benjamin No Name"
    expected_devoir_id = 2664
    assert new_devoir_events[0]["data"]["devoir_id"] == expected_devoir_id
