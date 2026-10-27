"""FastAPI entry point. Run from the project root:
    uvicorn backend.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import health
from backend.config import get_settings
from backend.database import init_db
from backend.models.schemas import fail
from backend.services.ai_provider import AIProviderError

logger = logging.getLogger("promptpilot")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="PromptPilot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)


@app.exception_handler(AIProviderError)
async def ai_error_handler(request: Request, exc: AIProviderError):
    return JSONResponse(status_code=exc.status_code, content=fail(exc.message))


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    return JSONResponse(
        status_code=422, content=fail(f"Invalid request: {where} {first.get('msg', '')}".strip())
    )


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))


@app.exception_handler(Exception)
async def unexpected_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", type(exc).__name__)  # type only: no stack, no content
    return JSONResponse(status_code=500, content=fail("Internal server error."))