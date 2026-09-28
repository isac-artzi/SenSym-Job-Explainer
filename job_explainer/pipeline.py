"""The job-explanation pipeline: analysis, then fourteen panels in parallel.

Every step is one `llm.complete_json()` or `llm.complete()` call against a
prompt template in `prompts/`. Templates use `$name` placeholders (Python's
`string.Template`) rather than `str.format`, because the prompts contain
literal JSON examples full of `{`/`}` that `.format()` would try to parse as
fields.

`PETALS` is the one place that defines every panel: its prompt file, its
title, which ring of the bloom it sits in, and which grid cell it occupies
(see PRD §8.3). `app.py` lays out the grid from it, this module loads each
panel's prompt from it, and `render.py` orders the DOCX from it. Adding a
fifteenth panel is one prompt file plus one entry here (and, if the grid is
full, widening it) — see EXTENDING.md.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Callable

from job_explainer.llm import LLMConfig, LLMError, complete, complete_json

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

RETURN_JSON_ONLY = "Return only the JSON object specified above. No prose, no markdown fences."


@dataclass(frozen=True)
class Petal:
    number: int
    slug: str
    title: str
    ring: int  # 1 (innermost, around the seed) to 3 (outermost)
    grid_cell: tuple[int, int]  # (row, col), 0-indexed, in the 5x3 bloom grid

    @property
    def key(self) -> str:
        return f"{self.number:02d}_{self.slug}"

    def prompt_path(self) -> Path:
        return PROMPTS_DIR / "petals" / f"{self.key}.txt"


# Grid layout mirrors PRD §8.3: ring 1 hugs the seed at (2, 1), ring 2 forms
# the next ring out, ring 3 the outermost. Panel order (01-14) is the bloom
# order and the DOCX order, independent of the grid position.
PETALS: list[Petal] = [
    Petal(1, "what_it_is", "What this job is", 1, (1, 1)),
    Petal(2, "skills", "Skills you'll need", 1, (2, 0)),
    Petal(3, "experience", "Experience and how to show it", 1, (2, 2)),
    Petal(4, "between_the_lines", "Between the lines", 1, (3, 1)),
    Petal(5, "learn_more", "Learn more about this job", 2, (1, 0)),
    Petal(6, "find_the_people", "Find the people who do this", 2, (1, 2)),
    Petal(7, "similar_jobs", "Similar jobs", 2, (3, 0)),
    Petal(8, "the_path", "The path to get there", 2, (3, 2)),
    Petal(9, "outlook", "Outlook, 3-5 years", 3, (0, 0)),
    Petal(10, "what_it_becomes", "What this job becomes", 3, (0, 1)),
    Petal(11, "ai_and_this_job", "AI and this job", 3, (0, 2)),
    Petal(12, "jargon_decoder", "Jargon decoder", 3, (4, 0)),
    Petal(13, "a_week_in_this_job", "A week in this job", 3, (4, 1)),
    Petal(14, "questions_to_ask", "Questions to ask, things to check", 3, (4, 2)),
]

SEED_GRID_CELL = (2, 1)


def _load_template(path: Path) -> Template:
    return Template(path.read_text(encoding="utf-8"))


def analyze_job(job_text: str, llm_config: LLMConfig) -> dict:
    """Step 2: one call, shared by every panel."""
    prompt = _load_template(PROMPTS_DIR / "job_analysis.txt").substitute(job_text=job_text)
    return complete_json(llm_config, prompt, RETURN_JSON_ONLY)


def run_petal(petal: Petal, job_text: str, analysis: dict, reading_level: str, llm_config: LLMConfig) -> str:
    """Step 3, one panel: run its prompt and return Markdown text.

    Raises LLMError on failure; callers isolate this per panel so one bad
    call never fails the whole bloom (PRD §7 step 3, F11).
    """
    template = _load_template(petal.prompt_path())
    prompt = template.substitute(
        job_text=job_text,
        analysis_json=json.dumps(analysis, indent=2),
        reading_level=reading_level,
    )
    return complete(llm_config, prompt)


@dataclass
class PetalResult:
    petal: Petal
    markdown: str = ""
    error: str | None = None


def generate_petals(
    job_text: str,
    analysis: dict,
    reading_level: str,
    llm_config: LLMConfig,
    parallel_calls: int,
    on_complete: Callable[[PetalResult], None] | None = None,
) -> dict[str, PetalResult]:
    """Step 3, all fourteen panels: run in a thread pool, `parallel_calls` at a time.

    Worker threads only call `llm.complete()` and return strings — no
    Streamlit calls happen off the main thread (PRD §13). `on_complete` is
    invoked on the main thread as each future resolves, so the caller can
    update a status placeholder ("Growing 5 of 14 panels...").
    """
    results: dict[str, PetalResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, parallel_calls)) as executor:
        future_to_petal = {
            executor.submit(run_petal, petal, job_text, analysis, reading_level, llm_config): petal
            for petal in PETALS
        }
        for future in as_completed(future_to_petal):
            petal = future_to_petal[future]
            try:
                markdown = future.result()
                result = PetalResult(petal=petal, markdown=markdown)
            except LLMError as exc:
                result = PetalResult(petal=petal, error=str(exc))
            except Exception as exc:  # noqa: BLE001 - one panel's failure must not sink the bloom
                result = PetalResult(petal=petal, error=f"Something went wrong generating this panel: {exc}")
            results[petal.key] = result
            if on_complete is not None:
                on_complete(result)
    return results
