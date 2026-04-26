import os

from home_assistant_lib.utils import load_env
from pydantic import BaseModel


class SpotifyConfig(BaseModel):
    model_config = {"frozen": True}

    client_id: str
    client_secret: str


def load_spotify_config() -> SpotifyConfig | None:
    load_env()
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    return SpotifyConfig(client_id=client_id, client_secret=client_secret)


SPOTIFY_CONFIG = load_spotify_config()
