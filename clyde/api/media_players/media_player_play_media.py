from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.media_player_play_media import media_player_play_media

import clyde.utils as utils


class MediaPlayerPlayMediaRequest(BaseModel):
    media_player: str
    media_content_id: str
    media_content_type: str
    enqueue: str | None = None
    announce: bool | None = None


class MediaPlayerPlayMediaResponse(BaseModel):
    media_player: str
    media_content_id: str
    media_content_type: str


async def handle_media_player_play_media(req: MediaPlayerPlayMediaRequest) -> utils.Result[MediaPlayerPlayMediaResponse]:
    result = await media_player_play_media(
        media_player=req.media_player,
        media_content_id=req.media_content_id,
        media_content_type=req.media_content_type,
        enqueue=req.enqueue,
        announce=req.announce,
    )
    if not result.ok:
        return utils.err(ValueError(result.error or "media player play_media failed"))
    return utils.ok(MediaPlayerPlayMediaResponse(media_player=req.media_player, media_content_id=req.media_content_id, media_content_type=req.media_content_type))


@MCP.custom_route("/api/media_players/{media_player}/play_media", methods=["POST"])
async def media_player_play_media_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MediaPlayerPlayMediaRequest, handle_media_player_play_media)
