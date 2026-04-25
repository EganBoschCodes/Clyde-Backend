from typing import Literal, assert_never

from pydantic import BaseModel

from home_assistant_lib import MediaPlayer

from clyde.mcp_app import MCP
from clyde.tools.media_player_helpers import resolve_media_player

import clyde.utils as utils


type TransportAction = Literal["on", "off", "play", "pause", "stop", "next", "previous"]


class MediaPlayerTransportResult(BaseModel):
    ok: bool
    media_player: str
    action: TransportAction
    error: str | None = None


def dispatch(player: MediaPlayer, action: TransportAction) -> utils.Result[None]:
    match action:
        case "on": return player.on()
        case "off": return player.off()
        case "play": return player.play()
        case "pause": return player.pause()
        case "stop": return player.stop()
        case "next": return player.next_track()
        case "previous": return player.previous_track()
        case _ as x: assert_never(x)


@MCP.tool(description="Send a transport command to a media player: on, off, play, pause, stop, next, previous.")
async def media_player_transport(media_player: str, action: TransportAction) -> MediaPlayerTransportResult:
    player, error = resolve_media_player(media_player)
    if error:
        return MediaPlayerTransportResult(ok=False, media_player=media_player, action=action, error=str(error))
    _, error = dispatch(player, action)
    if error:
        return MediaPlayerTransportResult(ok=False, media_player=media_player, action=action, error=str(error))
    return MediaPlayerTransportResult(ok=True, media_player=media_player, action=action)
