"""One thin client over four LLM providers: Anthropic, OpenAI, Gemini, Ollama.

Every other module only ever calls `complete()` or `complete_json()`. Provider
differences (auth, request shape, JSON mode) are confined to this file so the
rest of the app never has to know which provider is active.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# Pinned default model per provider. Check each provider's docs before
# bumping these — a student's config can always override with MODEL=.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-6-astra",
    "gemini": "gemini-3.8-flash",
    "ollama": "llama3.1",
}

MAX_RETRIES_ON_BAD_JSON = 1


class LLMError(Exception):
    """Raised with a message that is safe to show directly in the UI."""


@dataclass
class LLMConfig:
    provider: str  # anthropic | openai | gemini | ollama
    api_key: str = ""
    model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.4

    def resolved_model(self) -> str:
        return self.model.strip() if self.model.strip() else DEFAULT_MODELS[self.provider]


def complete(config: LLMConfig, prompt: str) -> str:
    """Send `prompt` and return the text reply."""
    try:
        if config.provider == "anthropic":
            return _complete_anthropic(config, prompt)
        if config.provider == "openai":
            return _complete_openai(config, prompt)
        if config.provider == "gemini":
            return _complete_gemini(config, prompt)
        if config.provider == "ollama":
            return _complete_ollama(config, prompt)
    except LLMError:
        raise
    except Exception as exc:  # provider SDK error -> friendly message
        raise LLMError(_friendly_error(config.provider, exc)) from exc

    raise LLMError(f"Unknown provider '{config.provider}'.")


def complete_json(config: LLMConfig, prompt: str, schema_hint: str) -> dict:
    """Like `complete()`, but parses the reply as JSON.

    `schema_hint` is plain-text guidance appended to the prompt describing
    the expected JSON shape (not a formal JSON Schema — kept simple so
    students can read and edit prompts in `prompts/`). On malformed JSON,
    retries once with the parse error fed back to the model, then raises a
    friendly LLMError.
    """
    full_prompt = f"{prompt}\n\n{schema_hint}\n\nRespond with valid JSON only. No prose, no markdown fences."

    last_error = None
    for attempt in range(MAX_RETRIES_ON_BAD_JSON + 1):
        raw = complete(config, full_prompt)
        try:
            return _parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            full_prompt = (
                f"{prompt}\n\n{schema_hint}\n\n"
                "Respond with valid JSON only. No prose, no markdown fences.\n\n"
                f"Your previous reply could not be parsed as JSON ({exc}). "
                "Reply again with corrected, valid JSON only."
            )

    raise LLMError(
        "The model returned a response that could not be read as data, even after a retry. "
        "Try again, or switch to a different model in Settings."
    )


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in reply")
    return json.loads(text[start : end + 1])


def _friendly_error(provider: str, exc: Exception) -> str:
    text = str(exc).lower()
    if "api key" in text or "authentication" in text or "401" in text:
        return f"{provider.title()} rejected the API key. Check it in Settings and try again."
    if "rate limit" in text or "429" in text:
        return f"{provider.title()} rate-limited this request. Wait a moment and try again."
    if "connection" in text or "timeout" in text or "timed out" in text:
        return f"Could not reach {provider.title()}. Check your internet connection (and, for Ollama, that it is running)."
    return f"{provider.title()} returned an error: {exc}"


# --- Anthropic -----------------------------------------------------------


def _complete_anthropic(config: LLMConfig, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.api_key)
    # Current Anthropic models (Claude 5 family) control response character via
    # reasoning effort rather than `temperature`, which the API no longer accepts,
    # and default to extended thinking that otherwise eats most of max_tokens
    # before any visible text is written. Thinking is disabled so the full
    # budget goes to visible output.
    response = client.messages.create(
        model=config.resolved_model(),
        max_tokens=4096,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


# --- OpenAI (also used for Ollama's OpenAI-compatible endpoint) ----------


def _complete_openai(config: LLMConfig, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.api_key)
    return _openai_chat(client, config, prompt)


def _complete_ollama(config: LLMConfig, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=f"{config.ollama_base_url.rstrip('/')}/v1", api_key="ollama")
    return _openai_chat(client, config, prompt)


def _openai_chat(client, config: LLMConfig, prompt: str) -> str:
    response = client.chat.completions.create(
        model=config.resolved_model(),
        temperature=config.temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


# --- Gemini ----------------------------------------------------------------


def _complete_gemini(config: LLMConfig, prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.api_key)
    response = client.models.generate_content(
        model=config.resolved_model(),
        contents=[prompt],
        config=types.GenerateContentConfig(temperature=config.temperature),
    )
    return response.text or ""
