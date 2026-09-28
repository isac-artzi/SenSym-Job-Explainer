"""SenSym Job Explainer — Streamlit entry point.

Layout and the State A / B / C machine only (PRD §8): an empty landing page
with one box and one button, a pulsing seed card while fourteen panels
generate, and a 3x5 bloom grid once they're in. All the real work — ingest,
the model calls, rendering — lives in job_explainer/.
"""

from __future__ import annotations

import html
import random
from pathlib import Path

import streamlit as st

from job_explainer import config, ingest, render, ui
from job_explainer.llm import LLMConfig, LLMError
from job_explainer.pipeline import PETALS, SEED_GRID_CELL, PetalResult, analyze_job, generate_petals, run_petal

APP_ROOT = Path(__file__).resolve().parent
LOCAL_ENV_PATH = APP_ROOT / "job_explainer.env"
EXAMPLES_DIR = APP_ROOT / "examples"


# --- session state -----------------------------------------------------


# Settings live under two names on purpose. `cfg_*` are the Settings popover
# widgets' own keys — but that popover is only instantiated in State A
# (PRD §8.1), and Streamlit garbage-collects a widget's session_state entry
# on any run where the widget isn't instantiated. Left as the only copy,
# the API key would vanish the moment generation finishes and State C
# renders, breaking a panel's "Try again" (F11). `llm_*` are plain,
# non-widget-bound keys that mirror them — set once here and re-synced after
# every `cfg_*` widget below — and every other part of the app reads those.
def _init_session_state() -> None:
    if "config_loaded" in st.session_state:
        return
    st.session_state["config_loaded"] = True

    loaded = config.load_env_file(LOCAL_ENV_PATH) or {}
    provider = loaded.get("LLM_PROVIDER", "anthropic")
    api_key = loaded.get("API_KEY", "")
    model = loaded.get("MODEL", "")
    ollama_url = loaded.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        parallel_calls = max(1, int(loaded.get("PARALLEL_CALLS", config.DEFAULT_PARALLEL_CALLS)))
    except ValueError:
        parallel_calls = int(config.DEFAULT_PARALLEL_CALLS)
    reading_level = loaded.get("READING_LEVEL", "")

    for prefix in ("cfg_", "llm_"):
        st.session_state[f"{prefix}provider"] = provider
        st.session_state[f"{prefix}api_key"] = api_key
        st.session_state[f"{prefix}model"] = model
        st.session_state[f"{prefix}ollama_url"] = ollama_url
        st.session_state[f"{prefix}parallel_calls"] = parallel_calls
        st.session_state[f"{prefix}reading_level"] = reading_level


def _start_over() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# --- config helpers ------------------------------------------------------


def _build_app_config() -> config.AppConfig:
    """Reads the `llm_*` canonical keys, not the Settings widgets' own `cfg_*`
    keys — see the note above `_init_session_state()`."""
    values = {
        "LLM_PROVIDER": st.session_state.get("llm_provider", "anthropic"),
        "API_KEY": st.session_state.get("llm_api_key", ""),
        "MODEL": st.session_state.get("llm_model", ""),
        "OLLAMA_BASE_URL": st.session_state.get("llm_ollama_url", "http://localhost:11434"),
        "PARALLEL_CALLS": str(st.session_state.get("llm_parallel_calls", config.DEFAULT_PARALLEL_CALLS)),
        "READING_LEVEL": st.session_state.get("llm_reading_level", ""),
    }
    return config.AppConfig(values=values)


def _build_llm_config(app_config: config.AppConfig) -> LLMConfig:
    return LLMConfig(
        provider=app_config.provider,
        api_key=app_config.api_key,
        model=app_config.model,
        ollama_base_url=app_config.ollama_base_url,
    )


def _generate_env_text() -> str:
    return config.generate_env_text(_build_app_config().values)


def _maybe_apply_uploaded_config(uploaded) -> None:
    """Parse an uploaded `job_explainer.env` into session state, once per file."""
    marker = f"{uploaded.name}:{uploaded.size}"
    if st.session_state.get("_last_upload_marker") == marker:
        return
    values = config.parse_env_text(uploaded.getvalue().decode("utf-8", errors="replace"))
    st.session_state["cfg_provider"] = values.get("LLM_PROVIDER", "anthropic")
    st.session_state["cfg_api_key"] = values.get("API_KEY", "")
    st.session_state["cfg_model"] = values.get("MODEL", "")
    st.session_state["cfg_ollama_url"] = values.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        st.session_state["cfg_parallel_calls"] = max(1, int(values.get("PARALLEL_CALLS", config.DEFAULT_PARALLEL_CALLS)))
    except ValueError:
        st.session_state["cfg_parallel_calls"] = int(config.DEFAULT_PARALLEL_CALLS)
    st.session_state["cfg_reading_level"] = values.get("READING_LEVEL", "")
    st.session_state["_last_upload_marker"] = marker


# --- small helpers ---------------------------------------------------------


def _pick_example() -> str:
    files = sorted(EXAMPLES_DIR.glob("*.txt"))
    return random.choice(files).read_text(encoding="utf-8") if files else ""


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:70] + ("…" if len(line) > 70 else "")
    return ""


def _meta_line(analysis: dict) -> str:
    company = analysis.get("company")
    return company if company and str(company).strip().lower() not in ("", "not stated") else ""


# (analysis key, icon, st.badge color) for the seed card's small tag row —
# only shown when the posting actually said something for that field, per
# the honesty rule against filling in what a posting left vague.
_SEED_BADGE_FIELDS = [
    ("seniority", "work", "blue"),
    ("work_arrangement", "home_work", "green"),
    ("location", "place", "violet"),
]


def _render_seed_badges(analysis: dict) -> None:
    fields = [
        (analysis.get(key), icon, color)
        for key, icon, color in _SEED_BADGE_FIELDS
        if analysis.get(key) and str(analysis[key]).strip().lower() not in ("", "not stated")
    ]
    if not fields:
        return
    cols = st.columns(len(fields))
    for col, (value, icon, color) in zip(cols, fields):
        with col:
            st.badge(str(value), icon=f":material/{icon}:", color=color)


# --- Settings popover (State A only, per PRD §8.1) ------------------------


def _render_settings_popover() -> None:
    _, right = st.columns([6, 1])
    with right:
        with st.popover("Settings", icon=":material/tune:", use_container_width=True):
            uploaded = st.file_uploader(
                "Upload a saved config", type=["env"], help=ui.TOOLTIPS["config_upload"], key="cfg_upload"
            )
            if uploaded is not None:
                _maybe_apply_uploaded_config(uploaded)

            st.selectbox("Provider", config.PROVIDERS, key="cfg_provider", help=ui.TOOLTIPS["provider"])
            st.session_state["llm_provider"] = st.session_state["cfg_provider"]

            if st.session_state["cfg_provider"] == "ollama":
                st.text_input("Ollama base URL", key="cfg_ollama_url", help=ui.TOOLTIPS["ollama_url"])
                st.session_state["llm_ollama_url"] = st.session_state["cfg_ollama_url"]
            else:
                st.text_input("API key", key="cfg_api_key", type="password", help=ui.TOOLTIPS["api_key"])
                st.session_state["llm_api_key"] = st.session_state["cfg_api_key"]

            st.text_input("Model (optional)", key="cfg_model", help=ui.TOOLTIPS["model"])
            st.session_state["llm_model"] = st.session_state["cfg_model"]

            st.number_input(
                "Panels generated at once",
                min_value=1,
                max_value=14,
                step=1,
                key="cfg_parallel_calls",
                help=ui.TOOLTIPS["parallel_calls"],
            )
            st.session_state["llm_parallel_calls"] = st.session_state["cfg_parallel_calls"]

            st.text_input("Reading level (optional)", key="cfg_reading_level", help=ui.TOOLTIPS["reading_level"])
            st.session_state["llm_reading_level"] = st.session_state["cfg_reading_level"]

            st.divider()
            st.download_button(
                "Download this config",
                data=_generate_env_text(),
                file_name="job_explainer.env",
                mime="text/plain",
                icon=":material/download:",
                help=ui.TOOLTIPS["download_config"],
                key="download_cfg_btn",
                use_container_width=True,
            )


# --- State A: the seed ------------------------------------------------------


def _render_landing() -> None:
    _render_settings_popover()

    with st.container(key="landing"):
        ui.render_landing_header()

        if st.session_state.get("top_level_error"):
            st.warning(st.session_state.pop("top_level_error"))

        input_area = st.empty()
        with input_area.container():
            st.text_area(
                "Job posting",
                key="posting_input",
                height=280,
                placeholder="Paste the full job description, or a link to it…",
                label_visibility="collapsed",
            )

            button_col, privacy_col = st.columns([1, 2])
            with button_col:
                clicked = st.button(
                    "Explain this job",
                    type="primary",
                    icon=":material/bolt:",
                    use_container_width=True,
                    key="explain_btn",
                )
            with privacy_col:
                st.markdown(
                    f'<div class="je-privacy-inline">{html.escape(ui.PRIVACY_LINE)}</div>',
                    unsafe_allow_html=True,
                )
                # TODO(v1.1): cost estimate here, next to the privacy line
                # (job_explainer/cost.py is ready; just not wired into the UI yet).

            st.markdown('<div class="je-link-button">', unsafe_allow_html=True)
            # on_click, not a checked return value: by the time a plain
            # `if st.button(...):` branch runs, posting_input's text_area has
            # already been instantiated this script run, and Streamlit
            # forbids writing to a widget's session_state key after that.
            # on_click callbacks run first, before the rerun that
            # re-instantiates the widget.
            st.button(
                "Try an example",
                icon=":material/lightbulb:",
                key="try_example_btn",
                on_click=_apply_example,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        if clicked:
            _handle_explain_click(input_area)


def _apply_example() -> None:
    st.session_state["posting_input"] = _pick_example()


def _handle_explain_click(input_area) -> None:
    raw_text = st.session_state.get("posting_input", "")
    app_config = _build_app_config()

    problems = config.validate(app_config)
    if problems:
        st.warning("Add an API key in Settings (top right) before I can explain this job.")
        return

    result = ingest.ingest(raw_text)
    if result.error:
        st.warning(result.error)
        return

    posting_text = result.text
    llm_config = _build_llm_config(app_config)

    # State B: the text area is replaced in place by a pulsing seed card
    # whose status line updates as work happens (PRD §8.2).
    with input_area.container(key="seed", border=True):
        st.markdown(
            f'<div class="je-seed-title je-pulsing">{html.escape(_first_line(posting_text) or "This posting")}</div>',
            unsafe_allow_html=True,
        )
        status = st.empty()
    status.markdown('<div class="je-seed-status">Reading the posting…</div>', unsafe_allow_html=True)

    try:
        analysis = analyze_job(posting_text, llm_config)
    except LLMError as exc:
        st.session_state["top_level_error"] = str(exc)
        st.rerun()
        return

    status.markdown('<div class="je-seed-status">Growing 0 of 14 panels…</div>', unsafe_allow_html=True)
    progress = {"n": 0}

    def on_complete(_result: PetalResult) -> None:
        progress["n"] += 1
        status.markdown(
            f'<div class="je-seed-status">Growing {progress["n"]} of 14 panels…</div>',
            unsafe_allow_html=True,
        )

    results = generate_petals(
        posting_text,
        analysis,
        app_config.reading_level,
        llm_config,
        app_config.parallel_calls,
        on_complete=on_complete,
    )

    st.session_state["analysis"] = analysis
    st.session_state["petal_results"] = results
    st.session_state["posting_text"] = posting_text
    st.session_state["just_bloomed"] = True
    st.session_state["truncated_notice"] = result.truncated
    st.rerun()


# --- State C: the bloom ------------------------------------------------------


def _render_seed_card(analysis: dict, petal_results: dict[str, PetalResult]) -> None:
    with st.container(key="seed", border=True, height=ui.PETAL_CARD_HEIGHT):
        st.markdown(
            f'<div class="je-seed-title">{html.escape(analysis.get("title") or "This job")}</div>',
            unsafe_allow_html=True,
        )
        company = _meta_line(analysis)
        if company:
            st.badge(company, icon=f":material/{ui.SEED_ICON}:", color="primary")
        _render_seed_badges(analysis)

        document = render.render_report(analysis, petal_results)
        docx_bytes = render.build_docx_bytes(document)
        json_bytes = render.render_explanation_json(analysis, petal_results)

        st.download_button(
            "Download report (.docx)",
            data=docx_bytes,
            file_name=render.report_filename(analysis),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            icon=":material/description:",
            use_container_width=True,
            key="download_docx_btn",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.session_state.get("read_as_page"):
                label, icon = "Back to the bloom", "grid_view"
            else:
                label, icon = "Read as a page", "article"
            if st.button(label, icon=f":material/{icon}:", use_container_width=True, key="toggle_read_page"):
                st.session_state["read_as_page"] = not st.session_state.get("read_as_page", False)
                st.session_state["just_bloomed"] = False
                st.rerun()
        with col_b:
            if st.button(
                "Start over", icon=":material/restart_alt:", use_container_width=True, key="start_over_btn"
            ):
                _start_over()
                st.rerun()

        st.download_button(
            "Download data (.json)",
            data=json_bytes,
            file_name="explanation.json",
            mime="application/json",
            icon=":material/data_object:",
            use_container_width=True,
            key="download_json_btn",
        )


def _retry_petal(petal) -> None:
    analysis = st.session_state["analysis"]
    posting_text = st.session_state.get("posting_text", "")
    app_config = _build_app_config()
    llm_config = _build_llm_config(app_config)
    try:
        markdown = run_petal(petal, posting_text, analysis, app_config.reading_level, llm_config)
        st.session_state["petal_results"][petal.key] = PetalResult(petal=petal, markdown=markdown)
    except LLMError as exc:
        st.session_state["petal_results"][petal.key] = PetalResult(petal=petal, error=str(exc))
    st.session_state["just_bloomed"] = False
    st.rerun()


def _render_petal_card(petal, result: PetalResult | None) -> None:
    icon, badge_color = ui.petal_badge(petal.number)
    with st.container(key=f"petal-{petal.number:02d}", border=True, height=ui.PETAL_CARD_HEIGHT):
        st.badge(f"{petal.number:02d} · {petal.title}", icon=icon, color=badge_color)
        if result is None or result.error:
            message = result.error if result and result.error else "This panel wasn't generated."
            st.markdown(f'<div class="je-petal-error">{html.escape(message)}</div>', unsafe_allow_html=True)
            if st.button("Try again", icon=":material/refresh:", key=f"retry_{petal.key}"):
                _retry_petal(petal)
            # TODO(v1.1): Regenerate control on every panel, not just failed ones.
        else:
            st.markdown(result.markdown)


def _render_grid_view(analysis: dict, petal_results: dict[str, PetalResult]) -> None:
    grid = {p.grid_cell: p for p in PETALS}
    for row in range(ui.GRID_ROWS):
        cols = st.columns(ui.GRID_COLS)
        for col in range(ui.GRID_COLS):
            with cols[col]:
                if (row, col) == SEED_GRID_CELL:
                    _render_seed_card(analysis, petal_results)
                else:
                    petal = grid.get((row, col))
                    if petal is not None:
                        _render_petal_card(petal, petal_results.get(petal.key))


def _render_page_view(analysis: dict, petal_results: dict[str, PetalResult]) -> None:
    with st.container(key="page-view"):
        st.markdown(
            f'<div class="je-title">{html.escape(analysis.get("title") or "This job")}</div>',
            unsafe_allow_html=True,
        )
        company = _meta_line(analysis)
        if company:
            st.badge(company, icon=f":material/{ui.SEED_ICON}:", color="primary")
        _render_seed_badges(analysis)

        document = render.render_report(analysis, petal_results)
        docx_bytes = render.build_docx_bytes(document)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button(
                "Download report (.docx)",
                data=docx_bytes,
                file_name=render.report_filename(analysis),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                icon=":material/description:",
                use_container_width=True,
                key="download_docx_btn_page",
            )
        with col_b:
            if st.button(
                "Back to the bloom",
                icon=":material/grid_view:",
                use_container_width=True,
                key="toggle_read_page_2",
            ):
                st.session_state["read_as_page"] = False
                st.rerun()
        with col_c:
            if st.button(
                "Start over", icon=":material/restart_alt:", use_container_width=True, key="start_over_btn_2"
            ):
                _start_over()
                st.rerun()

        st.divider()

        for petal in PETALS:
            result = petal_results.get(petal.key)
            icon, badge_color = ui.petal_badge(petal.number)
            st.badge(f"{petal.number:02d} · {petal.title}", icon=icon, color=badge_color)
            if result is None or result.error:
                message = result.error if result and result.error else "This panel wasn't generated."
                st.markdown(f"*{message}*")
            else:
                st.markdown(result.markdown)
            st.divider()


def _render_bloom() -> None:
    analysis = st.session_state["analysis"]
    petal_results = st.session_state["petal_results"]
    just_bloomed = st.session_state.get("just_bloomed", False)

    if just_bloomed:
        st.markdown(ui.bloom_css(), unsafe_allow_html=True)

    if st.session_state.pop("truncated_notice", False):
        st.info("This posting was long, so it was trimmed to the first 15,000 characters.")

    if st.session_state.get("read_as_page"):
        _render_page_view(analysis, petal_results)
    else:
        _render_grid_view(analysis, petal_results)

    # The reveal plays once: this flag is only ever True on the single render
    # right after generation completes, and is cleared here so every later
    # interaction (scrolling, a button click) renders the grid statically.
    st.session_state["just_bloomed"] = False


# --- entry point ---------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title=ui.APP_NAME, layout="centered")
    ui.inject_base_css()
    _init_session_state()

    has_results = st.session_state.get("analysis") is not None and st.session_state.get("petal_results") is not None
    if has_results:
        _render_bloom()
    else:
        _render_landing()


main()
