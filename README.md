# mcp-maps

Routes and navigation (Google Directions) with saved places, as an
[MCP](https://modelcontextprotocol.io) server.

| Tool | |
|---|---|
| `get_maps_memory` | the caller's saved places by **alias** (Home, work…), preferred stops, travel notes |
| `get_route_details` | a route between aliases / stops / landmarks; transit by default |
| `whoami` | which client and principal your key acts as |

**Addresses never leave the server.** Tools see aliases; `get_route_details` resolves them and
relabels the route endpoints back to the alias.

**Places are per principal** — a household group id forwarded by a trusted client such as
Jarvis (`X-On-Behalf-Of: dom`), or a client's own id. A caller with no scope gets no places.
See `config/places.example.yaml`; convert Jarvis's old file with
`mcp-maps import-legacy maps_memory.json --principals dom`.

Part of the Jarvis tool servers; built on
[jarvis-mcp-kit](https://github.com/jaknow01/jarvis-mcp-kit) (API keys, rate limits, logs).

## Run

```bash
cp .env.example .env                              # GOOGLE_MAPS_API_KEY
cp config/clients.example.yaml config/clients.yaml
cp config/places.example.yaml config/places.yaml  # your places (gitignored)
uv run --env-file .env mcp-maps serve             # http://localhost:8010/mcp/maps
```

Kubernetes: `deploy/kubernetes.yaml` (clients and places as Secrets). This server holds
personal data — keep it ClusterIP-only.

## Connect

- **Jarvis:** `config/subagents.yaml` entry with `identity: group`.
- **Claude Code:** `claude mcp add --transport http maps https://<host>/mcp/maps --header "Authorization: Bearer jvk_…"`
  (add your client id to a scope's `principals`).
