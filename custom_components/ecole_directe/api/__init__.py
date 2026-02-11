"""API package for ecole_directe."""

from .client import (
    EDEleve,
    EDSession,
    check_ecoledirecte_session,
    get_unique_id,
)

__all__ = [
    "EDEleve",
    "EDSession",
    "check_ecoledirecte_session",
    "get_unique_id",
]
