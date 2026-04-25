import urllib.parse

from starlette.requests import Request
from starlette.responses import RedirectResponse

from clyde.mcp_app import MCP

from .google import GOOGLE_AUTHORIZE_URL


@MCP.custom_route("/authorize", methods=["GET"])
async def authorize_redirect(request: Request) -> RedirectResponse:
    params = dict(request.query_params)
    if "scope" not in params or not params["scope"].strip():
        params["scope"] = "openid email profile"
    params["access_type"] = "offline"
    params["prompt"] = "consent"
    target = f"{GOOGLE_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=target, status_code=302)
