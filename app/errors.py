from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        if error.get("type") == "json_invalid":
            return JSONResponse(
                status_code=400,
                content={"message": "Request body is not valid JSON", "code": "MALFORMED_JSON"},
            )
    first = errors[0] if errors else {}
    field = first.get("loc", ["field"])[-1]
    return JSONResponse(
        status_code=422,
        content={"message": f"{field} is required", "code": "VALIDATION_ERROR"},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})
