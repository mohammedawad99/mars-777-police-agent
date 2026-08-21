# Submission checklist — group MaRs-777 (POLICE)

**Status: CURRENT.** Last verified at Stage 9A-2AF, on commits green in CI on
their exact SHAs in both repositories.

Every row carries one status and its evidence. This is a working gate, not a
ceremony: a row moves to `VERIFIED` only when the thing is in the repository and
green in CI on the exact commit.

| Status | Meaning |
|---|---|
| `VERIFIED` | done, in the repository, evidenced |
| `PENDING` | real remaining work, ours to do |
| `PARTNER_DEPENDENT` | cannot be completed without another group's real agent |
| `FINAL_FREEZE_PENDING` | deliberately held until the submission freeze |
| `NOT_APPLICABLE_WITH_REASON` | genuinely does not apply, with the reason stated |

## Delivery

| Item | Status | Evidence |
|---|---|---|
| Both repositories exist on GitHub under `mohammedawad99` | `VERIFIED` | private repos `mars-777-police-agent`, `mars-777-thief-agent` |
| Collaborator `Rawey7` added | `PENDING` | awaiting an explicit instruction; no collaborator action is taken without one |
| Exact competition commit tagged and reproducible | `FINAL_FREEZE_PENDING` | 0 tags by design until Stage 9C |
| Working tree clean, index empty, `HEAD = origin/main = ls-remote` | `VERIFIED` | checked mechanically at every stage entry |
| Branch protection / rulesets | `NOT_APPLICABLE_WITH_REASON` | unavailable for private repositories on the current GitHub plan (Stage 0D); a platform limitation, not an omission |

## Compliance with the project book

| Item | Status | Evidence |
|---|---|---|
| Full 160-page extraction with page coverage | `VERIFIED` | `docs/spec/PAGE_COVERAGE.md` (160/160) |
| Requirement catalog | `VERIFIED` | `docs/spec/REQUIREMENT_CATALOG.md` — **91** requirements |
| Appendix E crosswalk | `VERIFIED` | 55/55 entries (45 MUST, 9 MUST NOT, 1 SHOULD) |
| Appendix F numeric values sourced with citations | `VERIFIED` | `docs/spec/APPENDIX_F_NUMERIC_INVENTORY.md` — 32 rows (14 FIXED / 9 MINIMUM / 9 NEGOTIABLE) |
| Four mandatory JSON document types | `VERIFIED` | config / declaration / log / result contracts implemented; a complete series writes **14** official files |
| Commit-reveal cryptography | `VERIFIED` | sealed record, CSPRNG nonce, recomputation, `TAMPERED` on mismatch, golden vectors |
| Keyed Step-0 and configuration authentication | `VERIFIED` | implemented and covered; never downgraded for convenience |
| Game rules — movement, barriers, capture, scoring, terminal | `VERIFIED` | deterministic engine, 100% covered |
| Exactly six sub-games per counted series | `VERIFIED` | structurally enforced; a seventh sub-game is not representable |
| Public network / tunnel | `VERIFIED` | demonstrated end to end on one stable public route with proven teardown |
| **Replay Viewer** (`REPLAY-001`, `REPLAY-002`) | `VERIFIED` | `uv run python -m mars777_police.replay_main --log … --config …`; per-step `Verified OK` / `TAMPERED`, textual board, and an audit-completeness rule so a partly-checkable log cannot report success (exit `4`). `docs/reference/REPLAY_VIEWER.md` |
| **GUI** (`GUI-001/002/003`) | `VERIFIED` | `uv run python -m mars777_police.gui_main replay --log … --config …` and `… live --launch …`. Live view is local truth only, projected from `Observation`, with a labelled belief heatmap and a turn-state banner; the replay view shows both agents only after the audit point. `docs/reference/GUI.md` |
| **Gmail reporting** (`REPORT-001`, `REPORT-002`, `JSON-001`, `JSON-002`) | `IMPLEMENTATION_COMPLETE` / `LIVE_SEND_NOT_PERFORMED` | `uv run python -m mars777_police.report_main --result …`. The agreed result artifact is the message's **only** part - `multipart/mixed`, one `application/json` attachment, no textual body (ruling at 9A-2CF) - sent to the fixed Appendix F Table 20 address; eligibility is the Appendix E rule 35 mutual agreement. Proved against a fake provider at the adapter seam; **no real message has been sent**. `docs/reference/REPORTING.md` |
| **Rate-limit enforcement for provider calls** | `VERIFIED` | `app/gatekeeper.py` + versioned `config/rate_limits.json`; the tunnel Agent API is composed through it |
| **Rate-limit enforcement for Gmail** (`REPORT-003`, `NET-002`, E-28, E-29) | `VERIFIED` | the **token bucket** rule 28 names by algorithm, plus the Quota Manager and DOS detector of Ch 9 §9.3.1, composed inside the one Gatekeeper as `gmail.send_report`. `429` backs off, honours `Retry-After` within a cap, retries boundedly, then fails honestly |
| Counted match against another group | `PARTNER_DEPENDENT` | every run so far used a synthetic non-counted opponent or an explicitly friendly kit run |

## Engineering quality

| Item | Status | Evidence |
|---|---|---|
| Ruff lint — zero violations | `VERIFIED` | CI gate |
| Ruff format check | `VERIFIED` | CI gate |
| `mypy --strict` | `VERIFIED` | CI gate |
| Full test suite green | `VERIFIED` | CI on the exact SHA, Ubuntu and Windows |
| Coverage above the gate | `VERIFIED` | measured **100%**; `fail_under = 90` |
| `uv build` | `VERIFIED` | CI gate |
| `uv.lock` committed; `uv sync --frozen` clean | `VERIFIED` | 79 packages checked |
| `src/**` ≤ 150 code lines per file | `VERIFIED` | 0 violations across 248 files |
| `tests/**` ≤ 150 code lines per file | `VERIFIED` | 0 violations across 430 files; every over-limit file was split by responsibility at Stage 9A-1B2 |
| CI enforces the line rule automatically | `VERIFIED` | `tools/check_python_loc.py`, gating on Ubuntu and Windows; identical command locally |
| Public SDK façade (guideline §4.1) | `VERIFIED` | `sdk/AgentSdk` — five forwarding operations; operator entrypoints reach only the standard library and `.sdk`; structural and out-of-process consumer tests |
| `__all__` and `__version__` in `__init__.py` (§14.2) | `VERIFIED` | both declared; `__version__` renders the authority |
| CI green on `ubuntu-latest` **and** `windows-latest` | `VERIFIED` | both, every push |

## Documentation

| Item | Status | Evidence |
|---|---|---|
| `README.md` as a full user manual | `VERIFIED` | install, environment, usage in three modes, CLI flags, configuration, troubleshooting, testing, contributing, security, license & credits, known limitations |
| Dec-POMDP formulation in the README | `VERIFIED` | README §1.1 |
| FastMCP description in the README | `VERIFIED` | README §10 |
| Strategy description in the README | `VERIFIED` | README §11 |
| Companion-repository link | `VERIFIED` | README header and §1.2 |
| Learning curve | `NOT_APPLICABLE — SUBSTITUTED` | nothing is trained, so no learning curve is presented. The truthful equivalent is delivered: a **strategy research progression** over the order candidates were evaluated (baseline → C1 rejected → C2 not advanced → C3 rejected → C4 → development → validation → stress → one-shot holdout → promotion), with rejected candidates kept visible |
| Screenshots | `VERIFIED` | `docs/evidence/gui/live_belief_map.png` and `docs/evidence/gui/replay_verified.png`, both rendered by the real GUI from one real thirty-five-round sub-game played in this repository; regenerate with `MARS777_WRITE_GUI_EVIDENCE=1 uv run pytest tests/gui/test_gui_evidence.py`. README §12 |
| `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` | `VERIFIED` | all three current |
| Per-mechanism PRDs | `VERIFIED` | `docs/prd/PRD-01…07` |
| Architecture documentation | `VERIFIED` | 21 documents under `docs/architecture/` |
| Architecture **diagrams** | `PENDING` | no diagram of any kind is committed yet |
| Prompt book | `VERIFIED` | `docs/PROMPTS.md` backfilled through Stage 9A-0, honestly labelled |
| Systematic parameter study / result visualisation (guideline §9.1/§9.3) | `VERIFIED` | `research/` + `results/`: 6,048 games per role over seven opponent families, six source-legal configuration families and three disjoint seed banks; eight figures regenerated from committed rows by `uv run python -m research.bench_main all --out results`. `docs/research/COMPETITIVE_RESEARCH.md` |
| Results-analysis notebook (guideline §9.2) | `PARTIAL` | the guideline's *"or equivalent"*: every statistic is a tested function and one command regenerates every table and figure. A Jupyter surface is deliberately deferred rather than added as a large optional dependency |
| Guideline alignment document | `VERIFIED` | `docs/GUIDELINE_ALIGNMENT.md`, written against the actual v3.00 PDF |
| Cost analysis | `VERIFIED` | `docs/COSTS.md`, measured |
| Decision log | `VERIFIED` | `docs/DECISIONS.md` |

## Configuration and security

| Item | Status | Evidence |
|---|---|---|
| `.env` git-ignored | `VERIFIED` | `.gitignore` |
| `.env.example` committed with placeholders only | `VERIFIED` | added at Stage 9A-1A |
| No secrets in the repository | `VERIFIED` | secret scan clean at every stage |
| Secrets from environment only, unprintable in logs | `VERIFIED` | `AuthSecret.__repr__` / `__str__` render `<withheld>` |
| Tunnel credential never read by this project | `VERIFIED` | the ngrok agent uses the operator's own configuration |
| `SECURITY.md` and a threat model | `VERIFIED` | `SECURITY.md`; `docs/architecture/SECURITY_ARCHITECTURE.md` (15 threats) |
| Versioned configuration files | `VERIFIED` | `config/rate_limits.json` carries `rate_limits.version` and is validated at load; the binding game configuration remains negotiated with the peer by design |
| Software version authority starting at `1.00` | `VERIFIED` | `shared/version.py` holds one value at the guideline's initial version, rendered `1.00` and `1.0` from a single source; `pyproject.toml`, `__version__` and the installed distribution metadata are held to it by test, and a mismatch refuses the process |

## Research and analysis

| Item | Status | Evidence |
|---|---|---|
| Systematic parameter study | `DONE` | Stage 9B-0: 7 opponent families x 6 source-legal configuration families x 3 disjoint seed banks, over MINIMUM/NEGOTIABLE axes only |
| Sensitivity analysis | `DONE` | `docs/research/SENSITIVITY.md` — board size, quota, horizon, opponent family, the threshold variants already tried, and latency. Post-hoc and descriptive: nothing was run or tuned to produce it |
| Analysis notebook | `DONE` | `notebooks/competitive_research.ipynb` — explains and displays; every statistic stays in tested `research/` functions, and a test executes every cell against committed results |
| Result charts | `DONE` | 8 baseline + 6 candidate/evidence figures, all regenerated by one command from committed rows |
| Token cost table | `NOT_APPLICABLE_WITH_REASON` | the shipped path uses no model; measured consumption is a structural **0** (`docs/COSTS.md` §1) |

## Honesty

| Item | Status | Evidence |
|---|---|---|
| No fabricated performance, coverage or win-rate claim | `VERIFIED` | every figure in the documentation is measured and reproducible |
| Development evidence cannot be mistaken for counted evidence | `VERIFIED` | `friendly_` names, `evidence_class: DEVELOPMENT_EVIDENCE`, `counted_eligible: false`, `ABSENT` where authentication and mutual agreement did not happen |
| Every rule and value cited to the book | `VERIFIED` | `docs/spec/`, `docs/REQUIREMENTS_TRACEABILITY.md` |
| Stopped stages and rejected candidates recorded, not hidden | `VERIFIED` | Stage 8A-2 stopped with zero changes; the thief competitive candidate is recorded as **rejected** |


---

## Submission gate — Stage 9A-3 closure

Four buckets, because "not done" and "not ours to do" are different things and a
grader should not have to guess which is which.

### A. Ready now — repository, code and document evidence

| item | evidence |
|---|---|
| Agent plays a full counted-shaped series autonomously | six sub-games, six `CONSISTENT` audits, 14 artifacts per side, two OS processes |
| Protocol, auth, negotiation, lock, commit/reveal, audit | `tests/protocol/`, `tests/session/`, `tests/audit/`, `tests/semantic/` |
| Both audit gates documented with evidence | `docs/reference/AUDIT_GATES.md` |
| Strategy research, promotion and its rejections | `docs/research/COMPETITIVE_RESEARCH.md` §1–§18, `EVIDENCE_INDEX.md`, `SENSITIVITY.md`, notebook |
| Architecture diagrams | `docs/architecture/DIAGRAMS.md` — system, component, sequence, deployment |
| Requirement traceability | `docs/REQUIREMENTS_TRACEABILITY.md` |
| Expected test results | `docs/reference/EXPECTED_TEST_RESULTS.md` |
| Dependency and licence inventory | `docs/reference/DEPENDENCIES.md` |
| GUI + Replay screenshots (`DOC-001` #5) | `docs/evidence/gui/` |
| Packaging: `py.typed`, six console scripts, wheel + sdist | `tests/packaging/test_distribution_surface.py` |
| Quality: LOC, ruff, mypy --strict, 100% coverage, build | `docs/reference/EXPECTED_TEST_RESULTS.md` |

### B. Partner-dependent — needs another group's live agent

| item | status |
|---|---|
| Friendly interop with a real external opponent | **NOT PERFORMED** — proved only against the pinned kit and our own public loopback |
| Counted match | **NOT PERFORMED** |
| Counted result agreement with a real opponent | **NOT PERFORMED** |

Neither is a repository defect. Both are blocked on a counterparty, and no
substitute is presented as though it were the real thing.

### C. Operator-dependent — needs an explicit human authorisation

| item | status |
|---|---|
| Live Gmail send | **`LIVE_GMAIL_SEND: NOT_PERFORMED`** — implemented, rate-limited and tested end to end against a fake transport; a real send needs `MARS777_RUN_LIVE_GMAIL=1`, a token and a recipient |

### D. Final freeze — Stage 9C only

| item | status |
|---|---|
| Hostile final audit | pending |
| Push the outstanding local commits (one CI run) | pending |
| Final submission tag | pending — **no tag exists** |
