"""Maps tools: the caller's saved-place aliases and route planning (Google Directions).

The model works with place ALIASES only (Home, work, …); the real address behind an alias is
resolved here and the route endpoints are relabelled back to the alias, so street addresses
are not handed out as a browsable address book. Saved places are per principal (places.py).
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Literal, Optional, Union

import googlemaps

from mcp_maps import places
from mcp_maps.directions import normalize_departure_time, simplify_directions_response
from mcp_maps.server import server

logger = logging.getLogger(__name__)


@server.tool()
async def get_maps_memory() -> dict:
    """
    Description:
    This tool lists the user's known/favourite places by their ALIAS (e.g. 'Home',
    'work', 'University'), together with preferred transit stops near them and any travel
    notes saved for the user. Use these aliases as origin/destination in get_route_details
    — the real street address behind an alias is resolved automatically and is not
    needed (and not shown) here.
    """
    entries = places.known_entries()
    result = {
        "known_places": [
            {"aliases": e.get("aliases", []),
             "preferred_transit_points": e.get("preferred_transit_points") or e.get("preffered_transit_points") or []}
            for e in entries
        ],
        "known_place_aliases": [a for e in entries for a in e.get("aliases", [])],
        "note": "Refer to these places by alias; their actual addresses are resolved automatically.",
    }
    if notes := places.notes():
        result["travel_notes"] = notes
    return result


@server.tool()
async def get_route_details(origin: str,
                            destination: str,
                            transport_mode: Literal["driving", "walking", "bicycling", "transit"] = "transit",
                            transit_mode: Optional[Literal["bus", "subway", "tram", None]] = None,
                            departure_time: Optional[Union[str, datetime]] = "now",
                            show_alternatives: Optional[bool] = True
                            ) -> dict | list:
    """
    Description:
    This tool is used to calculate the route between origin and destination based on the user's preferred
    mode of transport (such as car, transit, etc.) and return the most optimal route to the user.
    Unless specified otherwise one should always assume that both origin and destination are in Warsaw, Poland.

    Parameters:
    origin: str
        The starting point of the journey. This can be an alias of a known place
        (from get_maps_memory, e.g. 'Home'), a specific bus/metro/train stop, or a
        landmark. Known aliases are resolved to their real address automatically.

    destination: str
        The end of the journey. This can be an alias of a known place (from
        get_maps_memory, e.g. 'work'), a specific bus/metro/train stop, or a landmark.
        Known aliases are resolved to their real address automatically.

    transport_mode: Literal["driving", "walking", "bicycling", "transit"] = 'transit'
        User's preffered mode of communication such as 'car', 'transit' etc.
        Note: should remain with defalut value 'transit' unless user specifies otherwise

    transit_mode: Optional[Literal["bus", "subway", "tram", None]] = None
        Limits the public transit options to only one specified mode. When left with default value of None
        the route may consist of any combination of public transport modes such as buses, trams, subways etc.
        If a given mode is specified the route will be limited to only one mode of public transport.
        Note: this parameter can only be provided if transport_mode = 'transit'. Otherwise it should remain None

    departure_time: Optional[Union[str, datetime]] = "now"
        Time at which user wishes to leave. By default is set to 'now'.

    show_alternatives: Optional[bool] = True
        This parameter controls whether the navigation API returns only one most optimal route
        or multiple options.
        When True only one route is returned, otherwise multiple options
        Note: it sholud remain True unless user specifies otherwise

    Output:
        This function returns a json file with all of the steps of the most optimal route from origin to destination
        along with all transfers if necessary. Should an error occurr this function will return a json with the
        proper error message.

    Note:
        Apply any travel_notes returned by get_maps_memory (e.g. the user's walking speed).
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"Message": "Routing is not configured on this server (no Google Maps key)."}
    gmaps_client = googlemaps.Client(api_key, timeout=20, retry_timeout=20)

    if transport_mode != "transit" and transit_mode is not None:
        transit_mode = None

    origin_address, origin_alias = places.resolve_place(origin)
    destination_address, destination_alias = places.resolve_place(destination)
    departure_time = normalize_departure_time(departure_time)

    try:
        directions_result = await asyncio.to_thread(
            gmaps_client.directions,
            origin=origin_address,
            destination=destination_address,
            mode=transport_mode,
            transit_mode=transit_mode,
            departure_time=departure_time,
            alternatives=show_alternatives,
        )
        result = await simplify_directions_response(directions_result)
    except Exception as e:  # type only: client errors may echo the request (addresses, key)
        logger.warning("Google Directions failed (%s)", type(e).__name__)
        return {"Message": "Error while getting routes from Google", "Error": type(e).__name__}

    for leg in result:
        if origin_alias:
            leg["start_address"] = origin_alias
        if destination_alias:
            leg["end_address"] = destination_alias
    return result
