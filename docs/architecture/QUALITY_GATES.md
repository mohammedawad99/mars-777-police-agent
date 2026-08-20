# Quality Gates — group MaRs-777

**Status: gate *definitions* frozen at Stage 2A; per-gate status reconciled at Stage 9A-1A.
**NO GATE HAS PASSED. NO GATE IS CLAIMED.** Stage 2A defines the evidence each gate
will require; none is evaluated here.

A gate PASSES only on **objective, reproducible evidence** — never on assertion, and
never because "the code was written".

## Gate 1 — REPOSITORY GATE

*Question: is this repository engineering-sound?*

| Evidence | Criterion |
|---|---|
| `uv sync --frozen` | exit 0, lockfile unchanged |
| `uv run ruff check .` | exit 0 |
| `uv run ruff format --check .` | exit 0 |
| `uv run mypy --strict src` | exit 0 |
| `uv run pytest --cov --cov-fail-under=90` | exit 0, coverage ≥ 90% |
| `uv build` | exit 0 |
| Git hygiene | clean tree, empty index, HEAD = origin/main = ls-remote |
| CI | green on **ubuntu-latest and windows-latest**. Ubuntu runs every test; the Windows gating suite excludes exactly one test, the documented native two-process exact-six stall (`CONCURRENCY_MODEL.md` §6), which runs in its own visible non-gating job |
| Secret scan | 0 findings in tree and history |
| File-size rule | every Python file ≤ **150 code lines**, enforced by `tools/check_python_loc.py` — see below |
| Dependency rules | import-graph DAG; no forbidden import; no cross-repo import |

**Status (Stage 9A-1B2): PASS on every row.** `uv sync --frozen`, the file-size
gate, ruff, `ruff format --check`, `mypy --strict`, the full suite, coverage,
`uv build`, Git hygiene, cross-OS CI, the secret scan and the dependency rules
are all green on the exact HEAD commit. The file-size rule now passes for
`src/**` **and** `tests/**`, and is enforced automatically rather than audited.

### The file-size rule

**Scope: every Python file in the repository, tests included.** The
professional-software guideline states the limit for code files (§3.2) and
restates it for test files explicitly (§6.1, test rule 6). This rule is
therefore **not** narrowed to `src/**`.

**Counting rule.** 150 **code** lines: blank lines and comment-only lines are
excluded, as §3.2 requires. Physical line count is reported alongside it for
transparency, and code is **split, never compressed** to fit — semicolon
packing or removing docstrings to pass the count is a violation of the rule's
purpose, not compliance with it.

**Measured at Stage 9A-2AF.**

| Tree | Files | Over the limit |
|---|---|---|
| `src/**/*.py` | 265 | **0** |
| `tests/**/*.py` | 449 | **0** |

**Enforcement: automatic.** `tools/check_python_loc.py` is the one authority for
this rule. It counts code lines exactly as defined above, inspects **both**
trees, prints every offender in sorted order, and exits non-zero. It runs as a
**gating** step in CI on Ubuntu **and** Windows, and the command a contributor
runs locally is the same command:

```bash
uv run python tools/check_python_loc.py
```

The checker is itself covered by tests: exactly 150 passes, 151 fails, blank and
comment-only lines are excluded, docstrings and inline-commented code lines are
counted, non-Python files and files outside the two trees are ignored, and the
failure list is sorted so the output is deterministic.

## Gate 2 — PROTOCOL GATE

*Question: does the agent speak the locked protocol correctly and safely?*

| Evidence | Criterion |
|---|---|
| Step-0 handshake | keyed authentication verified both directions; refuse-on-failure demonstrated |
| Config negotiation | byte-identical config; `config_sha256` equality **and** auth tag verified; Appendix F status rules enforced (FIXED/MINIMUM/NEGOTIABLE) |
| Commit-Reveal | full Commit→Ack→Reveal→Audit cycle; nonce withheld until audit; every `H_commit` recomputes |
| Negative suite | all 20 planned tests in `TEST_ARCHITECTURE.md` §2 pass, incl. malformed JSON, illegal move/barrier, stale/duplicate, wrong key, hash mismatch, 429, timeout, retry exhaustion |
| Cross-OS | identical canonical bytes and digests on Linux and Windows |
| Isolation | cross-process run with no shared state |

**Status: capabilities IMPLEMENTED AND COVERED; no Gate-2 evidence report has
been written.** Step-0 keyed authentication, config negotiation and lock,
the full Commit→Ack→Reveal→Audit cycle, cross-OS canonical bytes and
cross-process isolation are all implemented and exercised by the suite, and a
real two-process series has been played. What is missing is the **gate ritual
itself** — a written evidence report walking these rows with exact commands and
results. Until that exists this gate is reported as **PARTIAL**, not as passed.

## Gate 3 — MATCH GATE

*Question: was a real counted series actually played and provable?*

| Evidence | Criterion |
|---|---|
| Series completeness | **6 sub-games** played (`num_games` = 6 / FIXED) |
| Exact commits | the played `github_commit` recorded per sub-game and reproducible |
| Artifacts | all four artifacts present per game, correctly named, canonical, identity-bound (INV-01/02) |
| Logs | complete Commit/Ack/Reveal records + final nonce disclosure |
| Replay | independent replay from files only ⇒ **Verified OK**, no TAMPERED |
| Scores | derived solely from Appendix F values (+ technical_loss 0/0, C-07) |
| Opponent agreement | both teams' `result_sha256` equal, `mutual_agreement: true` |
| Sanction check | no missing/contradictory report (else **0 to both**, C-09) |

**Status: PARTNER_DEPENDENT.** No counted series exists. Six sub-games have been
played against an independent third-party implementation and six against a
synthetic distinct-group opponent, but both were explicitly **non-counted**, and
their evidence is written under names that cannot be mistaken for counted
artifacts. This gate cannot be evaluated until another group's real agent plays
us.

## Gate 4 — SUBMISSION GATE

*Question: is the deliverable complete and accessible to the grader?*

| Evidence | Criterion |
|---|---|
| Repository access | both repos reachable by the grader as required at submission time |
| Version identity | exact competition commit identifiable/reproducible (tag or recorded SHA) |
| Result JSON | `result_<game_id>.json` complete: identities, **four links**, `declaration_ref` join, per-sub-game scores/outcome/**commit**/tokens, cumulative, **total tokens**, timestamp, mutual agreement, `result_sha256`. Self-containment is a property of the **four-artifact set** — the declaration (MCP endpoints, hardware, members) is delivered with it (JDEC-014) |
| Gmail delivery | JSON **attachment** sent by each team to the required address (never free text) |
| Four links | both teams' police + thief repository links present |
| Documentation | required project documentation/PDF as specified |
| Moodle | per-member submission completed |
| Secret check | nothing secret in any submitted artifact |

**Status: FINAL_SUBMISSION_PENDING.** Row-level current state is tracked in
`docs/SUBMISSION_CHECKLIST.md`. Two rows are known to be unmet by construction
today: Gmail delivery (no reporting code exists) and the exact competition tag
(deliberately not created before the freeze).

## Gate discipline

- Gates are **ordered**: Repository → Protocol → Match → Submission. A later gate may not
  be claimed while an earlier one is unproven.
- Each gate produces a **written evidence report** with exact commands and results,
  including what was *not* verified.
- A failed gate is reported as **PARTIAL** or **BLOCKED** — never softened.
