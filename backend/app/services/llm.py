"""One place that talks to the AI provider.

AI_MODE=claude  -> Anthropic Claude API   (ANTHROPIC_API_KEY, AI_MODEL)
AI_MODE=gemini  -> Google Gemini API      (GEMINI_API_KEY, GEMINI_MODEL, default gemini-2.5-flash)
anything else   -> AI is off (no invented results)

Content is passed around as a list of Claude-style blocks (text / image / document, see documents.py);
for Gemini they are converted to `types.Part`s here.
"""
import base64
import logging
import time

from pydantic import BaseModel

from ..config import settings

log = logging.getLogger("llm")


class AIError(RuntimeError):
    """Error with a message that can be shown to the teacher."""


def provider() -> str | None:
    return settings.ai_mode if settings.ai_mode in ("claude", "gemini") else None


def model_name() -> str | None:
    p = provider()
    return settings.ai_model if p == "claude" else settings.gemini_model if p == "gemini" else None


def structured(system: str, content: list[dict], schema: type[BaseModel]) -> BaseModel:
    """Ask the AI and get back a validated `schema` instance."""
    p = provider()
    if p == "claude":
        return _claude_structured(system, content, schema)
    if p == "gemini":
        return _gemini_structured(system, content, schema)
    raise AIError("AI is not connected")


def text(system: str, prompt: str) -> str:
    """Plain text answer (lesson plans etc.)."""
    p = provider()
    if p == "claude":
        return _claude_text(system, prompt)
    if p == "gemini":
        return _gemini_text(system, prompt)
    raise AIError("AI is not connected")


# ================================================================ Claude
def _claude_errors(e: Exception) -> AIError:
    import anthropic

    if isinstance(e, anthropic.AuthenticationError):
        return AIError("Invalid or missing ANTHROPIC_API_KEY")
    if isinstance(e, anthropic.RateLimitError):
        return AIError("AI rate limit, try again in a minute")
    if isinstance(e, anthropic.APIConnectionError):
        return AIError("No connection to the AI service")
    if isinstance(e, anthropic.APIStatusError):
        return AIError(f"AI error: {e.message}")
    return AIError(str(e))


def _claude_structured(system, content, schema):
    import anthropic

    try:
        response = anthropic.Anthropic().beta.messages.parse(
            model=settings.ai_model,
            max_tokens=16000,
            system=system,
            output_config={"effort": "medium"},
            output_format=schema,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.APIError as e:
        raise _claude_errors(e) from e
    if response.stop_reason == "refusal":
        raise AIError("AI declined this request")
    if response.stop_reason == "max_tokens":
        raise AIError("AI answer was cut off (too long)")
    if response.parsed_output is None:
        raise AIError("AI returned no result")
    return response.parsed_output


def _claude_text(system, prompt):
    import anthropic

    try:
        response = anthropic.Anthropic().beta.messages.create(
            model=settings.ai_model,
            max_tokens=16000,
            system=system,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise _claude_errors(e) from e
    if response.stop_reason == "refusal":
        raise AIError("AI declined this request")
    return "".join(b.text for b in response.content if b.type == "text").strip()


# ================================================================ Gemini
GEMINI_TIMEOUT_MS = 120_000  # one request may not hang longer than 2 minutes


def _gemini_client():
    from google import genai
    from google.genai import types

    if not settings.gemini_api_key:
        raise AIError("GEMINI_API_KEY is empty in backend/.env")
    return genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS))


def _to_gemini_parts(content: list[dict]):
    from google.genai import types

    parts = []
    for block in content:
        kind = block.get("type")
        if kind == "text":
            parts.append(types.Part.from_text(text=block["text"]))
        elif kind in ("image", "document"):
            src = block["source"]
            parts.append(types.Part.from_bytes(data=base64.b64decode(src["data"]), mime_type=src["media_type"]))
    return parts


def _gemini_call(system: str, contents, schema: type[BaseModel] | None):
    from google.genai import errors, types

    client = _gemini_client()
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0.2,
        max_output_tokens=32768,
        **({"response_mime_type": "application/json", "response_schema": schema} if schema else {}),
    )
    # Main model first, then backups (GEMINI_FALLBACK_MODELS) when a model is overloaded or unavailable.
    models = list(dict.fromkeys([settings.gemini_model, *settings.gemini_fallback_models]))
    last_error: AIError | None = None
    for model in models:
        for attempt in range(3):  # Gemini sometimes answers 503 "overloaded" / 429: retry a little
            try:
                return client.models.generate_content(model=model, contents=contents, config=config)
            except errors.APIError as e:
                code = getattr(e, "code", None)
                if code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                last_error = _gemini_error(e)
                if code in (404, 500, 502, 503, 504):
                    log.warning("Gemini model %s failed (%s), trying the next one", model, code)
                    break  # next model
                raise last_error from e
            except Exception as e:  # network problems / timeout: one more try, then give up
                if attempt < 1:
                    time.sleep(2)
                    continue
                raise AIError("No answer from Gemini (network problem or timeout), try again") from e
    raise last_error or AIError("Gemini returned no answer")


def _gemini_error(e) -> AIError:
    code = getattr(e, "code", None)
    msg = (getattr(e, "message", None) or str(e)).strip()
    if code == 400 and "API key" in msg:
        return AIError("GEMINI_API_KEY is not valid")
    if code in (401, 403):
        return AIError("Gemini: access denied, check GEMINI_API_KEY")
    if code == 429:
        return AIError("Gemini: quota / rate limit reached, try again later")
    if code == 404:
        return AIError(f"Gemini: model '{settings.gemini_model}' is not available ({msg[:200]}). Change GEMINI_MODEL in backend/.env")
    if code == 503:
        return AIError("Gemini is overloaded right now, try again in a minute")
    return AIError(f"Gemini error {code}: {msg[:300]}")


def _gemini_check(response) -> None:
    if not response.candidates:
        reason = getattr(getattr(response, "prompt_feedback", None), "block_reason", None)
        raise AIError(f"Gemini blocked the request ({reason})" if reason else "Gemini returned no answer")
    finish = str(response.candidates[0].finish_reason or "")
    if "MAX_TOKENS" in finish:
        raise AIError("AI answer was cut off (too long)")
    if "SAFETY" in finish or "PROHIBITED" in finish:
        raise AIError("Gemini declined this request")


def _gemini_structured(system, content, schema):
    response = _gemini_call(system, _to_gemini_parts(content), schema)
    _gemini_check(response)
    parsed = response.parsed
    if isinstance(parsed, schema):
        return parsed
    try:
        return schema.model_validate_json(response.text or "")
    except Exception as e:
        log.warning("Gemini JSON did not match the schema: %s", (response.text or "")[:500])
        raise AIError("Gemini returned an answer in an unexpected format, try again") from e


def _gemini_text(system, prompt):
    response = _gemini_call(system, prompt, None)
    _gemini_check(response)
    return (response.text or "").strip()
