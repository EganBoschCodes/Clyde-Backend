from typing import Literal

from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.spotify import SPOTIFY, SpotifySearchResults


type SpotifySearchType = Literal["track", "playlist", "album", "artist"]

DEFAULT_TYPES: tuple[SpotifySearchType, ...] = ("track", "playlist")
DEFAULT_LIMIT = 10
MIN_LIMIT = 1
MAX_LIMIT = 50


class SpotifySearchResult(BaseModel):
    ok: bool
    query: str
    types: list[SpotifySearchType]
    results: SpotifySearchResults | None = None
    error: str | None = None


@MCP.tool(description="Search Spotify for tracks, playlists, albums, or artists. Returns Spotify URIs (e.g. spotify:track:...) that can be passed to media_player_play_media as media_content_id with media_content_type='music'. `types` defaults to track+playlist; `limit` is per type, 1-50.")
async def spotify_search(
    query: str,
    types: list[SpotifySearchType] | None = None,
    limit: int = DEFAULT_LIMIT,
) -> SpotifySearchResult:
    requested_types = tuple(types) if types else DEFAULT_TYPES
    bounded_limit = max(MIN_LIMIT, min(limit, MAX_LIMIT))
    types_out = list(requested_types)

    if not SPOTIFY.configured:
        return SpotifySearchResult(ok=False, query=query, types=types_out, error="Spotify is not configured (set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env)")

    if not query.strip():
        return SpotifySearchResult(ok=False, query=query, types=types_out, error="Query must not be empty")

    results, error = await SPOTIFY.search(query, requested_types, bounded_limit)
    if error:
        return SpotifySearchResult(ok=False, query=query, types=types_out, error=str(error))

    return SpotifySearchResult(ok=True, query=query, types=types_out, results=results)
