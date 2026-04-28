from pydantic import BaseModel

from home_assistant_lib import PlayMediaPayload

from clyde.mcp_app import MCP
from clyde.tools.media_player_helpers import resolve_media_player


class MediaPlayerPlayMediaResult(BaseModel):
    ok: bool
    media_player: str
    media_content_id: str
    media_content_type: str
    error: str | None = None


@MCP.tool(description="Play media on a media player. `media_content_type` is an HA-supported type (music, video, playlist, etc.). `enqueue` can be 'add', 'next', 'play', or 'replace'. Set `announce=true` for announcements.")
async def media_player_play_media(
    media_player: str,
    media_content_id: str,
    media_content_type: str,
    enqueue: str | None = None,
    announce: bool | None = None,
) -> MediaPlayerPlayMediaResult:
    player, error = resolve_media_player(media_player)
    if error:
        return MediaPlayerPlayMediaResult(ok=False, media_player=media_player, media_content_id=media_content_id, media_content_type=media_content_type, error=str(error))

    payload = PlayMediaPayload(media_content_id=media_content_id, media_content_type=media_content_type, enqueue=enqueue, announce=announce)
    _, error = await player.play_media(payload)
    if error:
        return MediaPlayerPlayMediaResult(ok=False, media_player=media_player, media_content_id=media_content_id, media_content_type=media_content_type, error=str(error))

    return MediaPlayerPlayMediaResult(ok=True, media_player=media_player, media_content_id=media_content_id, media_content_type=media_content_type)
