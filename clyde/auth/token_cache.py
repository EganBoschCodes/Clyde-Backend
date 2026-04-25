import time

from pydantic import BaseModel


class CachedIdentity(BaseModel):
    model_config = {"frozen": True}

    email: str
    expires_at: float


class TokenCache:
    def __init__(self) -> None:
        self.entries: dict[str, CachedIdentity] = {}

    def get(self, token: str) -> CachedIdentity | None:
        entry = self.entries.get(token)
        if entry is None:
            return None
        if entry.expires_at <= time.time():
            del self.entries[token]
            return None
        return entry

    def put(self, token: str, email: str, expires_at: float) -> None:
        self.entries[token] = CachedIdentity(email=email, expires_at=expires_at)


CACHE = TokenCache()
