from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.media_player_select_source import media_player_select_source

import clyde.utils as utils


class MediaPlayerSelectSourceRequest(BaseModel):
    media_player: str
    source: str


class MediaPlayerSelectSourceResponse(BaseModel):
    media_player: str
    source: str


async def handle_media_player_select_source(req: MediaPlayerSelectSourceRequest) -> utils.Result[MediaPlayerSelectSourceResponse]:
    result = await media_player_select_source(media_player=req.media_player, source=req.source)
    if not result.ok:
        return utils.err(ValueError(result.error or "media player select_source failed"))
    return utils.ok(MediaPlayerSelectSourceResponse(media_player=req.media_player, source=req.source))


@MCP.custom_route("/api/media_players/{media_player}/source", methods=["PUT"])
async def media_player_select_source_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MediaPlayerSelectSourceRequest, handle_media_player_select_source)
