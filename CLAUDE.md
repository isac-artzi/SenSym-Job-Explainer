# SenSym Job Explainer — project instructions for Claude Code

Read `PRD.md` before doing anything. It is the source of truth for scope, behavior, and UI. If the PRD and this file disagree, the PRD wins; if something is missing from both, choose the simplest option and note it in your summary.

## What this is

A free, open-source Streamlit app: paste a job posting (or a URL), click one button, and fourteen explanatory panels "bloom" around it — what the job is, skills and where to get them, what the company really wants, how to find the people who do it, the path, the outlook, what it becomes, and more. One DOCX report to download. No database, nothing stored, student brings their own AI key. Runs locally or on Streamlit Community Cloud from the same code.

## Sibling project

`../SenSym-resume-match` (public: https://github.com/isac-artzi/SenSym-Resume-Match) uses the same conventions. **Port, don't rewrite:** `resume_match/llm.py`, `config.py`, `cost.py`, and the DOCX styling in `docx_style.py` should be copied into `job_explainer/` and trimmed (no vision, no folder fields). Keep the docstrings — students read both repos. Match its brand tokens in `ui.py` so the two apps look like siblings.

## Non-negotiables

- **Honesty in every prompt.** No invented URLs (name the resource, don't link it), no named individuals, no salary figures unless the posting states them, no made-up statistics. Facts from the posting are stated as facts; everything else is labeled as inference or judgment in the panel's own words. Do not weaken these rules to make output "richer."
- **Store nothing.** No server-side writes except a `tempfile` for DOCX assembly if needed, deleted at once. API keys live only in `st.session_state`. No `st.cache_data` / `st.cache_resource` on user content. `gatherUsageStats = false`.
- **Keep it simple.** Modules under ~300 lines, functions over classes, no tests, no Docker, no CI, no custom Streamlit component, no Node. Prompts are plain-text files in `prompts/`, never Python strings. Adding a panel must be one prompt file plus one tuple in `PETALS`.
- **No system binaries.** `pip install -r requirements.txt` is the only setup step on macOS, Windows, and Linux.
- **The bloom is the product.** State A (one box, one button, nothing else) → State B (seed card pulsing with a panel count) → State C (3 × 5 grid, seed in the center, CSS reveal from the center outward, once). Pure Streamlit + CSS keyframes on `st.container(key=…)` classes. Light only, Notion-style, no emoji, Streamlit chrome hidden. All brand tokens in `job_explainer/ui.py`.

## Layout

```
app.py                       Streamlit entry point — layout and the A/B/C state machine only
job_explainer/config.py      load / validate / generate job_explainer.env
job_explainer/ingest.py      text-or-URL detection, fetch, clean, truncate
job_explainer/llm.py         complete() and complete_json() over anthropic | openai | gemini | ollama
job_explainer/pipeline.py    PETALS list, job analysis, parallel panel generation
job_explainer/render.py      panels dict → DOCX report + explanation.json
job_explainer/cost.py        rough cost estimate
job_explainer/ui.py          brand tokens, CSS incl. bloom keyframes, seed card and petal card helpers
prompts/job_analysis.txt
prompts/petals/NN_slug.txt   one file per panel, numbered 01–14 in bloom order
examples/                    three fictional sample postings as .txt
```

## Conventions

- Python 3.11+. Type hints on public functions. Docstrings that a student can learn from — say *why*, not just what.
- Provider differences stay inside `llm.py`. Default model IDs pinned in one dict there; check each provider's current docs before pinning.
- Ollama through its OpenAI-compatible endpoint using the `openai` client with `base_url`.
- Worker threads call only `llm.complete()` and return strings. No Streamlit calls off the main thread.
- Panel prompts return Markdown limited to: `###` headings, bullets, numbered lists, bold, italic, pipe tables. `render.py` handles exactly that subset and nothing more.
- Errors surface as friendly `st.error` or in-card messages, never tracebacks. Malformed JSON from the model → one automatic retry, then a clear message. A failed panel never fails the run.
- Commit small and often with clear messages. Never commit `job_explainer.env` (in `.gitignore`); commit `job_explainer.env.example` instead.
- Never use a real API key in examples, docs, or commits.

## GitHub public repo

https://github.com/isac-artzi/SenSym-Job-Explainer

## Verifying your work

Run `streamlit run app.py` and exercise the full flow with each posting in `examples/`. Check that: State A shows nothing but the wordmark, tagline, box, button, and the two muted links; State B shows the pulsing seed card and a live panel count; State C lays out the 3 × 5 grid with the seed card in the exact center and the reveal plays from the center outward exactly once (scroll a card, click Regenerate — it must not replay); "Read as a page" and back both work; the DOCX opens cleanly in Word and round-trips through `python-docx`; a URL to a site that blocks fetching produces the one-line fallback, not an error banner; no panel contains a URL, a named person, or a salary figure that the posting didn't supply; "Start over" clears session state including the key; the page looks calm at 1024 px and reads well on a projector.
