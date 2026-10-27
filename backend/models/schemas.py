"""Pydantic schemas shared across the API. Every response uses ApiResponse."""
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: str | None = None


def ok(data: Any = None) -> ApiResponse:
    return ApiResponse(success=True, data=data)


def fail(message: str) -> dict:
    return {"success": False, "data": None, "error": message}