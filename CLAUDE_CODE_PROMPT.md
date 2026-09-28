# Kickoff prompt for Claude Code

Paste everything below the line into Claude Code in VS Code, from inside the `SenSym-Job-Explainer` folder. The sibling repo `SenSym-resume-match` should be checked out next to it.

---

Build the SenSym Job Explainer app described in `PRD.md`. Read `PRD.md` and `CLAUDE.md` fully before writing any code — they are the spec and the house rules, and I will not repeat them here. Also skim `../SenSym-resume-match/` — you will port several modules from it rather than write them again.

**Scope for this session: the demo build in PRD §14.** Working and elegant beats complete. In priority order:

1. Repo scaffold: MIT `LICENSE`, `.gitignore` (include `job_explainer.env`, `__pycache__`, `.venv`), `requirements.txt`, `.streamlit/config.toml` with usage stats off and the same light theme as Resume Match, `job_explainer.env.example`.
2. `job_explainer/llm.py`, `config.py`, `cost.py`: port from `../SenSym-resume-match/resume_match/`, trim what the PRD doesn't need (vision, folder fields, Drive), rename `resume_match.env` → `job_explainer.env`, add `PARALLEL_CALLS` and `READING_LEVEL`. Recheck and pin current default model IDs.
3. `job_explainer/ingest.py`: text-or-URL detection, fetch with `requests` + `beautifulsoup4`, the 400-character sanity check, the 15,000-character cap, the one-line fallback message.
4. `prompts/job_analysis.txt` and the fourteen `prompts/petals/NN_slug.txt` files, each carrying the honesty rules from PRD §7 step 4 verbatim. Then `job_explainer/pipeline.py` with the `PETALS` list (number, slug, title, ring, grid_cell), the analysis call, and parallel panel generation with `ThreadPoolExecutor` and per-panel error isolation.
5. `job_explainer/ui.py` and `app.py`: the A/B/C state machine from PRD §8 — the empty landing page, the pulsing seed card with a live count, and the 3 × 5 bloom grid with the CSS reveal (rings staggered, transforms pointing away from the center cell, plays once via a `just_bloomed` flag, reduced-motion respected). Seed card actions: Download report, Read as a page, Start over. Settings in a popover (or expander if popover feels wrong). "Try an example."
6. `job_explainer/render.py`: panels dict → one DOCX in the Resume Match style (port `docx_style.py` helpers) plus `explanation.json`. Markdown subset only: `###` headings, bullets, numbered lists, bold, italic, pipe tables.
7. `examples/`: three fictional postings as `.txt` — one entry-level technical role, one non-technical role, one senior or unusual role — so the bloom is interesting for each. Fictional companies only.
8. `README.md` (both run modes, Ollama, why URL fetching often fails and what to do, privacy, key hygiene) and `EXTENDING.md` (expand PRD §15 into invitations with the module each touches and a rough difficulty; the first entry should be the step-by-step recipe for adding a fifteenth panel).

**Defer to v1.1 unless you finish early:** per-panel Regenerate, the cost line. Leave a clear `# TODO(v1.1)` where each would go.

**How to work.** Plan briefly, then build in the order above, committing after each numbered step. Run the app with the `examples/` postings as you go and fix what you see; do not wait until the end. Spend real time on step 5 — the bloom is the point of this app, and I will show it to a room of students. Use my Anthropic key from the environment variable `ANTHROPIC_API_KEY` for testing — never write it into any file. If a design decision is not covered by the PRD, make the simpler choice and list it in your final summary rather than stopping to ask; only ask me if you are blocked. Reuse Resume Match's palette and text wordmark.

**Definition of done.** From a fresh clone: `pip install -r requirements.txt`, `streamlit run app.py`, click "Try an example," click "Explain this job," and within about 45 seconds fourteen panels bloom from the center of the page, none of them containing a URL, a named person, or a salary figure the posting didn't supply. The DOCX opens in Word. The landing page has nothing on it but the box and the button. It should look like something a designer made, not a default Streamlit app.

When finished, give me: the commit log, the list of decisions you made beyond the PRD, anything deferred, and the exact commands to run the demo.
