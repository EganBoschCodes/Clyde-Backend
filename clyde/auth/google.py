import httpx
from pydantic import BaseModel

import clyde.utils as utils


GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUER = "https://accounts.google.com"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"


class TokenInfo(BaseModel):
    aud: str
    email: str
    email_verified: str = "false"
    exp: str


async def fetch_token_info(access_token: str) -> utils.Result[TokenInfo]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(GOOGLE_TOKENINFO_URL, params={"access_token": access_token})
    except Exception as e:
        return utils.err(e, "tokeninfo request failed")

    if resp.status_code != 200:
        return utils.err(Exception(f"tokeninfo returned {resp.status_code}: {resp.text}"))

    return utils.ok(TokenInfo.model_validate(resp.json()))
