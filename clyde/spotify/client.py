import asyncio
import time

import httpx

import clyde.utils as utils

from .config import SPOTIFY_CONFIG, SpotifyConfig
from .parse import parse_search_results
from .types import SpotifySearchResults


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
TOKEN_REFRESH_LEEWAY_SEC = 60.0
HTTP_TIMEOUT_SEC = 10


class SpotifyClient:
    def __init__(self, config: SpotifyConfig | None) -> None:
        self._config = config
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return self._config is not None

    async def _refresh_token(self) -> utils.Result[str]:
        if self._config is None:
            return utils.err(RuntimeError("Spotify is not configured"))

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEC) as client:
                response = await client.post(
                    SPOTIFY_TOKEN_URL,
                    data={"grant_type": "client_credentials"},
                    auth=(self._config.client_id, self._config.client_secret),
                )
        except Exception as e:
            return utils.err(e, "Spotify token request failed")

        if response.status_code != 200:
            return utils.err(RuntimeError(f"Spotify token request returned {response.status_code}: {response.text}"))

        body = response.json()
        token = body.get("access_token") if isinstance(body, dict) else None
        expires_in = body.get("expires_in", 3600) if isinstance(body, dict) else 3600
        if not isinstance(token, str):
            return utils.err(RuntimeError("Spotify token response missing access_token"))

        self._token = token
        self._token_expires_at = time.monotonic() + float(expires_in) - TOKEN_REFRESH_LEEWAY_SEC
        return utils.ok(token)

    async def _get_token(self) -> utils.Result[str]:
        async with self._lock:
            if self._token is not None and time.monotonic() < self._token_expires_at:
                return utils.ok(self._token)
            return await self._refresh_token()

    async def search(self, query: str, types: tuple[str, ...], limit: int) -> utils.Result[SpotifySearchResults]:
        if self._config is None:
            return utils.err(RuntimeError("Spotify is not configured (missing SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET)"))

        token, error = await self._get_token()
        if error:
            return utils.err(error, "Could not obtain Spotify access token")

        params = {"q": query, "type": ",".join(types), "limit": str(limit)}

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEC) as client:
                response = await client.get(
                    f"{SPOTIFY_API_BASE}/search",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except Exception as e:
            return utils.err(e, f"Spotify search request failed (q={query!r})")

        if response.status_code != 200:
            return utils.err(RuntimeError(f"Spotify search returned {response.status_code}: {response.text}"))

        return utils.ok(parse_search_results(response.json()))


SPOTIFY = SpotifyClient(SPOTIFY_CONFIG)
