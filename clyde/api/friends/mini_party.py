import asyncio
import time
from dataclasses import dataclass, field

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.events.event_directory import MiniParty
from clyde.mcp_app import MCP
from clyde.managers import ENGINE

import clyde.utils as utils


CLIENT_IP_HEADER = "x-client-ip"
FREE_PRESSES = 3
COOLDOWN_S = 5 * 60.0
ABUSE_WINDOW_S = 60.0
ABUSE_THRESHOLD = 3
LOCKOUT_S = 4 * 60 * 60.0
EXCLUDED_ROOMS = {"bedroom"}


class MiniPartyRequest(BaseModel):
    pass


class MiniPartyResponse(BaseModel):
    rooms: list[str]
    failed: dict[str, str]


@dataclass
class IpState:
    presses: list[float] = field(default_factory=list)
    blocked_until: float = 0.0
    abuse_attempts: list[float] = field(default_factory=list)


state: dict[str, IpState] = {}


def check_and_record(ip: str, now: float) -> float:
    s = state.setdefault(ip, IpState())

    if now < s.blocked_until:
        s.abuse_attempts = [t for t in s.abuse_attempts if now - t < ABUSE_WINDOW_S]
        s.abuse_attempts.append(now)
        if len(s.abuse_attempts) >= ABUSE_THRESHOLD:
            s.blocked_until = now + LOCKOUT_S
            s.abuse_attempts.clear()
        return s.blocked_until - now

    s.abuse_attempts.clear()
    s.presses.append(now)

    if len(s.presses) >= FREE_PRESSES:
        s.blocked_until = now + COOLDOWN_S
        s.presses.clear()

    return 0.0


async def handle_mini_party(req: MiniPartyRequest) -> utils.Result[MiniPartyResponse]:
    del req
    rooms = [r for r in ENGINE.managers.keys() if r not in EXCLUDED_ROOMS]
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
    ip = request.headers.get(CLIENT_IP_HEADER)
    if not ip:
        return JSONResponse({"error": f"missing {CLIENT_IP_HEADER} header"}, status_code=400)

    remaining = check_and_record(ip, time.monotonic())
    if remaining > 0:
        retry_after = int(remaining) + 1
        return JSONResponse(
            {"error": "too many presses", "retry_after": retry_after},
            status_code=429,
            headers={"retry-after": str(retry_after)},
        )

    return await utils.handle_api(request, MiniPartyRequest, handle_mini_party)
