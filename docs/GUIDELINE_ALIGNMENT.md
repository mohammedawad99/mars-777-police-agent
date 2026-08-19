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
| 2.1 | `README.md` as a full user manual: install, usage, examples, configuration, contribution, license & credits | **PARTIAL** | `README.md` — all sections present; **screenshots absent** because there is no GUI to photograph | GUI slice, then Stage 9C |
| 2.2 | `docs/` with `PRD.md`, `PLAN.md`, `TODO.md` | **PASS** | `docs/PRD.md` (index + goals), `docs/PLAN.md`, `docs/TODO.md` | — |
| 2.3 | A dedicated PRD per algorithm / central mechanism | **PASS** | `docs/prd/PRD-01…07` — game logic, FastMCP, strategy, language & scent, public network, security & cryptography, reporting/GUI/replay | — |
| 2.4 | Recommended tree (`src/`, `tests/`, `docs/`, `config/`, `data/`, `results/`, `assets/`, `notebooks/`, `.env.example`) | **PARTIAL** | `src/ tests/ docs/ config/ artifacts/ .env.example` present, and **`sdk/` and `shared/version.py` added at Stage 9A-1B1**; still no `shared/gatekeeper.py`, `data/`, `results/`, `assets/`, `notebooks/` | §5.1 row below; `notebooks/`+`results/` at Stage 9B |
| 2.5 | Mandatory workflow PRD → PLAN → TODO → per-mechanism PRD → approval → implement | **PASS** | `docs/AI_WORKFLOW.md`; every stage in `docs/PLAN.md` names its approval | — |
| 3.1 | Modular project structure, clear separation of concerns | **PASS** | hexagonal layout `domain/ app/ protocol/ transport/ infra/`, enforced by `docs/architecture/DEPENDENCY_RULES.md` and a framework-confinement test | — |
| 3.2 | **≤ 150 code lines per file** (blank and comment lines excluded); split, never compress | **PARTIAL** | `src/`: **0 / 236** files over the limit. `tests/`: **13** files over it (largest 435 code lines) | Stage 9A-1B split |
| 3.3 | Docstrings on every module/class/function; comments explain *why* | **PASS** | every `src/**/*.py` module opens with a rationale docstring; ruff `D`-style discipline is visible throughout | — |
| 4.1 | **SDK layer** — one public entry point for all consumers; no business logic in CLI/GUI/controllers | **PASS** | `mars777_police/sdk` — `AgentSdk` with five operations, each a forwarding call to the composition module that owns the work. Every operator entrypoint now reaches nothing but the standard library and `.sdk`, proven by a structural test; a second test proves the facade names no business authority and no framework; an out-of-process consumer test proves the surface is usable from the installed distribution alone | — (extended when GUI and replay exist) |
| 4.2 | OOP, DRY, extract shared logic, mixin discipline | **PASS** | shared authorities are extracted, not copied (e.g. `app/kit_payload.py`, `transport/call_arguments.py`); no duplicated function body found across the package | — |
| 5.1 | **Central API Gatekeeper** — every external call through it; rate limits, queue, retries, monitoring | **GAP** (with real partial control) | dedicated authorities exist per surface — `transport/session_deadline.py` (deadline), `startup_budget.py` (narrow retry), `app/network_failure_policy.py` (explicit no-retry rule), `app/kit_delivery.py` (idempotency) — but there is **no single component** enforcing limits and logging every outbound call | Stage 9A-1C; see §5 for what must **not** be wrapped |
| 5.2 | Rate limits from configuration, never hardcoded | **PARTIAL** | `RateLimiterTerms` (requests/min, concurrency, backoff, max retries, queue depth) is **negotiated and cryptographically locked** at Step-0 and validated against Appendix F floors — so nothing is hardcoded — but there is **no local versioned `config/rate_limits.json`**, and the terms are **not enforced at call time** | Stage 9A-1C |
| 5.3 | Overflow queued (FIFO, bounded, backpressure), never dropped | **GAP** | `queue_depth` is negotiated and validated; no queue implementation consumes it | Stage 9A-1C |
| 6.1 | TDD red-green-refactor; every module has a test file; **test files also obey the 150-line rule** | **PARTIAL** | tests-first is the recorded method for every implementation stage (`docs/PLAN.md`, `docs/AI_WORKFLOW.md`); 387 test files; **13 exceed 150 code lines** | Stage 9A-1B split |
| 6.2 | Coverage ≥ 85%, suite fails below the threshold | **PASS** | measured **100%**; gate `fail_under = 90` in `pyproject.toml` and in CI — both above the 85% floor | — |
| 6.3 | Edge cases identified, documented, defensive programming, graceful degradation | **PASS** | `docs/architecture/ERROR_MODEL.md`; frozen error identities; dedicated edge suites (`tests/kit_series/test_kit_edges.py`, `tests/boot/test_runtime_edges.py`) | — |
| 6.4 | Expected test results documented; automated pass/fail reports; run logs kept | **PARTIAL** | CI runs the full suite on every push and its result is public per commit; no stored expected-result report artifact | Stage 9C |
| 7.1 | Ruff — zero violations | **PASS** | `uv run ruff check .` and `uv run ruff format --check .` are CI gates | — |
| 7.2 | No hardcoded configurable values | **PASS** | game parameters come from `NegotiatedConfig`; project constants live in dedicated modules; secrets come only from the environment (`infra/settings.py`) | — |
| 7.3 | Versioned configuration files, `.env` git-ignored, `.env.example` committed | **PARTIAL** | `.env.example` added at this stage; `.gitignore` covers `.env`, `.env.*`, `token.json`, `client_secret*.json`; **`config/` holds no versioned JSON** because the binding configuration is negotiated with the peer, not shipped | Stage 9A-1C |
| 7.4 | No secrets in the project; environment variables only; key rotation and least privilege | **PASS** | `AuthSecret` cannot be printed (`repr`/`str` → `<withheld>`); the tunnel credential is never read by this project at all; `SECURITY.md`; secret scan clean | — |
| 8.1 | **Explicit version tracking** for code, configuration and rate limits, starting at `1.00`, validated at boot | **PARTIAL** | **Code version: PASS** · **Configuration version: PASS** · **Rate-limits version: PENDING.** See §4 below for what each of the three actually means here | Stage 9A-1C |
| 8.2 | Clear commit history, feature branches, PR review, tags for major versions | **PARTIAL** | 107 commits, one purpose each, no force-push, no rewritten history; work is supervised stage-by-stage on `main` rather than through PRs; **no tag yet** — the submission tag is deliberately deferred to Stage 9C | Stage 9C |
| 8.3 | **Prompt book** — every significant prompt, its context and goal, outputs, iterations, lessons | **PASS** | `docs/PROMPTS.md` (stage register, backfilled through 9A-0) + `docs/AI_WORKFLOW.md` (method, corrections, lessons) | — |
| 8.4 | **uv mandatory**; no `pip`, no bare `python -m` in code, scripts, CI or documentation | **PASS** | `pyproject.toml` + `uv.lock` committed; CI installs with `uv sync --frozen` and runs every tool through `uv run`; all documented commands are `uv run …` | — |
| 9.1 | Systematic parameter study / sensitivity analysis | **GAP** | not started; deliberately deferred so that no learning curve is fabricated | Stage 9B |
| 9.2 | Results-analysis notebook | **GAP** | no `notebooks/` | Stage 9B |
| 9.3 | Result visualisation (bar/line/scatter/heatmap/box) | **GAP** | no generated charts | Stage 9B |
| 10 | UI/UX quality criteria, Nielsen heuristics, screenshots of every screen | **GAP** | no GUI exists | GUI slice |
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
| **Peer configuration equality** | do both peers hold the same configuration bytes? | the mutual `config_sha256` comparison at the lock | **PASS** — unchanged, and never touched by this stage |

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

**Still pending.** The third row, `rate_limits.version`, has no home until the
local versioned rate-limit configuration file exists. §8.1 is therefore **not**
claimed fully closed.

## 5. §5.1 — what a Gatekeeper may and may not wrap

Recorded because a naïve reading of §5.1 would **break** this project.

| External surface | Timeout | Retry | Rate limit | Queue | Idempotency | Gatekeeper-safe? |
|---|---|---|---|---|---|---|
| Peer gameplay calls (FastMCP `receive_turn`, `submit_audit`, `receive_control`) | locked `NegotiatedConfig` value, applied per request by `transport/session_deadline.py` | **must stay forbidden** | negotiated floors apply | **must stay forbidden** | commitment-keyed dedupe in `app/kit_delivery.py` | **NO** — a generic retry re-sends a turn the peer already applied, which Appendix E rule 35 classifies as a protocol violation, and a queue would silently break lockstep ordering |
| Peer pre-game (`negotiate` / Step-0) | bounded startup budget | **narrow, already implemented** — only "peer not listening yet", never a refusal | negotiated floors apply | n/a | n/a | partial — the existing `startup_budget.py` is the correct authority |
| Tunnel provider API (`infra/ngrok_ingress.py`, `ingress_release.py`) | 8 s / httpx `ReadTimeout` | safe | **missing** | **missing** | safe | **YES** — this is the one surface a real Gatekeeper should own today |
| Gmail / reporting | — | — | — | — | — | **YES**, when it exists — §5.1's motivating case (HTTP 429 back-off) |
| LLM provider | n/a | n/a | n/a | n/a | n/a | **JUSTIFIED_NA** — the shipped hint policy is a deterministic template catalogue: no provider, no network, no tokens |

The control goal of §5.1 is therefore **partly met by stronger, protocol-specific
authorities** and **unmet for provider APIs**. The closure is a Gatekeeper that
owns provider calls, not one that wraps gameplay.

## 6. ISO/IEC 25010 mapping (§13)

| Characteristic | How this project addresses it | Evidence |
|---|---|---|
| Functional suitability | every book requirement is catalogued and traced to code and tests | `docs/spec/REQUIREMENT_CATALOG.md` (91), `docs/REQUIREMENTS_TRACEABILITY.md` |
| Performance efficiency | measured protocol overhead against the turn budget | `docs/COSTS.md`; gateway hop ≈ 7.8 ms against a 180 s budget |
| Compatibility | two envelope profiles; interoperability with a third-party pinned kit proven by live play | `docs/architecture/API_BOUNDARIES.md §8`, `docs/reference/KIT_PAIRING_HANDOFF.md` |
| Usability | CLI with one option per decision, explicit exit-status classification, operator runbook | `docs/reference/MATCH_RUNBOOK.md`; `README.md` |
| Reliability | deterministic engine, 100% covered, settlement signalled rather than inferred, proven teardown | CI; `docs/architecture/STATE_MACHINE.md` |
| Security | keyed Step-0 authentication, commitment/reveal integrity, unprintable secrets, threat model | `docs/architecture/SECURITY_ARCHITECTURE.md` (15 threats), `SECURITY.md` |
| Maintainability | hexagonal layers, 12 ports, ≤150 code lines per source file, dependency rules enforced by test | `docs/architecture/DEPENDENCY_RULES.md`, `QUALITY_GATES.md` |
| Portability | `uv`-managed, Python pinned to 3.12, CI on Ubuntu **and** Windows, no absolute paths | `.github/workflows/ci.yml`, `pyproject.toml` |

## 7. Where this document must be updated

- when the test-file split lands (§3.2 / §6.1 rows);
- when a provider Gatekeeper lands (§5.1, §5.2, §5.3, §7.3);
- when the rate-limit configuration file gives §8.1 its third version row (§4);
- when Stage 9B produces the parameter study, notebook and charts (§9.1–§9.3);
- when a GUI and its screenshots exist (§10, §2.1);
- at the submission freeze (§8.2 tag, §17).
