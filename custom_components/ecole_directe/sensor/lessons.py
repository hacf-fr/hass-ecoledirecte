"""Lessons sensor for ecole_directe."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from custom_components.ecole_directe.const import DEFAULT_LUNCH_BREAK_TIME, LOGGER
from custom_components.ecole_directe.sensor.generic import EDGenericSensor, is_too_big

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="lessons",
        translation_key="lessons",
        icon="mdi:calendar-clock",
        has_entity_name=True,
    ),
)


class EDLessonsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
        suffix: str,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            key=f"{eleve.get_fullname_lower()}_timetable{suffix}",
            name="Emploi du temps",
            eleve=eleve,
            state="len",
        )
        self._suffix = suffix
        self._attr_name = self.name
        self.unique_id = f"ed_{eleve.get_fullname_lower()}_edt{suffix}"
        self._start_at = None
        self._end_at = None
        self._lunch_break_start_at = None
        self._lunch_break_end_at = None

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        name = "Emploi du temps"
        match self._suffix:
            case "_1":
                name = "Emploi du temps - Semaine en cours"
            case "_2":
                name = "Emploi du temps - Semaine suivante"
            case "_3":
                name = "Emploi du temps - Semaine après suivante"
            case "_today":
                name = "Emploi du temps - Aujourd'hui"
            case "_tomorrow":
                name = "Emploi du temps - Demain"
            case "_next_day":
                name = "Emploi du temps - Jour suivant"
        return name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        single_day = self._suffix in ["today", "tomorrow", "next_day"]
        if self._key in self.coordinator.data:
            lessons = self.coordinator.data[self._key]
            canceled_counter = None
            lunch_break_time = datetime.strptime(
                DEFAULT_LUNCH_BREAK_TIME,
                "%H:%M",
            ).time()

            if lessons is not None:
                self._start_at = None
                self._end_at = None
                self._lunch_break_start_at = None
                self._lunch_break_end_at = None
                self._date = None
                canceled_counter = 0
                for lesson in lessons:
                    index = lessons.index(lesson)

                    if not (
                        lesson["start_time"] == lessons[index - 1]["start_time"]
                        and lesson["is_annule"]
                    ):
                        attributes.append(lesson)
                        self._date = lesson["start"].strftime("%Y-%m-%d")
                    if lesson["is_annule"]:
                        canceled_counter += 1
                    if single_day and lesson["is_annule"] is False:
                        start = lesson["start"].strftime("%H:%M")
                        if self._start_at is None or start < self._start_at:
                            self._start_at = start
                        end = lesson["end"].strftime("%H:%M")
                        if self._end_at is None or end > self._end_at:
                            self._end_at = end
                        if (
                            datetime.strptime(lesson["end_time"], "%H:%M").time()
                            < lunch_break_time
                        ):
                            self._lunch_break_start_at = lesson["end"]
                        if (
                            self._lunch_break_end_at is None
                            and datetime.strptime(lesson["start_time"], "%H:%M").time()
                            >= lunch_break_time
                        ):
                            self._lunch_break_end_at = lesson["start"]
            if is_too_big(attributes):
                LOGGER.warning(
                    "[%s] Les attributs sont trop volumineux! %s",
                    self._attr_name,
                    attributes,
                )
                attributes = []
                attributes.append(
                    {
                        "Erreur": "Les attributs sont trop volumineux. Essayez de désactiver les tags HTML. https://www.hacf.fr/ecole-directe/#retrait-des-tags-html"
                    }
                )

        result = super().extra_state_attributes
        result.update(
            {
                "Emploi du temps": attributes,
                "Cours annulés": canceled_counter,
            }
        )

        if single_day:
            result["Déjeuner début"] = self._lunch_break_start_at
            result["Déjeuner fin"] = self._lunch_break_end_at
            result["Journée début"] = self._start_at
            result["Journée fin"] = self._end_at
            result["Date"] = self._date

        return result
