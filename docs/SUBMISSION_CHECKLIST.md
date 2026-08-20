# Submission checklist — group MaRs-777 (POLICE)

**Status: CURRENT.** Last verified at Stage 9A-1B2, on commits green in CI on
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
| **Replay Viewer** (`REPLAY-001`) | `PENDING` | an audit-time replay **engine** exists; a user-facing **viewer** does not |
| **GUI** (`GUI-001/002/003`) | `PENDING` | not implemented |
| **Gmail reporting** (`REPORT-001`) | `PENDING` | not implemented |
| **Rate-limit enforcement** (`REPORT-003`) | `PENDING` | terms negotiated, floor-validated and locked; never applied at call time |
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
| Learning curve | `PENDING` | nothing learns yet; will follow the Stage-9B experiments or not at all |
| Screenshots | `PENDING` | blocked on the GUI; no screenshot is fabricated |
| `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` | `VERIFIED` | all three current |
| Per-mechanism PRDs | `VERIFIED` | `docs/prd/PRD-01…07` |
| Architecture documentation | `VERIFIED` | 21 documents under `docs/architecture/` |
| Architecture **diagrams** | `PENDING` | no diagram of any kind is committed yet |
| Prompt book | `VERIFIED` | `docs/PROMPTS.md` backfilled through Stage 9A-0, honestly labelled |
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
| Versioned configuration files | `PENDING` | the binding configuration is negotiated and locked, not shipped; a local versioned configuration surface (and with it `rate_limits.version`) belongs to the provider gatekeeper slice |
| Software version authority starting at `1.00` | `VERIFIED` | `shared/version.py` holds one value at the guideline's initial version, rendered `1.00` and `1.0` from a single source; `pyproject.toml`, `__version__` and the installed distribution metadata are held to it by test, and a mismatch refuses the process |

## Research and analysis

| Item | Status | Evidence |
|---|---|---|
| Systematic parameter study | `PENDING` | Stage 9B |
| Sensitivity analysis | `PENDING` | Stage 9B |
| Analysis notebook | `PENDING` | Stage 9B |
| Result charts | `PENDING` | Stage 9B |
| Token cost table | `NOT_APPLICABLE_WITH_REASON` | the shipped path uses no model; measured consumption is a structural **0** (`docs/COSTS.md` §1) |

## Honesty

| Item | Status | Evidence |
|---|---|---|
| No fabricated performance, coverage or win-rate claim | `VERIFIED` | every figure in the documentation is measured and reproducible |
| Development evidence cannot be mistaken for counted evidence | `VERIFIED` | `friendly_` names, `evidence_class: DEVELOPMENT_EVIDENCE`, `counted_eligible: false`, `ABSENT` where authentication and mutual agreement did not happen |
| Every rule and value cited to the book | `VERIFIED` | `docs/spec/`, `docs/REQUIREMENTS_TRACEABILITY.md` |
| Stopped stages and rejected candidates recorded, not hidden | `VERIFIED` | Stage 8A-2 stopped with zero changes; the thief competitive candidate is recorded as **rejected** |
