"""FastAPI transport adapter for the Averse local prototype."""

from __future__ import annotations

import ipaddress
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.schemas import DemoComplaintRequest, ProcessRequest, ProcessResponse
from app.service import ApplicationService, build_default_service


async def require_loopback_client(request: Request) -> None:
    """Keep the demonstration complaint route local to the host machine."""
    client = request.client
    if client is None:
        raise HTTPException(status_code=403, detail="Local demonstration access only.")
    try:
        address = ipaddress.ip_address(client.host)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Local demonstration access only.") from exc
    if not address.is_loopback:
        raise HTTPException(status_code=403, detail="Local demonstration access only.")


def _safe_validation_message(error_type: str) -> str:
    return {
        "missing": "A required field is missing.",
        "string_type": "A field must be text.",
        "extra_forbidden": "The request contains an unsupported field.",
        "literal_error": "The request contains an unsupported demonstration value.",
    }.get(error_type, "The request is invalid.")


def create_app(
    service: ApplicationService | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    configuration = settings or Settings.from_environment()
    application_service = service or build_default_service(configuration)
    api = FastAPI(
        title="Averse local prototype API",
        description="Source-limited, local demonstration API. Not a customer complaint service.",
        version="0.1.0-prototype",
    )

    if configuration.cors_origins:
        api.add_middleware(
            CORSMiddleware,
            allow_origins=list(configuration.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @api.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors: list[dict[str, Any]] = []
        for error in exc.errors():
            location = [str(part) for part in error.get("loc", ())]
            error_type = str(error.get("type", "invalid"))
            errors.append(
                {
                    "loc": location,
                    "msg": _safe_validation_message(error_type),
                    "type": error_type,
                }
            )
        return JSONResponse(
            status_code=422,
            content={
                "request_id": "REQ-" + uuid.uuid4().hex,
                "action": "INVALID_REQUEST",
                "response_text": "The request is invalid. Check the request fields and try again.",
                "reason_code": "REQUEST_VALIDATION_FAILED",
                "errors": errors,
            },
        )

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-prototype"}

    @api.post("/api/v1/requests", response_model=ProcessResponse)
    async def process_request(payload: ProcessRequest) -> ProcessResponse:
        return application_service.process(payload)

    @api.post(
        "/api/v1/demo/complaints",
        response_model=ProcessResponse,
        dependencies=[Depends(require_loopback_client)],
    )
    async def demo_complaint(payload: DemoComplaintRequest) -> ProcessResponse:
        if not configuration.demo_enabled:
            raise HTTPException(status_code=404, detail="Demonstration workflow is disabled.")
        return application_service.process_demo_complaint(payload)

    return api


app = create_app()
