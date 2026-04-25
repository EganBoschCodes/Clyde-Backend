from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.tools.media_player_helpers import resolve_media_player


class MediaPlayerSelectSourceResult(BaseModel):
    ok: bool
    media_player: str
    source: str
    error: str | None = None


@MCP.tool(description="Select an input source on a media player (e.g. an app name on a Fire TV).")
async def media_player_select_source(media_player: str, source: str) -> MediaPlayerSelectSourceResult:
    player, error = resolve_media_player(media_player)
    if error:
        return MediaPlayerSelectSourceResult(ok=False, media_player=media_player, source=source, error=str(error))
    _, error = player.select_source(source)
    if error:
        return MediaPlayerSelectSourceResult(ok=False, media_player=media_player, source=source, error=str(error))
    return MediaPlayerSelectSourceResult(ok=True, media_player=media_player, source=source)
