from pydantic import BaseModel

from clyde.mcp_app import MCP

import clyde.utils as utils


class MediaPlayerInfo(BaseModel):
    name: str
    entity_id: str


class ListMediaPlayersResult(BaseModel):
    media_players: list[MediaPlayerInfo]


@MCP.tool(description="List all configured media players with their entity_id.")
async def list_media_players() -> ListMediaPlayersResult:
    out: list[MediaPlayerInfo] = []
    for key, player in utils.CONFIG.media_players.items():
        out.append(MediaPlayerInfo(name=key, entity_id=player.entity_id))
    return ListMediaPlayersResult(media_players=out)
