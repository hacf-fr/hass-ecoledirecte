"""
Credential validators.

Validation functions for user credentials and authentication.

When this file grows, consider splitting into:
- credentials.py: Basic credential validation
- oauth.py: OAuth-specific validation
- api_auth.py: API authentication methods
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ecoledirecte_api.client import QCMException

from custom_components.ecole_directe.api.client import (
    EDSession,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def validate_credentials(
    hass: HomeAssistant, username: str, password: str, qcm_path: str
) -> None:
    """
    Validate user credentials by testing API connection.

    Args:
        hass: Home Assistant instance.
        username: The username to validate.
        password: The password to validate.
        qcm_path: Path to the QCM file.

    Raises:
        EDApiClientAuthenticationError: If credentials are invalid.
        EDApiClientCommunicationError: If communication fails.
        EDApiClientError: For other API errors.

    """
    try:
        async with EDSession(
            user=username,
            pwd=password,
            hass=hass,
            qcm_path=qcm_path,
            conn_state=None,
        ) as session:
            await session.login()
    except QCMException:
        return


__all__ = [
    "validate_credentials",
]
