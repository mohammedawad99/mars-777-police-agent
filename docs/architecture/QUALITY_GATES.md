# Quality Gates — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — gate *definitions*.
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
| File-size rule | every Python file ≤ 150 lines |
| Dependency rules | import-graph DAG; no forbidden import; no cross-repo import |

**Status: NOT EVALUATED (no implementation exists).**

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

**Status: NOT EVALUATED.**

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

**Status: NOT EVALUATED.**

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

**Status: NOT EVALUATED.**

## Gate discipline

- Gates are **ordered**: Repository → Protocol → Match → Submission. A later gate may not
  be claimed while an earlier one is unproven.
- Each gate produces a **written evidence report** with exact commands and results,
  including what was *not* verified.
- A failed gate is reported as **PARTIAL** or **BLOCKED** — never softened.
