"""Workspace sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from custom_components.ecole_directe.entity.base import EDEntity
from custom_components.ecole_directe.sensor.generic import is_too_big

if TYPE_CHECKING:
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator


class EDWorkspaceSensor(SensorEntity, EDEntity):  # type: ignore[reportIncompatibleVariableOverride]
    """Represent a workspace and its activities and post-its."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        workspace: dict[str, Any],
        workspace_id: str,
    ) -> None:
        """Initialize the workspace sensor."""
        titre = workspace.get("titre")
        workspace_name = str(titre) if titre else f"Espace {workspace_id}"
        description = SensorEntityDescription(
            key=f"espace_{workspace_id}",
            name=workspace_name,
            icon="mdi:folder-multiple",
            has_entity_name=True,
        )
        super().__init__(coordinator, description)
        self._workspace_id = workspace_id

    @property
    def native_value(self) -> int:  # type: ignore[reportIncompatibleVariableOverride]
        """Return the number of activities in the workspace."""
        if not self.coordinator.data:
            return 0
        return len(
            self.coordinator.data.get("wk_activities", {}).get(self._workspace_id, [])
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:  # type: ignore[reportIncompatibleVariableOverride]
        """Return workspace details, activities, and post-its."""
        if not self.coordinator.data:
            return {}
        workspace = next(
            (
                item
                for item in self.coordinator.data.get("workspaces", [])
                if _get_workspace_id(item) == self._workspace_id
            ),
            {},
        )
        attributes = {
            "Espace de travail": workspace,
            "Activités": self.coordinator.data.get("wk_activities", {}).get(
                self._workspace_id, []
            ),
            "Post-it": self.coordinator.data.get("wk_postits", {}).get(
                self._workspace_id, []
            ),
        }
        if is_too_big(attributes):
            store_key = self._attr_unique_id or f"espace_{self._workspace_id}"
            self.coordinator.async_save_attributes(store_key, attributes)
            return {
                "stored_in_store": True,
                "store_key": store_key,
            }
        return attributes

    @property
    def available(self) -> bool:  # type: ignore[reportIncompatibleVariableOverride]
        """Return whether the workspace is still available."""
        if not self.coordinator.last_update_success or not self.coordinator.data:
            return False
        return any(
            _get_workspace_id(workspace) == self._workspace_id
            for workspace in self.coordinator.data.get("workspaces", [])
        )


def _get_workspace_id(workspace: dict[str, Any]) -> str | None:
    """Return a workspace identifier from an API object."""
    for key in ("id", "idEspace", "espaceId", "workspaceId"):
        value = workspace.get(key)
        if value is not None:
            return str(value)
    return None
