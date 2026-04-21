from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_events import EventInfo, list_events

import clyde.utils as utils


class ListEventsRequest(BaseModel):
    pass


class ListEventsResponse(BaseModel):
    events: list[EventInfo]


async def handle_list_events(req: ListEventsRequest) -> utils.Result[ListEventsResponse]:
    del req
    result = await list_events()
    return utils.ok(ListEventsResponse(events=result.events))


@MCP.custom_route("/api/events", methods=["GET"])
async def list_events_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListEventsRequest, handle_list_events)
