import asyncio

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.events.event_directory import MiniParty
from clyde.mcp_app import MCP
from clyde.routines import ENGINE

import clyde.utils as utils


class MiniPartyRequest(BaseModel):
    pass


class MiniPartyResponse(BaseModel):
    rooms: list[str]
    failed: dict[str, str]


async def handle_mini_party(req: MiniPartyRequest) -> utils.Result[MiniPartyResponse]:
    del req
    rooms = list(ENGINE.managers.keys())
    results = await asyncio.gather(*(ENGINE.fire_event(room, MiniParty()) for room in rooms))
    fired: list[str] = []
    failed: dict[str, str] = {}
    for room, (_, error) in zip(rooms, results):
        if error:
            failed[room] = str(error)
        else:
            fired.append(room)
    return utils.ok(MiniPartyResponse(rooms=fired, failed=failed))


@MCP.custom_route("/api/friends/mini-party", methods=["POST"])
async def mini_party_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, MiniPartyRequest, handle_mini_party)
