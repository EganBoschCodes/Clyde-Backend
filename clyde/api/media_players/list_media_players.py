from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_media_players import MediaPlayerInfo, list_media_players

import clyde.utils as utils


class ListMediaPlayersRequest(BaseModel):
    pass


class ListMediaPlayersResponse(BaseModel):
    media_players: list[MediaPlayerInfo]


async def handle_list_media_players(req: ListMediaPlayersRequest) -> utils.Result[ListMediaPlayersResponse]:
    result = await list_media_players()
    return utils.ok(ListMediaPlayersResponse(media_players=result.media_players))


@MCP.custom_route("/api/media_players", methods=["GET"])
async def list_media_players_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListMediaPlayersRequest, handle_list_media_players)
