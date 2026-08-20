# Cost and resource awareness — group MaRs-777 (POLICE)

**Status: CURRENT.** Last measured at Stage 9A-1A.

Every number here was measured on this repository. Nothing is estimated,
extrapolated, or converted into money — a latency figure is not a price, and
this project has no metered spend to price.

## 1. LLM / model tokens — measured zero

| Path | Provider calls | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| Hint generation (`TemplateHintPolicy`) | **0** | **0** | **0** | **0** |
| Strategy (`BaselineStrategy`, `CompetitiveStrategy`) | **0** | **0** | **0** | **0** |
| Scent belief interpretation | **0** | **0** | **0** | **0** |
| Every other runtime path | **0** | **0** | **0** | **0** |

This is a structural zero, not a small number. The shipped natural-language
channel is a **deterministic template catalogue**: a truthful pre-written
sentence is selected by code, validated (Unicode NFC, word count against the
negotiated `hint_max_words`, refusal of direct coordinate syntax) and sealed.
There is no model, no provider client and no network call anywhere on that path,
and `docs/architecture/LLM_BOUNDARY.md` is the architectural statement of it.

`TokenAccountingPort` exists and reports the consumption in the completion
document (`PERF-001`); with the T0 path it reports `0`, which is the truth
rather than an omission. The negotiated `token_budget_per_series` is therefore
never approached.

**If an optional LLM path is ever enabled**, this table becomes a real
per-model input/output/cost breakdown, and the guideline's §11 budget-monitoring
requirements start to apply. Today they do not, and marking them "done" would be
dishonest.

## 2. Compute — local CPU only

Strategy, cryptography, canonicalisation and the whole game engine run in the
local process. No GPU, no accelerator, no external compute service.

| Operation | Measured |
|---|---|
| Wire decode | **3.1 µs** per turn |
| Wire encode | **0.3 µs** per turn |
| Direct call to a role backend | **6.4 ms** median over 200 calls |
| Call through the group gateway | **14.2 ms** median over 200 calls |
| **Gateway hop overhead** | **≈ 7.8 ms** |

The overhead is recorded and deliberately **not** optimised. The negotiated
watchdog default is 60 s (Appendix F, NEGOTIABLE) and the kit series measurement
was taken against a 180 s per-turn budget; 7.8 ms is roughly 0.004% of the
latter. Optimising it would be premature, and the note in
`docs/architecture/API_BOUNDARIES.md` says so at the measurement.

## 3. Memory

| Process | Measured |
|---|---|
| Group gateway | **≈ 80 MB peak RSS** |

The gateway is the process a real match adds, so it is the one worth stating.
Backend agent processes were not separately profiled; that measurement is
missing rather than assumed.

## 4. Disk

| Item | Measured |
|---|---|
| Virtual environment (`.venv`) | **167 MB** |
| Repository history (`.git`) | **18 MB** |
| Tracked files | **716** |
| Artifacts written by one complete series | **14 files** |
| Current `artifacts/` tree | **12 KB** |

Official artifacts are small: they are canonical JSON documents and digests, not
recordings. Development evidence from friendly runs is written under its own
`friendly_` names and is likewise a few KB.

## 5. Continuous integration

| Item | Measured |
|---|---|
| Full local suite | **232 s** (`uv run pytest`, this repository) |
| Wall-clock per push | **≈ 9–11 minutes** (measured across the five most recent runs) |
| Jobs per push | Ubuntu quality job, Windows quality job, and one isolated Windows known-limitation job |
| Runner cost | **0** — GitHub-hosted minutes on the account's own plan |

One operational cost is worth recording because it actually happened: at Stage
8A-2G both repositories showed a three-second CI failure that was **not** a code
failure — the account had been blocked for a billing reason. The lesson is
recorded in `docs/AI_WORKFLOW.md`: a red CI badge is not automatically a red
codebase.

## 6. Network and third-party services

Since Stage 9A-1C every call to an external provider passes through one
Gatekeeper with a versioned local policy, so the rate at which this project can
spend somebody else's quota is bounded in one place and recorded per call.

| Service | Plan | Cost to this project |
|---|---|---|
| `ngrok` tunnel | the **operator's own** account | none incurred by this repository; one ephemeral HTTP tunnel per match is within the free tier |
| GitHub | private repositories on the account's plan | none beyond the account plan |
| Interoperability kit | public repository, read at a pinned commit | none; never vendored, never modified |

The tunnel credential belongs to the operator and is never read by this project,
so there is no credential-bearing cost surface in the codebase at all.

## 7. Human and AI development effort

Recorded qualitatively on purpose. The stage-by-stage history is in
`docs/PLAN.md`, the method and its corrections in `docs/AI_WORKFLOW.md`, and the
prompt log in `docs/PROMPTS.md`. Development was AI-assisted under human
supervision; assistant token consumption is a property of the development
sessions, not of this software, and is not metered by anything this repository
controls. It is therefore **not reported here rather than estimated**.

## 8. Continuous integration as a measured resource

CI runs are **intentionally minimised**: full verification happens locally
before each push, and the hosted runners are reserved for independent
confirmation of a change that has already passed every gate on a developer
machine. Nothing about the gates themselves is reduced to achieve that - the
same lint, format, strict typing, file-size, full-suite and 100%-coverage checks
run in both places, on Ubuntu and on Windows.

Practically this means: no speculative push, no "let us see what CI says", no
empty commit to retrigger a workflow, and no manual re-run of a workflow that is
already green. Platform-specific behaviour is rehearsed locally first - the
Stage-9A-2B lesson, where a toolkit was verified against the wrong interpreter
and cost a whole gating run.

## 9. Optimisation strategies actually applied

- **Zero-token by design.** The hint channel is deterministic, so the largest
  potential recurring cost in a project of this shape simply does not exist.
- **No re-resolution.** `uv sync --frozen` against a committed `uv.lock` keeps
  installs reproducible and avoids repeated dependency resolution in CI.
- **Measure before optimising.** The gateway hop was measured, found to be four
  thousandths of a percent of the turn budget, and left alone.
- **Small artifacts.** Canonical documents and digests, never recordings.
- **The research laboratory added no dependency either.** Figures are drawn with
  the deterministic renderer the GUI stage already ships, so there is no
  `matplotlib`, no `numpy`, no `pandas` and no Jupyter in the runtime or in CI.
  A benchmark sweep is pure CPU: **6,048 games per role in ~12 minutes** on one
  developer core, ~0.12 s per game, peak memory in the tens of megabytes, and
  about 2 MB of committed result rows, tables and figures per repository.
  Benchmarks never run on GitHub Actions.
- **Reporting is one provider call per game.** A completed game produces exactly
  one report: one OAuth refresh and one `users.messages.send`, both inside the
  Gatekeeper. There is no polling, no batching and no periodic re-send, so the
  steady-state provider cost of this project is bounded by the number of games
  played. LLM tokens remain **zero**: nothing in the reporting path calls a
  model.
- **The Gmail path added no dependency.** It speaks the provider's REST API over
  the standard library, so there is nothing extra to resolve, download or
  install - which also means no measurable change to environment setup time.
- **The graphical interface costs the game nothing.** Publishing a turn to a
  window is one assignment into a one-slot box; drawing happens on the
  viewer's own timer, in the viewer's own thread, and a viewer that is slow
  misses a frame rather than delaying a turn. The one dependency it added
  (Pillow, pinned) is imported by a single module and is what lets the
  graphical output be produced on CI without a display, so it replaces
  manual screenshotting rather than adding a runtime cost to a match.

- **Candidate exploration cost, and what bought the result.** Stage 9B-1A ran
  every candidate by **replaying committed development scenarios locally** -
  4 candidates x 471 screening scenarios, then 2,247 for the one that advanced,
  plus latency and belief instrumentation. Zero GitHub Actions minutes, zero
  network calls, zero LLM tokens: nothing in the research path calls a model,
  and no benchmark runs on CI. The screening subset exists precisely to keep the
  cost of *rejecting* a candidate small - three of four candidates were decided
  on 21% of the corpus, and only the survivor paid for the full set.
- **The candidate figures added no dependency.** They reuse the headless
  rasteriser the GUI stage already ships, so the research charts cost the same
  as the baseline charts: nothing to install, and identical bytes on Ubuntu and
  Windows.
