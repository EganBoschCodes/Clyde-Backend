from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.applications import Starlette

from clyde.managers import ENGINE
from clyde.mcp_app import MCP
from clyde.scheduler import SCHEDULER
import clyde.api  # noqa: F401 — registers HTTP routes
import clyde.tools  # noqa: F401 — registers MCP tools


MCP_PATH = "/mcp"

app = MCP.http_app(path=MCP_PATH)

_inner_lifespan = app.router.lifespan_context


@asynccontextmanager
async def lifespan(scope: Starlette) -> AsyncIterator[None]:
    _, error = await SCHEDULER.start()
    if error:
        print(f"[scheduler] failed to start: {error}")
    try:
        async with _inner_lifespan(scope):
            yield
    finally:
        await SCHEDULER.stop()
        await ENGINE.shutdown()


app.router.lifespan_context = lifespan
