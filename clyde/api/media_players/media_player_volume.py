from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.media_player_volume import media_player_volume

import clyde.utils as utils


class MediaPlayerVolumeRequest(BaseModel):
    media_player: str
    level: float | None = None
    mute: bool | None = None


class MediaPlayerVolumeResponse(BaseModel):
    media_player: str
    level: float | None
    mute: bool | None


async def handle_media_player_volume(req: MediaPlayerVolumeRequest) -> utils.Result[MediaPlayerVolumeResponse]:
    result = await media_player_volume(media_player=req.media_player, level=req.level, mute=req.mute)
    if not result.ok:
        return utils.err(ValueError(result.error or "media player volume failed"))
    return utils.ok(MediaPlayerVolumeResponse(media_player=req.media_player, level=result.level, mute=result.mute))


@MCP.custom_route("/api/media_players/{media_player}/volume", methods=["PUT"])
async def media_player_volume_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MediaPlayerVolumeRequest, handle_media_player_volume)
