"""`mcp-maps` command line.

    mcp-maps serve                                         run the MCP server (default)
    mcp-maps import-legacy maps_memory.json --principals dom,kuba-claude-code
        print a places.yaml scope built from Jarvis's old maps_memory.json (stdout only)
"""

import argparse
import json
import sys

import yaml
from jarvis_mcp_kit import run, setup_logging

from mcp_maps.server import server


def create_app():
    from mcp_maps import tools  # noqa: F401  (registers the tools on `server`)

    return server.app()


def legacy_to_scope(data: dict, principals: list[str]) -> dict:
    entries = []
    for key in ("known_adressess", "known_addresses", "known_adresses"):
        if isinstance(data.get(key), list):
            entries = data[key]
            break
    places = [{"aliases": e.get("aliases", []), "address": e.get("address", ""),
               "preferred_transit_points": e.get("preffered_transit_points") or e.get("preferred_transit_points") or []}
              for e in entries if isinstance(e, dict)]
    return {"principals": principals, "places": places}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="mcp-maps", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="run the MCP server (default)")
    p_imp = sub.add_parser("import-legacy", help="convert Jarvis maps_memory.json to a places scope")
    p_imp.add_argument("path")
    p_imp.add_argument("--principals", required=True, help="comma list of principal ids")
    args = parser.parse_args(argv)
    if args.cmd == "import-legacy":
        with open(args.path, encoding="utf-8") as f:
            scope = legacy_to_scope(json.load(f), [p.strip() for p in args.principals.split(",") if p.strip()])
        yaml.safe_dump({"scopes": [scope]}, sys.stdout, allow_unicode=True, sort_keys=False)
        return
    setup_logging()
    run(create_app())


if __name__ == "__main__":
    main()
