from pydantic import BaseModel

from home_assistant_lib import MediaPlayerState

from clyde.mcp_app import MCP
from clyde.tools.media_player_helpers import resolve_media_player


class MediaPlayerStateResult(BaseModel):
    ok: bool
    media_player: str
    state: MediaPlayerState | None = None
    error: str | None = None


@MCP.tool(description="Get the current state of a media player: power state, volume, muted, source, source list, and current media metadata.")
async def media_player_state(media_player: str) -> MediaPlayerStateResult:
    player, error = resolve_media_player(media_player)
    if error:
        return MediaPlayerStateResult(ok=False, media_player=media_player, error=str(error))
    state, error = await player.get_state()
    if error:
        return MediaPlayerStateResult(ok=False, media_player=media_player, error=str(error))
    return MediaPlayerStateResult(ok=True, media_player=media_player, state=state)
