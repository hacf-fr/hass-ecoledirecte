"""Wallet sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
)

from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wallet",
        translation_key="wallet",
        icon="mdi:wallet",
        has_entity_name=True,
    ),
)


class EDWalletSensor(EDGenericSensor):
    """Representation of an ED wallet sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        libelle: str = "wallet",
        eleve: EDEleve | None = None,
        solde: int = 0,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            "wallets" if eleve is None else f"{eleve.get_fullname_lower()}_wallets",
            libelle,
            eleve,
            solde,
        )
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:wallet"
        self.unique_id = self._attr_name

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._key not in self.coordinator.data:
            return "unavailable"
        wallet = next(
            item
            for item in self.coordinator.data[self._key]
            if item.get("libelle") == self._attr_name
        )
        if wallet is None:
            return "unavailable"
        return wallet["solde"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._key in self.coordinator.data
        )
