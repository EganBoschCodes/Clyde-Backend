from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP


@MCP.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
@MCP.custom_route("/.well-known/oauth-protected-resource/{rest:path}", methods=["GET"])
async def oauth_protected_resource(request: Request) -> JSONResponse:
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.hostname or "localhost")
    base = f"{scheme}://{host}"

    return JSONResponse({
        "resource": f"{base}/mcp",
        "authorization_servers": [base],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
    })


@MCP.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_authorization_server(request: Request) -> JSONResponse:
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.hostname or "localhost")
    base = f"{scheme}://{host}"

    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "scopes_supported": ["openid", "email", "profile"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
    })
