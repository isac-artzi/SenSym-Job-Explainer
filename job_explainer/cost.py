"""A rough token-count and dollar-cost estimate, shown beside the button.

Deliberately approximate (PRD §7: "an estimate," not a bill) — this counts
characters, not real tokens, and uses per-call token constants observed
empirically rather than re-deriving the actual prompts. Good enough to give a
student a sense of scale before they click, not a substitute for provider
billing.
"""

from __future__ import annotations

from job_explainer.llm import LLMConfig

# $ per million tokens, (input, output), for each provider's pinned default
# model (see llm.DEFAULT_MODELS). Checked directly against each provider's
# pricing page in September 2026 — like the model IDs themselves, recheck
# before trusting this months later; model pricing moves at least as often
# as model names do.
PROVIDER_PRICING = {
    "anthropic": (2.00, 10.00),  # Claude Sonnet 5
    "openai": (10.00, 50.00),  # GPT-6 Astra
    "gemini": (0.75, 3.75),  # Gemini 3.8 Flash, standard tier
    "ollama": (0.0, 0.0),  # runs on your own hardware, no per-token cost
}

CHARS_PER_TOKEN = 4  # standard rough heuristic for English text

NUM_PANELS = 14

# Fixed overhead per call, on top of the posting text itself: prompt
# instructions plus, for the fourteen panel calls, the shared job-analysis
# JSON that rides along with every one of them.
ANALYSIS_CALL_OVERHEAD_TOKENS = 250
PANEL_CALL_OVERHEAD_TOKENS = 400

# Empirically observed output size per call.
ANALYSIS_OUTPUT_TOKENS = 350
PANEL_OUTPUT_TOKENS = 450


def estimate_tokens(posting_text: str) -> dict:
    """Estimate input/output token totals for one posting without calling any model."""
    posting_tokens = len(posting_text or "") // CHARS_PER_TOKEN

    analysis_input = posting_tokens + ANALYSIS_CALL_OVERHEAD_TOKENS
    panel_input = (posting_tokens + PANEL_CALL_OVERHEAD_TOKENS) * NUM_PANELS

    input_tokens = analysis_input + panel_input
    output_tokens = ANALYSIS_OUTPUT_TOKENS + PANEL_OUTPUT_TOKENS * NUM_PANELS

    return {"input_tokens": input_tokens, "output_tokens": output_tokens}


def estimate_cost(llm_config: LLMConfig, posting_text: str) -> dict:
    """Estimate the USD cost of explaining one posting. See estimate_tokens()."""
    tokens = estimate_tokens(posting_text)
    input_price, output_price = PROVIDER_PRICING.get(llm_config.provider, (0.0, 0.0))
    cost_usd = (
        tokens["input_tokens"] / 1_000_000 * input_price
        + tokens["output_tokens"] / 1_000_000 * output_price
    )
    return {**tokens, "cost_usd": cost_usd}
