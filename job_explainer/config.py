"""Load, validate, and generate `job_explainer.env`.

The config never touches disk on the server in cloud mode — it is parsed
into a plain dict and held in `st.session_state`. Local mode may load
`job_explainer.env` from the repo root if the student put one there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROVIDERS = ["anthropic", "openai", "gemini", "ollama"]

DEFAULT_PARALLEL_CALLS = "4"
DEFAULT_READING_LEVEL = "first-year undergraduate"

# (key, comment, default) in the order they should appear in a generated file
FIELDS = [
    ("LLM_PROVIDER", "anthropic | openai | gemini | ollama", "anthropic"),
    ("API_KEY", "leave blank for ollama", ""),
    ("MODEL", "optional; provider default used if blank", ""),
    ("OLLAMA_BASE_URL", "ollama only", "http://localhost:11434"),
    ("PARALLEL_CALLS", "panels generated at once; use 1 for ollama", DEFAULT_PARALLEL_CALLS),
    ("READING_LEVEL", 'e.g. "first-year undergraduate" (default) or "high school"', ""),
]

SECTION_BREAKS = {
    "LLM_PROVIDER": "--- AI provider ---",
    "PARALLEL_CALLS": "--- Generation (all optional) ---",
}


@dataclass
class AppConfig:
    values: dict = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default) or default

    @property
    def provider(self) -> str:
        return self.get("LLM_PROVIDER", "anthropic")

    @property
    def api_key(self) -> str:
        return self.get("API_KEY")

    @property
    def model(self) -> str:
        return self.get("MODEL")

    @property
    def ollama_base_url(self) -> str:
        return self.get("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def parallel_calls(self) -> int:
        raw = self.get("PARALLEL_CALLS", DEFAULT_PARALLEL_CALLS)
        try:
            value = int(raw)
        except ValueError:
            return int(DEFAULT_PARALLEL_CALLS)
        return max(1, value)

    @property
    def reading_level(self) -> str:
        return self.get("READING_LEVEL", DEFAULT_READING_LEVEL) or DEFAULT_READING_LEVEL


def parse_env_text(text: str) -> dict:
    """Parse simple `KEY=value` lines. Blank lines and `#` comments are ignored."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.split("#", 1)[0].strip() if "#" in value else value.strip()
        values[key] = value
    return values


def load_env_file(path: Path) -> dict | None:
    """Read `job_explainer.env` from `path` if it exists, else return None."""
    if not path.exists():
        return None
    return parse_env_text(path.read_text(encoding="utf-8"))


def generate_env_text(values: dict) -> str:
    """Render a config dict back out as a commented `.env` file the student can re-upload."""
    lines = []
    for key, comment, default in FIELDS:
        if key in SECTION_BREAKS:
            if lines:
                lines.append("")
            lines.append(f"# {SECTION_BREAKS[key]}")
        value = values.get(key, default)
        suffix = f"  # {comment}" if comment else ""
        lines.append(f"{key}={value}{suffix}")
    return "\n".join(lines) + "\n"


def validate(config: AppConfig) -> list[str]:
    """Return a list of human-readable problems; empty list means ready to generate."""
    problems = []
    if config.provider not in PROVIDERS:
        problems.append(f"Unknown provider '{config.provider}'.")
    if config.provider != "ollama" and not config.api_key:
        problems.append("An API key is required for this provider.")
    return problems
