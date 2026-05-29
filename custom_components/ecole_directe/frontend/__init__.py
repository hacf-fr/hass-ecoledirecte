"""Enregistrement des modules JavaScript."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.http import StaticPathConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from ..const import JSMODULES, URL_BASE

_LOGGER = logging.getLogger(__name__)


class JSModuleRegistration:
    """Enregistre les modules JavaScript dans Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize tle registraire."""
        self.hass = hass
        self.lovelace = self.hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Enregistrer les ressources frontend."""
        await self._async_register_path()
        # Enregistrer les modules uniquement si Lovelace est en mode stockage
        if (
            getattr(
                self.lovelace, "mode", getattr(self.lovelace, "resource_mode", "yaml")
            )
            == "storage"
        ):
            await self._async_register_lovelace_modules()

    async def _async_register_path(self) -> None:
        """Enregistrer le chemin HTTP statique."""
        try:
            await self.hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        url_path=URL_BASE,
                        path=Path(__file__).parent,
                        cache_headers=False,
                    )
                ]
            )
            _LOGGER.debug(
                "Chemin enregistré : %s -> %s", URL_BASE, Path(__file__).parent
            )
        except RuntimeError:
            _LOGGER.debug("Chemin déjà enregistré : %s", URL_BASE)

    async def _async_register_lovelace_modules(self) -> None:
        """Charger les ressources Lovelace puis enregistrer les modules."""
        if not getattr(self.lovelace.resources, "loaded", True):
            try:
                await self.lovelace.resources.async_get_info()
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.debug("Impossible de charger les ressources Lovelace: %s", err)
                return

        await self._async_register_modules()

    async def _async_register_modules(self) -> None:
        """Enregistrer ou mettre à jour les modules JavaScript."""
        _LOGGER.debug("Installation des modules JavaScript")

        # Récupérer les ressources existantes de cette intégration
        existing_resources = [
            r
            for r in self.lovelace.resources.async_items()
            if r["url"].startswith(URL_BASE)
        ]

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            registered = False

            for resource in existing_resources:
                if self._get_path(resource["url"]) == url:
                    registered = True
                    # Vérifier si une mise à jour est nécessaire
                    if self._get_version(resource["url"]) != module["version"]:
                        _LOGGER.info(
                            "Mise à jour de %s vers la version %s",
                            module["name"],
                            module["version"],
                        )
                        await self.lovelace.resources.async_update_item(
                            resource["id"],
                            {
                                "res_type": "module",
                                "url": f"{url}?v={module['version']}",
                            },
                        )
                    break

            if not registered:
                _LOGGER.info(
                    "Enregistrement de %s version %s", module["name"], module["version"]
                )
                await self.lovelace.resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": f"{url}?v={module['version']}",
                    }
                )

    def _get_path(self, url: str) -> str:
        """Extraire le chemin sans les paramètres."""
        return url.split("?", maxsplit=1)[0]

    def _get_version(self, url: str) -> str:
        """Extraire la version de l'URL."""
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1].replace("v=", "")
        return "0"

    async def async_unregister(self) -> None:
        """Supprimer les ressources Lovelace de cette intégration."""
        if self.lovelace.mode == "storage":
            for module in JSMODULES:
                url = f"{URL_BASE}/{module['filename']}"
                resources = [
                    r
                    for r in self.lovelace.resources.async_items()
                    if r["url"].startswith(url)
                ]
                for resource in resources:
                    await self.lovelace.resources.async_delete_item(resource["id"])
