from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.tools.media_player_helpers import resolve_media_player


class MediaPlayerVolumeResult(BaseModel):
    ok: bool
    media_player: str
    level: float | None = None
    mute: bool | None = None
    error: str | None = None


@MCP.tool(description="Set a media player's volume level (0.0-1.0, clamped) and/or mute state. Provide at least one of `level` or `mute`.")
async def media_player_volume(media_player: str, level: float | None = None, mute: bool | None = None) -> MediaPlayerVolumeResult:
    if level is None and mute is None:
        return MediaPlayerVolumeResult(ok=False, media_player=media_player, error="must provide `level` or `mute`")

    player, error = resolve_media_player(media_player)
    if error:
        return MediaPlayerVolumeResult(ok=False, media_player=media_player, error=str(error))

    if level is not None:
        _, error = player.volume_set(level)
        if error:
            return MediaPlayerVolumeResult(ok=False, media_player=media_player, error=str(error))

    if mute is not None:
        _, error = player.volume_mute(mute)
        if error:
            return MediaPlayerVolumeResult(ok=False, media_player=media_player, error=str(error))

    return MediaPlayerVolumeResult(ok=True, media_player=media_player, level=level, mute=mute)
