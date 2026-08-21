# Guideline alignment — group MaRs-777 (POLICE)

**Status: CURRENT.** Written at Stage 9A-1A against the lecturer's own document,
read directly. Nothing here is reconstructed from memory or from a summary.

## 1. The source

| Field | Value |
|---|---|
| Title | *Guidelines for Writing Professional Software at the Highest Level of Excellence* (הנחיות לכתיבת תוכנה מקצועית ברמת הצטיינות יתרה) |
| Author | Dr. Yoram Segal |
| Version | **3.00** |
| Document date | 2026-03-26 |
| Pages | 39 |
| SHA-256 | `3f02df37767c745efc47646140c2e6ac7cae3b9c87c92073daf4eef74be09ebb` |

The PDF is an **external course reference**. It is held outside both
repositories, read-only, and is deliberately **not committed** — this file
records its identity and section numbers instead, which is enough for anyone to
re-derive every verdict below from their own copy.

Section numbers below are the document's own (`§2.1` = README, `§3.2` = the
150-line rule, and so on). The Hebrew original renders them right-to-left as
`1.2`, `2.3`; they are written here in the conventional order.

## 2. The lecturer's own qualification (§19)

> Not every clause must be implemented in full; the more criteria are met, the
> higher the quality assessment. Focus on depth, professionalism, and
> demonstrated engineering capability.

§19 is recorded because it is real, and it is **not** used below to excuse a
single binding requirement of the project book. Where a clause is marked
`JUSTIFIED_NA`, the reason is structural — the project genuinely has no such
surface — never "§19 says we may skip it".

§19 also states that the assessment itself may be performed with AI agents.
Every claim in this document is therefore written to be **mechanically
checkable**: file paths, counts and commands, not adjectives.

## 3. Alignment matrix

Status vocabulary: **PASS** · **PARTIAL** · **GAP** · **JUSTIFIED_NA**.

| § | Requirement (summarised) | Status | Evidence | Closure |
|---|---|---|---|---|
| 2.1 | `README.md` as a full user manual: install, usage, examples, configuration, contribution, license & credits | **PASS** | `README.md` — all sections present, including **§12 screenshots**: a live belief map and a replay verification, both rendered by the real GUI from one real sub-game played in this repository (Stage 9A-2B) | Stage 9C final pass |
| 2.2 | `docs/` with `PRD.md`, `PLAN.md`, `TODO.md` | **PASS** | `docs/PRD.md` (index + goals), `docs/PLAN.md`, `docs/TODO.md` | — |
| 2.3 | A dedicated PRD per algorithm / central mechanism | **PASS** | `docs/prd/PRD-01…07` — game logic, FastMCP, strategy, language & scent, public network, security & cryptography, reporting/GUI/replay | — |
| 2.4 | Recommended tree (`src/`, `tests/`, `docs/`, `config/`, `data/`, `results/`, `assets/`, `notebooks/`, `.env.example`) | **PARTIAL** | `src/ tests/ docs/ config/ artifacts/ .env.example` present, plus `sdk/`, `shared/version.py`, `shared/rate_limits.py` and the gatekeeper modules; still no `data/`, `results/`, `assets/`, `notebooks/` | `notebooks/`+`results/` at Stage 9B |
| 2.5 | Mandatory workflow PRD → PLAN → TODO → per-mechanism PRD → approval → implement | **PASS** | `docs/AI_WORKFLOW.md`; every stage in `docs/PLAN.md` names its approval | — |
| 3.1 | Modular project structure, clear separation of concerns | **PASS** | hexagonal layout `domain/ app/ protocol/ transport/ infra/`, enforced by `docs/architecture/DEPENDENCY_RULES.md` and a framework-confinement test | — |
| 3.2 | **≤ 150 code lines per file** (blank and comment lines excluded); split, never compress | **PASS** | **0 over the limit in `src/` and 0 in `tests/`**, and no longer audited by hand: `tools/check_python_loc.py` is the one authority, runs as a gating CI step on Ubuntu and Windows, and is the same command a contributor runs locally | — |
| 3.3 | Docstrings on every module/class/function; comments explain *why* | **PASS** | every `src/**/*.py` module opens with a rationale docstring; ruff `D`-style discipline is visible throughout | — |
| 4.1 | **SDK layer** — one public entry point for all consumers; no business logic in CLI/GUI/controllers | **PASS** | `mars777_police/sdk` — `AgentSdk` with nine operations, each a forwarding call to the composition module that owns the work. Every operator entrypoint now reaches nothing but the standard library and `.sdk`, proven by a structural test; a second test proves the facade names no business authority and no framework; an out-of-process consumer test proves the surface is usable from the installed distribution alone. Extended at 9A-2A with the replay operations and at 9A-2B with the live-view seam; the GUI *consumes* the facade rather than sitting behind it, so the dependency points inward | — |
| 4.2 | OOP, DRY, extract shared logic, mixin discipline | **PASS** | shared authorities are extracted, not copied (e.g. `app/kit_payload.py`, `transport/call_arguments.py`); no duplicated function body found across the package | — |
| 5.1 | **Central API Gatekeeper** — every external call through it; rate limits, queue, retries, monitoring | **PASS for provider calls; peer gameplay deliberately excluded** | `app/gatekeeper.py` owns rate, concurrency, a bounded FIFO, bounded retries and per-call observation for provider operations, and the one provider surface that exists (`ngrok.discover_tunnels`) is composed through it. Peer gameplay keeps its stronger protocol-specific authorities — see §5 of this document and `API_BOUNDARIES.md` §10 | — |
| 5.2 | Rate limits from configuration, never hardcoded | **PASS** | `config/rate_limits.json` — versioned, per-service, loaded by one typed loader that refuses a missing file, bad JSON, an unknown key, a missing key, a malformed value or an unsupported version. The peer-negotiated `RateLimiterTerms` remain a separate authority and are untouched | — |
| 5.3 | Overflow queued (FIFO, bounded, backpressure), never dropped | **PASS** | `app/gatekeeper_queue.py` — a bounded FIFO whose depth comes from configuration, served strictly in arrival order, surviving cancellation without reordering, and raising backpressure only at the boundary. The gate drains it as the rolling windows reset | — |
| 6.1 | TDD red-green-refactor; every module has a test file; **test files also obey the 150-line rule** | **PASS** | tests-first is the recorded method for every implementation stage (`docs/PLAN.md`, `docs/AI_WORKFLOW.md`); the test-file size rule is now met by every file and enforced automatically. The rule was **not** narrowed to `src/` | — |
| 6.2 | Coverage ≥ 85%, suite fails below the threshold | **PASS** | measured **100%**; gate `fail_under = 90` in `pyproject.toml` and in CI — both above the 85% floor | — |
| 6.3 | Edge cases identified, documented, defensive programming, graceful degradation | **PASS** | `docs/architecture/ERROR_MODEL.md`; frozen error identities; dedicated edge suites (`tests/kit_series/test_kit_edges.py`, `tests/boot/test_runtime_edges.py`) | — |
| 6.4 | Expected test results documented; automated pass/fail reports; run logs kept | **PARTIAL** | CI runs the full suite on every push and its result is public per commit; no stored expected-result report artifact | Stage 9C |
| 7.1 | Ruff — zero violations | **PASS** | `uv run ruff check .` and `uv run ruff format --check .` are CI gates | — |
| 7.2 | No hardcoded configurable values | **PASS** | game parameters come from `NegotiatedConfig`; project constants live in dedicated modules; secrets come only from the environment (`infra/settings.py`) | — |
| 7.3 | Versioned configuration files, `.env` git-ignored, `.env.example` committed | **PASS** | `config/rate_limits.json` is versioned and validated at load; `.env.example` is committed; `.gitignore` covers `.env`, `.env.*`, `token.json`, `client_secret*.json`. The binding **game** configuration remains negotiated with the peer rather than shipped, by design | — |
| 7.4 | No secrets in the project; environment variables only; key rotation and least privilege | **PASS** | `AuthSecret` cannot be printed (`repr`/`str` → `<withheld>`); the tunnel credential is never read by this project at all; `SECURITY.md`; secret scan clean | — |
| 8.1 | **Explicit version tracking** for code, configuration and rate limits, starting at `1.00`, validated at boot | **PASS** | all three rows met: software version, configuration schema version, and now `rate_limits.version`. See §4 below for what each one actually means | — |
| 8.2 | Clear commit history, feature branches, PR review, tags for major versions | **PARTIAL** | 107 commits, one purpose each, no force-push, no rewritten history; work is supervised stage-by-stage on `main` rather than through PRs; **no tag yet** — the submission tag is deliberately deferred to Stage 9C | Stage 9C |
| 8.3 | **Prompt book** — every significant prompt, its context and goal, outputs, iterations, lessons | **PASS** | `docs/PROMPTS.md` (stage register, backfilled through 9B-1A) + `docs/AI_WORKFLOW.md` (method, corrections, lessons) | — |
| 8.4 | **uv mandatory**; no `pip`, no bare `python -m` in code, scripts, CI or documentation | **PASS** | `pyproject.toml` + `uv.lock` committed; CI installs with `uv sync --frozen` and runs every tool through `uv run`; all documented commands are `uv run …` | — |
| 9.1 | Systematic parameter study / sensitivity analysis | **PASS** | `research/` sweeps seven opponent families × six source-legal configuration families × three disjoint seed banks — 6,048 games per role — over the Appendix F MINIMUM/NEGOTIABLE axes only, never a FIXED one. `docs/research/COMPETITIVE_RESEARCH.md` §5 | — |
| 9.2 | Results-analysis notebook | **PARTIAL** | the guideline's *"or equivalent"*: every statistic lives in tested functions (`research/analysis.py`, `research/stats.py`) and one documented command regenerates every table and figure from the committed rows. A notebook surface on top of those functions is deliberately **not** added while GitHub Actions is a scarce resource, because Jupyter is a large optional dependency whose absence would silently skip the tests that prove the analysis reproduces | Stage 9C, if a notebook surface is wanted |
| 9.3 | Result visualisation (bar/line/scatter/heatmap/box) | **PASS** | eight figures under `results/figures/`, regenerated by one command from the committed result rows, drawn with the project's own tested deterministic renderer — title, labelled axes, units, sample size, baseline identity, zero-based proportion scales, no 3-D. **No plotting dependency was added**. Stage 9B-1A adds two candidate figures under `results/figures/candidates/` — a **diverging** delta chart with a real zero line (a signed difference must not be drawn on a shifted origin) and an exploration progression curve that keeps and marks the rejected candidates. Both are labelled **DEVELOPMENT RESEARCH / NOT FINAL HOLDOUT / NOT PRODUCTION PROMOTION**, and the progression is explicitly *not* a learning curve: nothing is trained, the x axis is the order ideas were tried. Stage 9B-2 completes the set with the strategy research progression (baseline → C1 rejected → C2 not advanced → C3 rejected → C4 ablation → development → validation → stress → **one-shot final holdout** → promotion), the per-bank delta comparison and the holdout family chart. The holdout point is drawn **once** from its recorded result and never re-estimated. Still not a learning curve: nothing is trained | — |
| 10 | UI/UX quality criteria, Nielsen heuristics, screenshots of every screen | **PASS** | `docs/reference/GUI.md` and README §12. Two screens exist and both are photographed. **Visibility of system status** — a turn-state banner naming the mode, role, sub-game, step and phase. **Match between system and world** — the source's own words (`Verified OK`, `TAMPERED`), never invented status names. **Error prevention** — the windows have no control that could act, so there is no destructive action to confirm. **Recognition over recall** — every heated belief cell carries its number and every verdict its glyph, so nothing depends on remembering a colour key. **Aesthetic and minimalist design** — one board, one panel, no chrome that carries no information. **Accessibility** — status is colour **and** glyph **and** word, so no judgement rests on hue alone | Stage 9C final pass |
| 11 | Cost analysis (token counts, cost per model, budget monitoring) | **PARTIAL** | `docs/COSTS.md` records **measured** resource use; the token table is structurally `0` because the shipped hint path is a deterministic template provider with no model and no network | — (revisit only if an LLM path is ever enabled) |
| 12 | Extension points, plugin-style interfaces, maintainability | **PASS** | a **21-port register** in `docs/architecture/API_BOUNDARIES.md`, of which **18** are declared in `src/` as `Protocol` classes — `StrategyPort`, `PeerTransportPort`, `ArtifactStorePort`, `CommitmentPort`, `NonceSourcePort`, `TimestampPort`, `HintPort`, `HintCatalogue`, `PublicIngressPort`, `ConfigDigestPort`, `ConfigLockAuthPort`, `ResultDigestPort`, `TokenAccountingPort`, `PeerOperations`, `AuthProvider`, `HostResolver`, `JsonFetcher`, `ScentBeliefSource`. Every one has a production adapter and a test double, so a consumer can be replaced without touching the domain | — |
| 13 | ISO/IEC 25010 product-quality characteristics | **PASS** (mapped) | §6 of this document | — |
| 14 | Package organisation: `pyproject.toml` with name/version/description/author/license/deps; `__init__.py` everywhere with `__version__`; relative imports only | **PASS** | all metadata present and current; `__version__` renders the authority rather than holding a literal; `__all__` declared in `__init__.py` and in `sdk/__init__.py`; every import in `src/` is relative or by package name | — |
| 15 | Concurrency: right tool for I/O vs CPU, thread safety, resource cleanup | **PASS** | `docs/architecture/CONCURRENCY_MODEL.md` — single-threaded asyncio for an I/O-bound protocol, one owner per mutable structure, deterministic ordering, explicit teardown proven by test | — |
| 16 | Building-block design: declared input / output / setup data, single responsibility, dependency injection | **PASS** | every adapter is constructed with its collaborators; ports are the declared interfaces; no module reaches for a global | — |
| 17 | Final submission checklist | **PARTIAL** | `docs/SUBMISSION_CHECKLIST.md` is current and per-row evidenced; several rows are legitimately still `PENDING` | Stage 9C |
| 20 | Detailed appendix (restates 2–17 as a checklist) | — | covered by the rows above | — |


## 4. §8.1 — three different questions, and why they are not one

The clause names three version rows and asks the application to validate
compatibility at startup. Reading them as one requirement is the mistake this
project made and then corrected, so the distinction is recorded here.

| | Question | Authority | Status |
|---|---|---|---|
| **Software version consistency** | is this process running the code it thinks it is? | `shared/version.py` — one value, rendered `1.00` for the guideline and `1.0` for packaging; `pyproject.toml`, `__version__` and the installed distribution metadata are held to it by test | **PASS** — `verify_installation()` refuses a mismatch at facade construction |
| **Configuration schema compatibility** | can this build represent and run this configuration revision? | `domain/config_schema.py` — `SUPPORTED_CONFIG_SCHEMA_VERSIONS` | **PASS** — an unsupported revision is not a constructible `NegotiatedConfig` |
| **Peer configuration equality** | do both peers hold the same configuration bytes? | the mutual `config_sha256` comparison at the lock | **PASS** — unchanged |
| **Local rate-limit configuration version** | can this build run this local provider policy? | `config/rate_limits.json` `rate_limits.version`, against `SUPPORTED_RATE_LIMIT_VERSIONS` | **PASS** — an unsupported version refuses before any provider call is possible |

**They are not substitutes for one another.**

- Software consistency says nothing about the configuration: a correctly
  installed build can still be handed a revision it cannot represent.
- **Peer equality is not compatibility.** Byte-identity proves the two sides hold
  the *same* document; it proves nothing about whether either side can run it.
  Two peers can agree perfectly on a version neither one supports — which is
  exactly the hole the guideline's startup-validation clause exists to close, and
  exactly what the local support authority now closes.
- Configuration compatibility is deliberately **local**. Nothing about a peer's
  software version is consulted, and nothing about ours is sent: a counterparty
  running their own code at their own package version is not a fault.

**Order.** Shape and local support are decided when a configuration first becomes
a value — one place, the domain constructor — which is strictly before
negotiation, before convergence and before the lock. There is no fallback: an
unsupported revision is never normalised, defaulted or downgraded, and never
accepted because both peers happened to send it.

**All three §8.1 rows are now met.** The rate-limit row was closed at Stage
9A-1C by `config/rate_limits.json`, whose `version` is validated against the
versions this build supports before any provider call can be made — refusal, no
fallback, no silent migration. Its version is stored as **text** for the same
reason the software version is: `1.00` written as a JSON number reads back as
`1.0`.

## 5. §5.1 — what a Gatekeeper may and may not wrap

Recorded because a naïve reading of §5.1 would **break** this project.

| External surface | Timeout | Retry | Rate limit | Queue | Idempotency | Gatekeeper-safe? |
|---|---|---|---|---|---|---|
| Peer gameplay calls (FastMCP `receive_turn`, `submit_audit`, `receive_control`) | locked `NegotiatedConfig` value, applied per request by `transport/session_deadline.py` | **must stay forbidden** | negotiated floors apply | **must stay forbidden** | commitment-keyed dedupe in `app/kit_delivery.py` | **NO** — a generic retry re-sends a turn the peer already applied, which Appendix E rule 35 classifies as a protocol violation, and a queue would silently break lockstep ordering |
| Peer pre-game (`negotiate` / Step-0) | bounded startup budget | **narrow, already implemented** — only "peer not listening yet", never a refusal | negotiated floors apply | n/a | n/a | partial — the existing `startup_budget.py` is the correct authority |
| Tunnel provider API (`infra/ngrok_ingress.py`, `ingress_release.py`) | 8 s / httpx `ReadTimeout` | safe | **missing** | **missing** | safe | **YES** — this is the one surface a real Gatekeeper should own today |
| Gmail / reporting | — | — | — | — | — | **YES**, when it exists — §5.1's motivating case (HTTP 429 back-off) |
| LLM provider | n/a | n/a | n/a | n/a | n/a | **JUSTIFIED_NA** — the shipped hint policy is a deterministic template catalogue: no provider, no network, no tokens |

**Closed at Stage 9A-1C, exactly this way.** The Gatekeeper owns provider calls;
peer gameplay keeps its stronger protocol-specific authorities and is held
outside by a structural test. The control goal of §5.1 is met for every surface
where generic control is semantically safe, and deliberately not applied where it
would break the protocol.

## 6. ISO/IEC 25010 mapping (§13)

| Characteristic | How this project addresses it | Evidence |
|---|---|---|
| Functional suitability | every book requirement is catalogued and traced to code and tests | `docs/spec/REQUIREMENT_CATALOG.md` (91), `docs/REQUIREMENTS_TRACEABILITY.md` |
| Performance efficiency | measured protocol overhead against the turn budget | `docs/COSTS.md`; gateway hop ≈ 7.8 ms against a 180 s budget |
| Compatibility | two envelope profiles; interoperability with a third-party pinned kit proven by live play | `docs/architecture/API_BOUNDARIES.md §8`, `docs/reference/KIT_PAIRING_HANDOFF.md` |
| Usability | CLI with one option per decision, explicit exit-status classification, operator runbook | `docs/reference/MATCH_RUNBOOK.md`; `README.md` |
| Reliability | deterministic engine, 100% covered, settlement signalled rather than inferred, proven teardown | CI; `docs/architecture/STATE_MACHINE.md` |
| Security | keyed Step-0 authentication, commitment/reveal integrity, unprintable secrets, threat model | `docs/architecture/SECURITY_ARCHITECTURE.md` (15 threats), `SECURITY.md` |
| Maintainability | hexagonal layers, a 21-port register of which 18 are declared `Protocol` classes, ≤150 code lines per source file enforced by a gating check, dependency rules enforced by test | `docs/architecture/DEPENDENCY_RULES.md`, `QUALITY_GATES.md` |
| Portability | `uv`-managed, Python pinned to 3.12, CI on Ubuntu **and** Windows, no absolute paths | `.github/workflows/ci.yml`, `pyproject.toml` |

## 7. Where this document must be updated

- when Stage 9B completes the parameter study and notebook (§9.1–§9.2); its
  charts (§9.3) and the strategy research evidence are delivered;
- at the submission freeze (§8.2 tag, §17).

§10 and §2.1 closed at Stage 9A-2B. The terminal Replay Viewer added at Stage
9A-2A was deliberately never counted as a screenshot; the two committed images
are of the graphical windows themselves.
