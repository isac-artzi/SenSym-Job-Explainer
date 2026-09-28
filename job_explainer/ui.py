"""Brand tokens, CSS (including the bloom keyframes), and small UI helpers.

Palette and wordmark are copied from Resume Match so the two apps read as
siblings (PRD: "same conventions"). Everything visual lives here so a real
SenSym logo/color can replace the neutral placeholder later by editing this
one file.
"""

from __future__ import annotations

import streamlit as st

from job_explainer.pipeline import PETALS, SEED_GRID_CELL

ACCENT_COLOR = "#C1662E"  # warm terracotta
ACCENT_SOFT = "#F3DCC2"  # soft tint, for hover/highlight backgrounds
ACCENT_DARK = "#A24F1F"  # hover/active state for accent-colored buttons
TEXT_COLOR = "#2B2420"  # warm near-black
MUTED_TEXT_COLOR = "#8A7566"  # warm muted brown-gray
BACKGROUND_COLOR = "#FFFCF8"  # warm off-white
SURFACE_COLOR = "#F8F1E7"  # warm sand
BORDER_COLOR = "#EADFD0"  # warm taupe

APP_NAME = "SenSym Job Explainer"
APP_TAGLINE = "Paste a job posting. Understand the job."
PRIVACY_LINE = "Nothing you paste is stored."
WORDMARK_TEXT = "SenSym™"  # TODO: replace with the real SVG wordmark once brand assets arrive

# Grid geometry used both for Streamlit's column layout and for the CSS
# translate() distances the bloom animates from. Approximate card widths at
# the 1024px+ design target (PRD §8.3) — pixel-perfect isn't the point, a
# plausible "flying out from the center" distance is.
GRID_ROWS = 5
GRID_COLS = 3
CELL_DX = 372  # px between adjacent columns
CELL_DY = 344  # px between adjacent rows
RING_BASE_DELAY_MS = {1: 0, 2: 220, 3: 440}
RING_STAGGER_MS = 60
PETAL_CARD_HEIGHT = 320

TOOLTIPS = {
    "provider": "Which AI service writes your panels. Anthropic is the default; Ollama runs "
    "a model on your own computer, needs no key, and only works when run locally.",
    "api_key": "From your provider's website (e.g. console.anthropic.com for Anthropic). Held "
    "only in this browser session — never written to disk by the app, never sent anywhere "
    "except your provider.",
    "model": "Overrides the provider's default model. Leave blank unless you know the exact "
    "model name you want.",
    "ollama_url": "The address Ollama is listening on. The default is correct unless you "
    "changed Ollama's port.",
    "parallel_calls": "How many panels generate at once. Lower this to 1 for Ollama, which "
    "usually can't run several requests at the same time.",
    "reading_level": 'e.g. "first-year undergraduate" (default) or "high school".',
    "config_upload": "Upload a config file you downloaded from this app before — it fills in "
    "your provider, key, and preferences automatically for this session.",
    "download_config": "Saves your current settings — including your API key in plain text — "
    "as job_explainer.env, so you can re-upload it next time instead of retyping everything. "
    "Keep the downloaded file private.",
}


def inject_base_css() -> None:
    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header [data-testid="stToolbar"] {{visibility: hidden;}}

        html, body, [class*="css"] {{
            font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
            color: {TEXT_COLOR};
        }}

        body {{
            background-color: {BACKGROUND_COLOR};
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }}

        /* --- Landing (State A) --- */

        .st-key-landing {{
            max-width: 640px;
            margin: 4vh auto 0 auto;
        }}

        /* "Read as a page" (State C, single column) — a bit wider than the
        landing box so pipe tables have room to breathe. */
        .st-key-page-view {{
            max-width: 760px;
            margin: 0 auto;
        }}

        .je-wordmark {{
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            color: {ACCENT_COLOR};
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }}

        .je-title {{
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
            color: {TEXT_COLOR};
        }}

        .je-tagline {{
            font-size: 1.05rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 1.4rem;
        }}

        .je-privacy-inline {{
            font-size: 0.82rem;
            color: {MUTED_TEXT_COLOR};
        }}

        .je-example-link {{
            font-size: 0.85rem;
            margin-top: 0.4rem;
        }}

        /* Settings popover trigger styled as a quiet link, not a button */
        div[data-testid="stPopover"] > div > button {{
            background: transparent !important;
            border: none !important;
            color: {MUTED_TEXT_COLOR} !important;
            font-size: 0.85rem !important;
            padding: 0 !important;
            box-shadow: none !important;
        }}

        div[data-testid="stPopover"] > div > button:hover {{
            color: {ACCENT_COLOR} !important;
            text-decoration: underline;
        }}

        /* "Try an example" / plain-link buttons */
        .je-link-button button {{
            background: transparent !important;
            border: none !important;
            color: {MUTED_TEXT_COLOR} !important;
            font-size: 0.85rem !important;
            padding: 0 !important;
            box-shadow: none !important;
            text-decoration: underline;
            text-decoration-color: {BORDER_COLOR};
        }}

        .je-link-button button:hover {{
            color: {ACCENT_COLOR} !important;
            text-decoration-color: {ACCENT_COLOR};
        }}

        /* --- Buttons, generally --- */

        div.stButton > button, div.stDownloadButton > button {{
            border-radius: 8px;
            border-color: {BORDER_COLOR};
            transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
        }}

        div.stButton > button:hover, div.stDownloadButton > button:hover {{
            transform: translateY(-1px);
            border-color: {ACCENT_COLOR};
            box-shadow: 0 3px 8px rgba(193, 102, 46, 0.15);
        }}

        div.stButton > button[kind="primary"] {{
            background-color: {ACCENT_COLOR};
            border-color: {ACCENT_COLOR};
        }}

        div.stButton > button[kind="primary"]:hover {{
            background-color: {ACCENT_DARK};
            border-color: {ACCENT_DARK};
            box-shadow: 0 4px 10px rgba(162, 79, 31, 0.3);
        }}

        /* --- Seed card (States B and C) --- */

        .st-key-seed {{
            background: linear-gradient(160deg, {SURFACE_COLOR} 0%, {BACKGROUND_COLOR} 100%);
            border-color: {ACCENT_SOFT} !important;
        }}

        .je-seed-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {TEXT_COLOR};
            margin-bottom: 0.15rem;
        }}

        .je-seed-meta {{
            font-size: 0.82rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.6rem;
        }}

        .je-seed-status {{
            font-size: 0.88rem;
            color: {ACCENT_COLOR};
            font-weight: 600;
        }}

        @keyframes je-pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.55; }}
        }}

        .je-pulsing {{
            animation: je-pulse 1.6s ease-in-out infinite;
        }}

        /* --- Petal cards (State C) --- */

        .je-petal-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: {ACCENT_COLOR};
            margin-bottom: 0.35rem;
        }}

        .je-petal-error {{
            font-size: 0.88rem;
            color: {MUTED_TEXT_COLOR};
            font-style: italic;
        }}

        hr {{
            border-color: {BORDER_COLOR};
        }}

        /* Resting state for every bloom cell: default to fully visible so a
        page with no bloom CSS injected (every render after the first) shows
        a static grid with no animation. */
        {_resting_state_selector()} {{
            opacity: 1;
            transform: none;
        }}

        @media (prefers-reduced-motion: reduce) {{
            {_resting_state_selector()} {{
                animation: none !important;
                transform: none !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _resting_state_selector() -> str:
    keys = [".st-key-seed"] + [f".st-key-petal-{p.number:02d}" for p in PETALS]
    return ", ".join(keys)


def bloom_css() -> str:
    """CSS for the once-per-generation reveal (PRD §8.3).

    Built fresh each call so it can be injected only on the run right after
    generation completes (`just_bloomed`), and never again — that single
    injection is what keeps the animation from replaying on later reruns.
    Reduced-motion users get the same timing with the transform dropped, via
    the same `prefers-reduced-motion` media query used in inject_base_css().
    """
    seed_row, seed_col = SEED_GRID_CELL
    rules = [
        """
        @keyframes je-seed-settle {
            from { transform: scale(1.06); }
            to { transform: scale(1); }
        }
        .st-key-seed {
            animation: je-seed-settle 500ms ease-out both;
        }
        """
    ]

    by_ring: dict[int, list] = {}
    for petal in PETALS:
        by_ring.setdefault(petal.ring, []).append(petal)

    for ring, petals in by_ring.items():
        base_delay = RING_BASE_DELAY_MS.get(ring, 0)
        for index, petal in enumerate(sorted(petals, key=lambda p: p.number)):
            row, col = petal.grid_cell
            dx = (seed_col - col) * CELL_DX
            dy = (seed_row - row) * CELL_DY
            delay = base_delay + index * RING_STAGGER_MS
            anim_name = f"je-fly-{petal.number:02d}"
            rules.append(
                f"""
                @keyframes {anim_name} {{
                    from {{ opacity: 0; transform: scale(0.55) translate({dx}px, {dy}px); }}
                    to {{ opacity: 1; transform: none; }}
                }}
                .st-key-petal-{petal.number:02d} {{
                    animation: {anim_name} 600ms ease-out both;
                    animation-delay: {delay}ms;
                }}
                """
            )

    reduced = [
        """
        @media (prefers-reduced-motion: reduce) {
            .st-key-seed { animation: je-seed-settle-reduced 300ms ease-out both; }
            @keyframes je-seed-settle-reduced { from { opacity: 0.4; } to { opacity: 1; } }
        }
        """
    ]
    for petal in PETALS:
        reduced.append(
            f"""
            @media (prefers-reduced-motion: reduce) {{
                .st-key-petal-{petal.number:02d} {{
                    animation: je-fade-{petal.number:02d} 300ms ease-out both;
                }}
                @keyframes je-fade-{petal.number:02d} {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            }}
            """
        )

    return "<style>" + "\n".join(rules + reduced) + "</style>"


def render_landing_header() -> None:
    """Wordmark, app name, tagline. Call inside `st.container(key="landing")`
    so `.st-key-landing`'s CSS width constrains these plus the box below."""
    st.markdown(f'<div class="je-wordmark">{WORDMARK_TEXT}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="je-title">{APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="je-tagline">{APP_TAGLINE}</div>', unsafe_allow_html=True)
