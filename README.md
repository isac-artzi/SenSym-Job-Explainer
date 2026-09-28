# SenSym™ Job Explainer

A free, open-source Streamlit app that turns a job posting into an
explanation you can act on. Paste a posting — or a link to one — into a
single box, click one button, and fourteen short panels bloom outward from
it: what the job actually is, the skills it takes and where you'd pick them
up, what the company is really looking for, how to find the people who do
this work, the path in, where it's headed, what it becomes, and more. One
report downloads as a DOCX you can open and edit in Word.

This app is provided free of charge by **SenSym™** ([sensym.ai](https://sensym.ai))
as a tool for students and early-career job seekers. There's no catch and no
paywall in the app itself — you only ever pay your own AI provider directly
for the model calls the app makes on your behalf (see "Getting an API key"
below); SenSym never charges for the app and never sees your API key or
anything you paste into it.

**The guiding rule for every panel: say what the posting supports, and
label the rest as judgment.** Facts drawn from the posting are stated as
facts. Everything else — inference about tone, a forecast about where the
role is headed, a guess at what's missing — is labeled as such, in the
panel's own words. No panel invents a URL (it names the resource instead),
a named individual, a salary figure the posting didn't give, or a
statistic.

The app stores nothing — no database, no accounts, no logging of what you
paste. You bring your own AI key (Anthropic, OpenAI, Gemini, or a local
Ollama model) and pay your own model costs, typically a few cents per
posting.

## Runs locally or on Streamlit Community Cloud — your choice

This is the same app, the same repo, and the same code either way. Run it
on your own computer for full control (a local Ollama model, nothing ever
leaves your machine except calls to your chosen AI provider), or deploy it
to Streamlit Community Cloud for zero-setup access from any browser. The
only difference is whether Ollama is reachable — everything else, including
the config form, works identically in both places.

| | Local | Streamlit Community Cloud |
|---|---|---|
| Setup | `git clone`, `pip install`, `streamlit run app.py` | Deploy this repo from [share.streamlit.io](https://share.streamlit.io) |
| Config | `job_explainer.env` at the repo root loads automatically if present, or use the in-app form | In-app form or upload; held in session memory only |
| Local models (Ollama) | Supported | Not reachable from the cloud |
| Output | DOCX download | DOCX download |

## Quick start (local)

Works the same way on macOS, Windows, and Linux — Python and a browser are
the only requirements.

<details>
<summary><strong>macOS</strong></summary>

Needs Python 3.11+. Check with `python3 --version`; if you don't have it,
install it from [python.org](https://www.python.org/downloads/macos/) or via
Homebrew (`brew install python@3.12`).

```bash
git clone https://github.com/isac-artzi/SenSym-Job-Explainer.git
cd SenSym-Job-Explainer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

</details>

<details>
<summary><strong>Windows</strong></summary>

Needs Python 3.11+. Install it from
[python.org](https://www.python.org/downloads/windows/) — check "Add
python.exe to PATH" during install — or from the Microsoft Store. Check with
`python --version` in PowerShell.

```powershell
git clone https://github.com/isac-artzi/SenSym-Job-Explainer.git
cd SenSym-Job-Explainer
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks the activation script with an "execution policy"
error, run this once first (for the current session only, nothing
permanent): `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
Using Command Prompt instead of PowerShell? Activate with
`.venv\Scripts\activate.bat` instead of the `.ps1` line above.

</details>

<details>
<summary><strong>Linux</strong></summary>

Needs Python 3.11+ and the matching `venv` package. Most distributions ship
Python 3, but you may need the venv module separately, e.g. on
Debian/Ubuntu: `sudo apt install python3-venv`.

```bash
git clone https://github.com/isac-artzi/SenSym-Job-Explainer.git
cd SenSym-Job-Explainer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

</details>

Whichever platform you're on, `streamlit run app.py` opens the app in your
default browser at `http://localhost:8501`. Leave the terminal window open
while you use the app; closing it stops the app. Next time, you don't need
to recreate the virtual environment — just `cd` into the folder, re-activate
it, and run `streamlit run app.py` again.

Then, in the app:

1. Click **Settings** (top right) and pick a provider and paste your API
   key — or upload a `job_explainer.env` file if you have one saved from
   before.
2. Paste a job posting into the box, or a URL to one.
3. Click **Explain this job** and watch the bloom. This takes about 20-45
   seconds on a hosted model.
4. Open a panel, toggle **Read as a page** to view everything in order, and
   **Download report (.docx)** when you're happy with it.

Want to try it before you have a posting handy? Click **Try an example**
under the box — it fills the box with one of the fictional postings in
[`examples/`](examples/).

## Quick start (cloud)

No install, no clone, no terminal — just a browser, once you (or whoever
runs the class) have deployed this repo to Streamlit Community Cloud from
[share.streamlit.io](https://share.streamlit.io) (point it at this repo and
`app.py`; no secrets to configure, since every student brings their own
key).

1. Open the deployed app's URL.
2. Click **Settings** and paste your API key.
3. Paste a posting (or a link) and click **Explain this job**.
4. Download the report when you're done.

Nothing you paste touches the server's disk in cloud mode — see "Privacy"
below.

## Getting an API key

The app defaults to **Anthropic** (Claude). Get a key at
[console.anthropic.com](https://console.anthropic.com). OpenAI, Gemini, and
a local [Ollama](https://ollama.com) install are also supported — pick your
provider in Settings.

**Because you're pasting a key into a web app (especially the hosted cloud
version), create a dedicated key with a spending limit if your provider
supports one, and rotate it (delete the old one, make a new one) once
you're done using the app for the day.** The app never writes your key to
disk and holds it only in your browser session, but a key that leaves your
machine at all is safer treated as temporary.

### Using Ollama (local models, no API key)

Ollama installs on macOS, Windows, and Linux and lets you run the app
entirely on your own machine, with no API key and no per-use cost — you
trade that for slower generation and, on smaller models, a higher chance of
instruction-following mistakes (a panel that drifts off the requested
shape, or forgets a honesty rule).

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull a model: `ollama pull llama3.1` (or any model you prefer).
3. In Settings, choose provider "ollama." No API key is needed.
4. Set **Panels generated at once** to 1 — most Ollama setups can't run
   several requests in parallel.
5. Ollama only works when the app is running **locally** — Streamlit
   Community Cloud can't reach a model on your own machine.

## Why URL fetching often fails, and what to do

Paste a link instead of pasted text, and the app tries to fetch and read
it. Many job sites (LinkedIn, Workday, Greenhouse behind a login, most of
Indeed) either block scraping outright or serve a JavaScript shell with no
readable text in the initial response — the app can't tell those apart from
a network error, so either way you'll see one line: *"That site didn't let
me read the posting. Paste the text instead."*

When that happens: open the posting in your browser, select all the text,
and paste it into the box instead. This always works, since the app never
has to guess at what a script rendered.

## Privacy

- **Nothing is stored.** No database, no server-side writes (a `tempfile`
  is used only transiently for DOCX assembly, if at all, and never
  persists). `gatherUsageStats = false`.
- Your API key lives in the browser session only — never logged, never
  written to disk by the app, cleared when you click **Start over** or
  close the tab.
- No analytics, no third-party scripts, no usage tracking.
- The only network calls the app makes are to the AI provider you chose,
  and to a URL if you paste one instead of text.
- The app itself stores nothing, but **your chosen model provider
  processes the text you send it** (the posting, plus the model's own
  analysis of it). Read your provider's data-handling policy if that
  matters for your situation.

## Configuration reference

Copy `job_explainer.env.example` to `job_explainer.env` and edit it, or use
the in-app Settings form (fill it in, then **Download this config**). A
`job_explainer.env` placed at the repo root is loaded automatically the
next time you run the app locally.

```
LLM_PROVIDER=anthropic          # anthropic | openai | gemini | ollama
API_KEY=                        # leave blank for ollama
MODEL=                          # optional; provider default used if blank
OLLAMA_BASE_URL=http://localhost:11434   # ollama only

PARALLEL_CALLS=4                # panels generated at once; use 1 for ollama
READING_LEVEL=                  # e.g. "first-year undergraduate" (default) or "high school"
```

`job_explainer.env` is in `.gitignore` — never commit your real config or
your key.

## What you get

- `job_explainer_<title>-<company>.docx` — the full report: a posting
  summary, then all fourteen panels as numbered sections. Opens cleanly in
  Word and is meant to be a strong starting point, not a finished,
  un-reviewable artifact.
- `explanation.json` — the same content as structured data (the job
  analysis plus every panel's Markdown), for anyone who wants to build on
  it without calling a model again.

## Troubleshooting

- **"Add an API key in Settings"** — pick a provider other than Ollama and
  paste a key, or switch to Ollama.
- **A panel shows an error instead of content** — one call failing never
  fails the whole bloom; click **Try again** on that panel's card.
- **A link didn't fetch** — paste the posting's text instead (see above).
- **The model returned something that couldn't be parsed** — the job
  analysis step retries automatically once; if it still fails, try again or
  switch models in Settings.
- **A very long posting got cut off** — postings are capped at about
  15,000 characters, with a notice when that happens. Trim it to the
  parts that matter (the role description and requirements) and try again.

## License

MIT — see `LICENSE`. This is a teaching artifact as much as a tool; see
[`EXTENDING.md`](EXTENDING.md) if you want to build on it. The code is
open source under MIT; "SenSym" and the SenSym™ name and branding are
trademarks of SenSym LLC and aren't covered by the code license — fork and
extend the app freely, just don't reuse the SenSym name/branding for a
different or competing product.
