"""API package for ecole_directe."""

from .client import (
    EDApiClient,
    EDApiClientAuthenticationError,
    EDApiClientCommunicationError,
    EDApiClientError,
    EDEleve,
    check_ecoledirecte_session,
)

__all__ = [
    "EDApiClient",
    "EDApiClientAuthenticationError",
    "EDApiClientCommunicationError",
    "EDApiClientError",
    "EDEleve",
    "check_ecoledirecte_session",
]
