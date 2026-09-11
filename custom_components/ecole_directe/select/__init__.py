"""Select platform for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntityDescription
from homeassistant.core import Event, callback

from custom_components.ecole_directe.const import EVENT_TYPE, LOGGER

from .question_2fa import QuestionSelect

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ecole_directe.data import (
        EDConfigEntry,
    )


ENTITY_DESCRIPTION = SelectEntityDescription(
    key="qcm_question",
    name="QCM Question",
    icon="mdi:help-circle",
    has_entity_name=False,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator = entry.runtime_data.coordinator

    initial_data = coordinator.data or {}
    questions = set(initial_data.get("qcm_questions", {}))
    LOGGER.debug("Setting up QCM select entities for questions: %s", questions)

    entities: list[QuestionSelect] = [
        QuestionSelect(coordinator, ENTITY_DESCRIPTION, question)
        for question in questions
    ]

    if entities:
        async_add_entities(entities)

    # Track registered questions to prevent duplicates
    registered_questions = set(questions)

    @callback
    def _handle_new_qcm_event(event: Event) -> None:
        if event.data.get("type") != "new_qcm":
            return
        LOGGER.debug("Received new QCM event: %s", event.data)

        qcm_json = event.data.get("qcm_json", {})
        new_entities: list[QuestionSelect] = []

        LOGGER.debug("qcm_json: %s", qcm_json)

        for question in qcm_json:
            if question in registered_questions:
                continue
            LOGGER.debug("Adding new QCM question select entity: %s", question)
            new_entities.append(
                QuestionSelect(coordinator, ENTITY_DESCRIPTION, question)
            )
            registered_questions.add(question)

        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(hass.bus.async_listen(EVENT_TYPE, _handle_new_qcm_event))
