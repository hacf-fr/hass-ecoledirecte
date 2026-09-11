"""Question select for ecole_directe."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from custom_components.ecole_directe.entity.base import EDEntity

if TYPE_CHECKING:
    from custom_components.ecole_directe.coordinator.base import (
        EDDataUpdateCoordinator,
    )


class QuestionSelect(SelectEntity, EDEntity):  # type: ignore[reportIncompatibleVariableOverride]
    """Question select class."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SelectEntityDescription,
        question: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator, entity_description)
        self._question = question
        # Override unique_id to include question hash for uniqueness
        question_hash = hashlib.sha256(self._question.encode()).hexdigest()[:8]
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_qcm_{question_hash}"
        )

    @property
    def name(self) -> str | None:  # type: ignore[reportIncompatibleVariableOverride]
        """Return the dynamic name for the QCM select entity."""
        return self._question

    @property
    def current_option(self) -> str | None:  # type: ignore[reportIncompatibleVariableOverride]
        """Return the currently selected option."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("qcm_selected_options", {}).get(self._question)

    @property
    def options(self) -> list[str]:  # type: ignore[reportIncompatibleVariableOverride]
        """Return the available options for the current question."""
        if self.coordinator.data is None:
            return []

        return [
            str(option)
            for option in self.coordinator.data.get("qcm_questions", {}).get(
                self._question, []
            )
        ]

    @property
    def available(self) -> bool:  # type: ignore[reportIncompatibleVariableOverride]
        """Return whether the QCM question is currently available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, str]:  # type: ignore[reportIncompatibleVariableOverride]
        """Return the state attributes for the QCM select."""
        if self.coordinator.data is None:
            return {}

        attributes: dict[str, str] = {
            "question": self._question,
        }
        selected_option = self.coordinator.data.get("qcm_selected_options", {}).get(
            self._question
        )
        if selected_option is not None:
            attributes["selected_option"] = selected_option
        return attributes

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self.coordinator.set_qcm_answer(self._question, option)
        self.async_write_ha_state()
