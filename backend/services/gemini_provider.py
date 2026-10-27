"""Gemini implementation using the official google-genai SDK."""
from backend.services.ai_provider import (
    AIConfigError,
    AIInvalidResponseError,
    AIProvider,
    AIProviderError,
    AIQuotaError,
    AITimeoutError,
)

REQUEST_TIMEOUT_MS = 60_000


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self.model = model
        self._client = None

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if not self._api_key:
            raise AIConfigError("GEMINI_API_KEY is not set. Add it to your .env file and restart.")
        if self._client is None:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
            )
        return self._client

    def _translate(self, exc) -> AIProviderError:
        code = getattr(exc, "code", None)
        message = str(getattr(exc, "message", "") or "")
        if code == 429:
            return AIQuotaError(
                "Gemini quota or rate limit reached. Wait a minute and retry; "
                "free-tier limits also reset daily."
            )
        if code in (401, 403) or (code == 400 and "api key" in message.lower()):
            return AIConfigError("Gemini rejected the API key. Check GEMINI_API_KEY in .env.")
        if code == 404:
            return AIConfigError(
                f"Model '{self.model}' was not found. Run python scripts\\check_env.py "
                "to list available models, then update GEMINI_MODEL."
            )
        return AIProviderError(f"Gemini API error (HTTP {code}).")

    def generate_text(self, prompt, system=None, temperature=None, json_mode=False) -> str:
        client = self._get_client()
        from google.genai import errors, types

        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        try:
            response = client.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
        except errors.APIError as exc:
            raise self._translate(exc) from None
        except Exception as exc:  # network, timeout, etc. Never include details that could leak keys
            if "timeout" in type(exc).__name__.lower():
                raise AITimeoutError("The AI request timed out. Try again.") from None
            raise AIProviderError(f"AI request failed ({type(exc).__name__}).") from None

        text = response.text
        if not text:
            raise AIInvalidResponseError(
                "The AI returned an empty response (it may have been blocked by safety filters)."
            )
        return text