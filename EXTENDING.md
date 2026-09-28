# Extending SenSym Job Explainer

This app is a teaching artifact as much as a tool — every module is short
enough to read in one sitting, and the ideas below are starting points, not
a roadmap anyone owns. Pick one, read the module it touches, and go. Pull
requests welcome.

A few things worth knowing before you start:

- **Prompts are plain text**, in `prompts/`. You can change how the app
  writes without touching a line of Python.
- **The LLM client is two functions**: `complete()` and `complete_json()`
  in `job_explainer/llm.py`. Any new provider-specific behavior goes there;
  everything else in the app should stay provider-agnostic.
- **The honesty rules are the whole point of this app.** If your change
  touches a prompt in `prompts/petals/`, keep the "Rules:" block — no
  invented URLs, no named individuals, no unsupported salary figures, facts
  vs. labeled inference — verbatim, and test your change against a posting
  that's vague or sparse, not just a detailed one. A model under-informed
  by a thin posting is exactly when it's most tempted to invent.

## Add a fifteenth panel (the recipe every other panel followed)

*Touches `prompts/petals/`, `job_explainer/pipeline.py`, possibly
`job_explainer/ui.py` · easy.* This is deliberately a one-file-plus-one-line
change (PRD §13):

1. **Write the prompt.** Copy the shape of an existing panel closest to
   what you want — a table (`02_skills.txt`), a numbered list
   (`08_the_path.txt`), or plain prose (`01_what_it_is.txt`) — into a new
   file `prompts/petals/15_your_slug.txt`. Keep three things intact: the
   `$job_text` / `$analysis_json` preamble, a clear `SHAPE:` instruction
   naming exactly the Markdown you want back (so `render.py`'s converter
   can handle it — see below), and the `Rules:` honesty block, copied
   verbatim from any other panel.
2. **Register it.** In `job_explainer/pipeline.py`, add one `Petal(...)` to
   the `PETALS` list: a number (15), a slug matching your filename, a
   title, a ring (1-3, or a new outer ring — see below), and a
   `grid_cell`.
3. **Find it a home in the grid.** The demo build's 5x3 grid (PRD §8.3) is
   exactly full: 14 petals plus the seed. Adding a fifteenth means either
   widening the grid or accepting an asymmetric layout. The simplest option
   is a new ring 4 row: bump `GRID_ROWS` in `job_explainer/ui.py` from 5 to
   6, and give your panel a `grid_cell` in the new row (e.g. `(5, 1)`). The
   seed card is no longer at the exact vertical center once you do this —
   a reasonable tradeoff for a fifteenth panel, and a good prompt to think
   about whether the grid should become responsive instead of fixed.
4. **That's it.** `job_explainer/render.py`'s DOCX builder and `app.py`'s
   grid and "Read as a page" view all iterate `PETALS`, so a new entry
   there is picked up everywhere automatically — no other code changes
   needed. Run `streamlit run app.py`, try an example, and check your panel
   renders in both the grid and the DOCX.

## Ideas, roughly easiest to hardest

**An optional "about you" line** — *touches `prompts/`,
`job_explainer/pipeline.py`, `app.py` · easy-medium.* A single optional
field (a target role, a self-described background) threaded into the
`skills`, `experience`, `find_the_people`, and `the_path` prompts so those
panels personalize instead of staying generic. Show a small diff view (old
panel vs. new) when the student adds this after already generating a
bloom, so it's clear what changed and why. Keep the honesty rules
unchanged — personalizing must not become an excuse to invent.

**Compare mode** — *touches `app.py`, `job_explainer/pipeline.py`,
`job_explainer/ui.py` · medium.* Two postings side by side, their panels
aligned by number, with the differences between them highlighted (same
requirement worded differently vs. a genuinely different requirement).
The interesting design problem is the layout: two 3x5 grids don't fit
side by side at any reasonable width, so this probably wants "Read as a
page" as its base rather than the bloom grid.

**Save to the student's own Google Drive or Notion** — *new module, touches
`app.py` · medium.* Push the finished DOCX and `explanation.json` to a
destination the student authenticates to themselves (their credentials,
their storage) instead of only offering a local download. Start read-only
(just the upload), and keep the "store nothing server-side" privacy rule
intact — the app should never hold the student's Drive/Notion token beyond
the session.

**A skills constellation** — *new module, likely touches `app.py` and adds
a small viz dependency · medium.* If a student explains more than one
posting in a session (today, "Start over" clears everything — this would
need to relax that), plot the skills mentioned across all of them as a
graph, with edges for postings that share a skill. A good second project
after "Compare mode," since both want to keep more than one explained
posting around at once.

**Voice mode** — *touches `job_explainer/llm.py`, `app.py` · medium-hard.*
Read a panel aloud (text-to-speech), or let the student ask a follow-up
question about a specific panel and get a spoken or written answer. A
follow-up answer must obey the same honesty rules as the panel it's
following up on — it's tempting to treat a conversational follow-up as
exempt, and it shouldn't be.

**A real bloom** — *new module (a custom Streamlit component with a Node
build step) · hard.* Replace the CSS reveal with a component that lays
panels out with real force-directed physics instead of fixed grid cells —
this is explicitly out of scope for the demo build (PRD non-goals rule out
a Node build step for v1), so treat this as a genuine "next version"
project, not a small patch.

**Small-model mode** — *touches `prompts/`, `job_explainer/llm.py` · hard.*
Get the full pipeline producing acceptable panels on an 8B-class Ollama
model. The interesting problem isn't speed — it's that smaller models are
more prone to inventing a URL or a name when the posting is thin on
detail, so this is really about prompt engineering the honesty rules to
hold under a weaker model, plus a scorer (see below) to prove it does.

**Classroom mode** — *new module, needs a small server component · hard.*
An instructor pastes one posting; students see the same bloom appear on
their own devices via a share code. This is a genuine systems project (the
app currently has no server-side state at all, by design) — a good one for
a student who wants backend experience beyond this repo's scope.

**Evaluation harness** — *new module or `scripts/` directory · hard.* A set
of postings (thin ones especially — see "Small-model mode") run through
the pipeline automatically, with a rubric-based scorer that flags invented
URLs, names, or figures without a human reading every panel. This is what
would let a prompt change to `prompts/petals/` be measured instead of
eyeballed — genuinely useful before merging any change to the honesty
rules, and a reasonable prerequisite for "Small-model mode" above.
