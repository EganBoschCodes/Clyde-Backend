import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from clyde.mcp_app import MCP

from .google import GOOGLE_TOKEN_URL


@MCP.custom_route("/token", methods=["POST"])
async def token_proxy(request: Request) -> Response:
    body = await request.body()
    content_type = request.headers.get("content-type", "application/x-www-form-urlencoded")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            upstream = await client.post(
                GOOGLE_TOKEN_URL,
                content=body,
                headers={"Content-Type": content_type},
            )
    except Exception as e:
        return JSONResponse({"error": "token_proxy_failed", "detail": str(e)}, status_code=502)

    media_type = upstream.headers.get("content-type", "application/json")
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=media_type)
