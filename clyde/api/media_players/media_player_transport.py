from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.media_player_transport import TransportAction, media_player_transport

import clyde.utils as utils


class MediaPlayerTransportRequest(BaseModel):
    media_player: str
    action: TransportAction


class MediaPlayerTransportResponse(BaseModel):
    media_player: str
    action: TransportAction


async def handle_media_player_transport(req: MediaPlayerTransportRequest) -> utils.Result[MediaPlayerTransportResponse]:
    result = await media_player_transport(media_player=req.media_player, action=req.action)
    if not result.ok:
        return utils.err(ValueError(result.error or "media player transport failed"))
    return utils.ok(MediaPlayerTransportResponse(media_player=req.media_player, action=req.action))


@MCP.custom_route("/api/media_players/{media_player}/transport", methods=["POST"])
async def media_player_transport_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MediaPlayerTransportRequest, handle_media_player_transport)
