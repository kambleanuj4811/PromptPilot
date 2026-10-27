"""Vendor-neutral AI interface. Add another provider by subclassing AIProvider
and implementing generate_text(); everything else (structured output, retry
and repair) is inherited."""
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from backend.services.validation_service import extract_json

T = TypeVar("T", bound=BaseModel)


class AIProviderError(Exception):
    status_code = 502

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AIConfigError(AIProviderError):
    status_code = 503


class AIQuotaError(AIProviderError):
    status_code = 429


class AITimeoutError(AIProviderError):
    status_code = 504


class AIInvalidResponseError(AIProviderError):
    status_code = 502


class AIProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text. Must raise AIProviderError subclasses."""

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
        max_retries: int = 2,
        temperature: float | None = None,
    ) -> T:
        """Call the model, parse JSON, validate with Pydantic.

        On invalid output, ask the model to repair it. Total attempts are
        capped at max_retries + 1, so it can never loop forever."""
        attempt_prompt = prompt
        last_error = "unknown error"
        for _ in range(max_retries + 1):
            raw = self.generate_text(
                attempt_prompt, system=system, temperature=temperature, json_mode=True
            )
            try:
                return schema.model_validate(extract_json(raw))
            except ValueError as exc:  # JSONDecodeError and ValidationError both subclass it
                last_error = str(exc)[:500]
                attempt_prompt = (
                    f"{prompt}\n\n---\nYour previous reply was invalid.\n"
                    f"Problem: {last_error}\n"
                    f"Previous reply (truncated):\n{raw[:1500]}\n\n"
                    "Return ONLY corrected JSON that matches the required schema. "
                    "No commentary, no code fences."
                )
        raise AIInvalidResponseError(
            f"The AI did not return valid structured output after {max_retries + 1} attempts: {last_error}"
        )