from collections.abc import Awaitable, Callable

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from .result import Result, err, ok

type Handler[Req: BaseModel, Resp: BaseModel] = Callable[[Req], Awaitable[Result[Resp]]]

METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


async def safe_json(request: Request) -> Result[dict]:
    try:
        body = await request.json()
    except Exception as e:
        return err(e, "Failed to parse JSON body")
    if not isinstance(body, dict):
        return err(ValueError("request body must be a JSON object"))
    return ok(body)


def safe_validate[T: BaseModel](cls: type[T], data: dict[str, object]) -> Result[T]:
    try:
        return ok(cls.model_validate(data))
    except ValidationError as e:
        return err(e)


async def handle_api[Req: BaseModel, Resp: BaseModel](request: Request, req_cls: type[Req], handler: Handler[Req, Resp]) -> JSONResponse:
    data: dict[str, object] = {}
    data.update(request.path_params)
    data.update(request.query_params)

    if request.method in METHODS_WITH_BODY:
        body, error = await safe_json(request)
        if error:
            return JSONResponse({"error": str(error)}, status_code=400)
        data.update(body)

    req, error = safe_validate(req_cls, data)
    if error:
        return JSONResponse({"error": str(error)}, status_code=422)

    resp, error = await handler(req)
    if error:
        return JSONResponse({"error": str(error)}, status_code=400)

    return JSONResponse(resp.model_dump(), status_code=200)
