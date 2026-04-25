from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from home_assistant_lib import MediaPlayerState

from clyde.mcp_app import MCP
from clyde.tools.media_player_state import media_player_state

import clyde.utils as utils


class MediaPlayerStateRequest(BaseModel):
    media_player: str


class MediaPlayerStateResponse(BaseModel):
    media_player: str
    state: MediaPlayerState


async def handle_media_player_state(req: MediaPlayerStateRequest) -> utils.Result[MediaPlayerStateResponse]:
    result = await media_player_state(media_player=req.media_player)
    if not result.ok or result.state is None:
        return utils.err(ValueError(result.error or "media player state lookup failed"))
    return utils.ok(MediaPlayerStateResponse(media_player=req.media_player, state=result.state))


@MCP.custom_route("/api/media_players/{media_player}/state", methods=["GET"])
async def media_player_state_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MediaPlayerStateRequest, handle_media_player_state)
