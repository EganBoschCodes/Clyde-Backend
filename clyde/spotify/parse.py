from .types import SpotifyAlbum, SpotifyArtistRef, SpotifyPlaylistRef, SpotifySearchResults, SpotifyTrack


def parse_search_results(body: object) -> SpotifySearchResults:
    if not isinstance(body, dict):
        return SpotifySearchResults()

    return SpotifySearchResults(
        tracks=parse_tracks(body.get("tracks")),
        playlists=parse_playlists(body.get("playlists")),
        albums=parse_albums(body.get("albums")),
        artists=parse_artists(body.get("artists")),
    )


def extract_items(section: object) -> list[object]:
    if not isinstance(section, dict):
        return []
    items = section.get("items", [])
    if not isinstance(items, list):
        return []
    return items


def artist_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(a.get("name", "")) for a in value if isinstance(a, dict)]


def parse_tracks(section: object) -> list[SpotifyTrack]:
    out: list[SpotifyTrack] = []
    for item in extract_items(section):
        if not isinstance(item, dict):
            continue
        album = item.get("album", {})
        out.append(SpotifyTrack(
            name=str(item.get("name", "")),
            artists=artist_names(item.get("artists")),
            album=str(album.get("name", "")) if isinstance(album, dict) else "",
            uri=str(item.get("uri", "")),
            id=str(item.get("id", "")),
            duration_ms=int(item.get("duration_ms", 0)),
        ))
    return out


def parse_playlists(section: object) -> list[SpotifyPlaylistRef]:
    out: list[SpotifyPlaylistRef] = []
    for item in extract_items(section):
        if not isinstance(item, dict):
            continue
        owner = item.get("owner", {})
        tracks_meta = item.get("tracks", {})
        description = item.get("description")
        out.append(SpotifyPlaylistRef(
            name=str(item.get("name", "")),
            owner=str(owner.get("display_name", "")) if isinstance(owner, dict) else "",
            description=str(description) if isinstance(description, str) and description else None,
            uri=str(item.get("uri", "")),
            id=str(item.get("id", "")),
            track_count=int(tracks_meta.get("total", 0)) if isinstance(tracks_meta, dict) else 0,
        ))
    return out


def parse_albums(section: object) -> list[SpotifyAlbum]:
    out: list[SpotifyAlbum] = []
    for item in extract_items(section):
        if not isinstance(item, dict):
            continue
        release_date = item.get("release_date")
        out.append(SpotifyAlbum(
            name=str(item.get("name", "")),
            artists=artist_names(item.get("artists")),
            uri=str(item.get("uri", "")),
            id=str(item.get("id", "")),
            release_date=str(release_date) if isinstance(release_date, str) else None,
        ))
    return out


def parse_artists(section: object) -> list[SpotifyArtistRef]:
    out: list[SpotifyArtistRef] = []
    for item in extract_items(section):
        if not isinstance(item, dict):
            continue
        out.append(SpotifyArtistRef(
            name=str(item.get("name", "")),
            uri=str(item.get("uri", "")),
            id=str(item.get("id", "")),
        ))
    return out
