from clyde.mcp_app import MCP
import clyde.api  # noqa: F401 — registers HTTP routes
import clyde.tools  # noqa: F401 — registers MCP tools


MCP_PATH = "/mcp"

app = MCP.http_app(path=MCP_PATH)
