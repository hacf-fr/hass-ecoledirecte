"""Helpers for ecole_directe."""

from unidecode import unidecode


def get_unique_id(data: str) -> str:
    """Get unique id."""
    return unidecode(data).lower().replace(" ", "_")
