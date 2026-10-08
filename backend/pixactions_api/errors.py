from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SOLD_OUT = "SOLD_OUT"
    ORDER_NOT_FUNDED = "ORDER_NOT_FUNDED"
    TX_MISMATCH = "TX_MISMATCH"
    TX_EXPIRED = "TX_EXPIRED"
    TX_STALE = "TX_STALE"
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"
    RPC_ERROR = "RPC_ERROR"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.SOLD_OUT: 409,
    ErrorCode.ORDER_NOT_FUNDED: 409,
    ErrorCode.TX_MISMATCH: 400,
    ErrorCode.TX_EXPIRED: 409,
    ErrorCode.TX_STALE: 409,
    ErrorCode.ALREADY_CHECKED_IN: 409,
    ErrorCode.RPC_ERROR: 502,
}

ERROR_DESCRIPTIONS: dict[ErrorCode, str] = {
    ErrorCode.UNAUTHORIZED: "missing, invalid or expired Privy access token",
    ErrorCode.NOT_FOUND: "resource does not exist or does not belong to you",
    ErrorCode.VALIDATION_ERROR: "request body or parameters are invalid",
    ErrorCode.SOLD_OUT: "the event has no tickets left",
    ErrorCode.ORDER_NOT_FUNDED: "the order is not ready to be signed (Pix not confirmed yet)",
    ErrorCode.TX_MISMATCH: "the signed transaction differs from the one issued, or lacks a signature",
    ErrorCode.TX_EXPIRED: "the transaction blockhash expired; fetch a fresh transaction",
    ErrorCode.TX_STALE: "a concurrent purchase took this ticket slot; fetch a fresh transaction",
    ErrorCode.ALREADY_CHECKED_IN: "the ticket was already used",
    ErrorCode.RPC_ERROR: "Solana RPC failure",
}


class ApiError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    @property
    def status_code(self) -> int:
        return HTTP_STATUS[self.code]


class ErrorBody(BaseModel):
    code: ErrorCode = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Human-readable explanation.")
    details: dict[str, Any] = Field(default_factory=dict, description="Optional structured context.")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"error": {"code": "SOLD_OUT", "message": "Event is sold out", "details": {}}}]
        }
    )
    error: ErrorBody


def error_responses(*codes: ErrorCode) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses=` entries for the given error codes, grouped by HTTP status."""
    out: dict[int | str, dict[str, Any]] = {}
    for code in codes:
        entry = out.setdefault(HTTP_STATUS[code], {"model": ErrorResponse, "description": ""})
        line = f"`{code}`: {ERROR_DESCRIPTIONS[code]}"
        entry["description"] = f"{entry['description']}; {line}" if entry["description"] else line
    return out


def _payload(code: ErrorCode, message: str, details: dict[str, Any] | None = None) -> dict:
    return {"error": {"code": code.value, "message": message, "details": details or {}}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_payload(exc.code, exc.message, exc.details), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{k: e[k] for k in ("loc", "msg", "type") if k in e} for e in exc.errors()]
        return JSONResponse(
            _payload(ErrorCode.VALIDATION_ERROR, "Request validation failed", {"errors": errors}),
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: ErrorCode.NOT_FOUND, 401: ErrorCode.UNAUTHORIZED, 403: ErrorCode.UNAUTHORIZED}.get(
            exc.status_code, ErrorCode.VALIDATION_ERROR
        )
        return JSONResponse(_payload(code, str(exc.detail)), status_code=exc.status_code)
