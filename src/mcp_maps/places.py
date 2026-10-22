"""Saved places per principal (household group or client), from a scopes file.

``MCP_PLACES_CONFIG`` (default ``config/places.yaml``)::

    scopes:
      - principals: [dom, kuba-claude-code]
        notes: ["The user walks fast: assume walking legs take ~0.8x the estimate."]
        places:
          - aliases: [Home, Dom]
            address: "ul. …, Warszawa"
            preferred_transit_points: [Metro Bemowo]

Addresses never leave the server: tools see aliases, and get_route_details resolves them.
"""

from typing import Optional

from jarvis_mcp_kit import ScopedConfig, current_principal

PLACES = ScopedConfig("MCP_PLACES_CONFIG", "config/places.yaml")


def scope() -> dict:
    return PLACES.for_principal(current_principal()) or {}


def known_entries() -> list[dict]:
    places = scope().get("places") or []
    return [p for p in places if isinstance(p, dict)]


def notes() -> list[str]:
    return [str(n) for n in scope().get("notes") or []]


def resolve_place(name: str) -> tuple[str, Optional[str]]:
    """(real_address, matched_alias) for a known alias of this principal; unknown names pass
    through unchanged with alias None."""
    if not name:
        return name, None
    target = name.strip().lower()
    for entry in known_entries():
        if target in [str(a).lower() for a in entry.get("aliases", [])]:
            return entry.get("address", name), name
    return name, None
