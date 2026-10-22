"""Places are per principal, exposed as aliases only, resolved on the server."""

import asyncio
from types import SimpleNamespace

import pytest
import yaml
from jarvis_mcp_kit import Client, acting_as

from conftest import call_tools, text_of
from mcp_maps import places, tools
from mcp_maps.cli import legacy_to_scope

SCOPES = {"scopes": [
    {"principals": ["dom", "jarvis"], "notes": ["walks fast"],
     "places": [{"aliases": ["Home"], "address": "Sekretna 1", "preferred_transit_points": ["Stop A"]},
                {"aliases": ["work", "office"], "address": "Tajna 7"}]},
    {"principals": ["ala-flat"], "places": [{"aliases": ["Home"], "address": "Inna 3"}]},
]}


@pytest.fixture(autouse=True)
def places_file(tmp_path, monkeypatch):
    path = tmp_path / "places.yaml"
    path.write_text(yaml.safe_dump(SCOPES))
    monkeypatch.setenv("MCP_PLACES_CONFIG", str(path))
    places.PLACES._mtime = None


def _as(principal):
    return acting_as(Client("c", "C", "0" * 64, frozenset({"maps"})), principal)


def test_aliases_only_no_addresses():
    with _as("dom"):
        out = asyncio.run(tools.get_maps_memory())
    assert set(out["known_place_aliases"]) == {"Home", "work", "office"}
    assert "Sekretna" not in str(out) and "Tajna" not in str(out)
    assert out["travel_notes"] == ["walks fast"]


def test_resolution_is_per_principal_and_case_insensitive():
    with _as("dom"):
        assert places.resolve_place("Home") == ("Sekretna 1", "Home")
        assert places.resolve_place("OFFICE") == ("Tajna 7", "OFFICE")
        assert places.resolve_place("Metro Bemowo") == ("Metro Bemowo", None)
        assert places.resolve_place("") == ("", None)
    with _as("ala-flat"):
        assert places.resolve_place("Home") == ("Inna 3", "Home")


def test_unknown_principal_has_no_places():
    with _as("stranger"):
        assert asyncio.run(tools.get_maps_memory())["known_place_aliases"] == []
        assert places.resolve_place("Home") == ("Home", None)


def test_route_resolves_alias_and_relabels(monkeypatch):
    seen = {}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def directions(self, **kwargs):
            seen.update(kwargs)
            return [{"legs": []}]

    async def fake_simplify(_):
        return [{"start_address": "Sekretna 1, Warszawa", "end_address": "Tajna 7, Warszawa", "steps": []}]

    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test")
    monkeypatch.setattr(tools, "googlemaps", SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(tools, "simplify_directions_response", fake_simplify)
    with _as("dom"):
        out = asyncio.run(tools.get_route_details("Home", "work"))
    assert seen["origin"] == "Sekretna 1" and seen["destination"] == "Tajna 7"
    assert out[0]["start_address"] == "Home" and out[0]["end_address"] == "work"


def test_trusted_key_household_over_mcp(app, keys):
    (dom,) = call_tools(app, keys["jarvis"], [("get_maps_memory", {})], on_behalf_of="dom")
    from mcp_maps.cli import create_app

    (friend,) = call_tools(create_app(), keys["friend"], [("get_maps_memory", {})], on_behalf_of="dom")
    assert "office" in text_of(dom)
    assert "office" not in text_of(friend)  # untrusted key acts as itself → no places


def test_legacy_import():
    scope = legacy_to_scope({"known_adressess": [{"aliases": ["Home"], "address": "X", "preffered_transit_points": ["S"]}]},
                            ["dom"])
    assert scope == {"principals": ["dom"], "places": [{"aliases": ["Home"], "address": "X",
                                                        "preferred_transit_points": ["S"]}]}
