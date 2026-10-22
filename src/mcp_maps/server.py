"""The `maps` MCP server instance and its tool guide."""

from jarvis_mcp_kit import ToolServer

INSTRUCTIONS = (
    "Routes and navigation. Call get_maps_memory first to learn the user's saved places "
    "(aliases such as 'Home' or 'work'), the transit stops they prefer and any travel notes; "
    "then call get_route_details with aliases or with stops/landmarks. Assume Warsaw, Poland "
    "unless told otherwise, and public transit unless the user names another mode. Never ask "
    "for or reveal street addresses of saved places — aliases are resolved on the server. "
    "Apply travel notes (e.g. walking speed) when you summarize durations."
)

server = ToolServer("maps", title="Jarvis Maps", instructions=INSTRUCTIONS)
