# Test Architecture — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — test *design*. No tests written for it yet.**

**Principle.** Coverage is necessary but **not sufficient**: a 100%-covered agent can
still lose a match to a protocol or canonicalization defect. The ≥90% CI floor already
established is a *repository* gate; protocol/replay/E2E evidence is a separate gate
(`QUALITY_GATES.md`).

**Offline rule.** Every layer up to and including INTEGRATION and REPLAY must run with
**no public internet** — CI runs a local fake peer. Only EXTERNAL DELIVERY needs the
outside world.

## 1. Layers

| Layer | Scope | Doubles | Deterministic | Runs in CI |
|---|---|---|---|---|
| **UNIT** | one module, pure functions (rules, scoring, scent, board) | none | yes | yes |
| **CONTRACT** | every port honours its contract; **dependency/import rules** | fakes | yes | yes |
| **PROPERTY / INVARIANT** | invariants over generated inputs (legality, canonical round-trip, INV-01…15) | none | yes (seeded) | yes |
| **STATE-MACHINE** | legal/illegal transitions, ordering, idempotency | fake ports | yes | yes |
| **PROTOCOL** | wire schema, commit-reveal, keyed auth, config lock, negative cases | in-process fake peer | yes | yes |
| **INTEGRATION** | orchestrator + adapters together | local fake peer | mostly | yes |
| **CROSS-PROCESS** | two real processes (this agent vs a local stub peer) over real transport | local only | no | yes (Linux + Windows) |
| **REPLAY** | independent verification from artifacts only | none (files) | yes | yes |
| **SECURITY / NEGATIVE** | hostile/malformed/replayed input, secret-leak scans | hostile fake peer | yes | yes |
| **SIMULATION** | many self-play/stub series for strategy quality + regression | seeded | yes (seeded) | nightly/optional |
| **END-TO-END** | full series against a real opponent peer | real peer | no | manual/scheduled |
| **EXTERNAL DELIVERY** | Gmail send, GitHub links, submission artifacts | real services | no | manual, pre-submission |

## 2. Mandatory planned tests (highest risk first)

| # | Test | Layer | Expected behaviour | Locked requirement |
|---|---|---|---|---|
| 1 | **Malformed JSON** (truncated, wrong types, extra keys, huge payload, deep nesting) | PROTOCOL / SECURITY | rejected as `E-PROTO-MALFORMED`; no state change; bounded log | JSON-001…004 |
| 2 | **Illegal movement** (out of bounds, through barrier, >1 cell, wrong turn) | PROTOCOL / UNIT | deterministic reject; never applied | GAME-003, LLM-001 |
| 3 | **Invalid barrier** (over quota, non-adjacent, while moving, undeclared) | PROTOCOL | reject; audit evidence | BAR-001…005 |
| 4 | **Hash mismatch** (`H_commit` recompute differs) | PROTOCOL / REPLAY | **TAMPERED**, match void, no appeal (PDF p.75) | CRYPTO-001, INV-06 |
| 5 | **Wrong auth key / unknown `key_id` / missing mechanism** | SECURITY | `E-AUTH-FAILURE`; **refuse counted play**; no key bytes logged | CRYPTO-006, INV-14/15 |
| 6 | **Nonce mismatch / early nonce disclosure attempt** | PROTOCOL / SECURITY | reject; nonce absent from all pre-audit outputs | CRYPTO-002/010 |
| 7 | **Duplicate / stale / out-of-order message** | PROTOCOL | `E-PROTO-STALE`; idempotent, no double-apply | STATE_MACHINE R8 |
| 8 | **Timeout** (step deadline, watchdog) | INTEGRATION | correct escalation; evidence recorded | STATE-004/005 |
| 9 | **Retry exhaustion** | INTEGRATION | `E-RETRY-EXHAUSTED`; no silent continue | NET-003 |
| 10 | **HTTP 429** | INTEGRATION | back off to next window, **no immediate retry** | NET-002, REPORT-003 |
| 11 | **Config mismatch** (hash inequality, MINIMUM lowered, FIXED altered) | PROTOCOL | refuse to play | GAME-001/002, INV-15 |
| 12 | **Opponent disconnect mid-turn** | CROSS-PROCESS | deterministic handling; evidence; no corruption | STATE-004/005 |
| 13 | **Log mutation → TAMPERED** | REPLAY / SECURITY | replay detects any edit | REPLAY-001/002 |
| 14 | **Result disagreement / one-sided report** | INTEGRATION | **0 to both** | C-09, INV-11, E-35 |
| 15 | **External reporting failure** | INTEGRATION | retry; surfaced; never mutates score | REPORT-001/002 |
| 16 | **Windows/Linux canonicalization equivalence** | PROPERTY / CROSS-PROCESS | byte-identical canonical output and identical digests on both OSes | JDEC-002, NDEC-003 |
| 17 | **Privacy leak scans** (strategy/GUI/log/report contain no forbidden field, no secret) | SECURITY | assertions fail if a forbidden key appears | GUI-001/002, SEC-003/004 |
| 18 | **Dependency-direction test** (no cycles; forbidden imports absent) | CONTRACT | import graph is a DAG obeying the layer matrix | DEPENDENCY_RULES |
| 19 | **Zero-token fallback** (advisor disabled/failing) | INTEGRATION | full series completes deterministically | LLM_BOUNDARY §4 |
| 20 | **Replay from files only** (fresh process, no network) | REPLAY | verification succeeds offline | REPLAY-001/002 |

## 3. Fixtures and doubles

- **Fake peer** — cooperative (happy path), **hostile** (malformed/replayed/illegal), and
  **silent** (timeouts) variants. In-process for PROTOCOL, subprocess for CROSS-PROCESS.
- **Deterministic clock** — the only time source in tests (`ClockPort`).
- **Golden canonical vectors** — fixed inputs with known digests, asserted on both OSes.
- **Seeded RNG** — reproducible strategy and nonce-independent test paths.

## 4. Coverage policy

- Keep the established **≥90% line/branch** floor in CI (`--cov-fail-under=90`).
- Additionally require: 100% of `E-*` error codes exercised; 100% of state-machine
  transitions (legal and rejected) exercised; every port contract-tested.
- Coverage alone never satisfies the Protocol, Match, or Submission gates.
