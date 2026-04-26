from pydantic import BaseModel


class SpotifyArtistRef(BaseModel):
    name: str
    uri: str
    id: str


class SpotifyTrack(BaseModel):
    name: str
    artists: list[str]
    album: str
    uri: str
    id: str
    duration_ms: int


class SpotifyPlaylistRef(BaseModel):
    name: str
    owner: str
    description: str | None
    uri: str
    id: str
    track_count: int


class SpotifyAlbum(BaseModel):
    name: str
    artists: list[str]
    uri: str
    id: str
    release_date: str | None


class SpotifySearchResults(BaseModel):
    tracks: list[SpotifyTrack] = []
    playlists: list[SpotifyPlaylistRef] = []
    albums: list[SpotifyAlbum] = []
    artists: list[SpotifyArtistRef] = []
