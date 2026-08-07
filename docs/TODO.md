# TODO - group MaRs-777 (POLICE)

> **Status: DRAFT.**
> **Purpose:** Track outstanding foundation and project tasks.
> **Authoritative source:** book v3.0.0.
> **Note:** No requirement is approved merely because this file exists.

## Done
- [x] Stage 0A - environment / tooling / Git / GitHub preflight audit.
- [x] Stage 0B - local repository foundation.
- [x] Stage 0B.1 - final evidence audit (exact future-commit validation).
- [x] Stage 0C - private GitHub repository created; initial commit pushed over SSH.
- [x] Stage 0C - CI green on ubuntu-latest + windows-latest (all 4 matrix jobs).
- [x] Stage 0D - repository protection assessed (see below).
- [x] Stage 1A - full 160-page source extraction into `docs/spec/` (pending review).
- [x] Stage 1B - independent cross-audit + corrections (App F 32 rows / 14-9-9; technical_loss provenance; num_games closed; exact modality counts). See `docs/spec/STAGE_1B_CROSS_AUDIT.md`.

- [x] Stage 1B supervising review = **PASS**; corrected specification baseline approved as input to Stage 1C.

## In progress
- [ ] Stage 1B-CLOSE - commit + push the reviewed specification baseline (this stage).

## Pending
- [ ] Branch protection / rulesets - **blocked**: unavailable on the current GitHub
      plan for private repos (Stage 0D). Needs Pro upgrade, org, or public-at-submission.
- [x] Full 160-page source extraction - done (Stage 1A: `docs/spec/`).
- [ ] JSON contract construction - **pending Stage 1C**; source map done
      (`docs/spec/JSON_SOURCE_MAP.md`), some field details marked REVIEW REQUIRED.
- [ ] Example-simulator (Appendix D) review - non-binding; pending.
- [ ] Stage 1B - independent cross-audit of the extraction before it is accepted binding.
- [ ] PRD-01 game logic (Base Logic; board/movement/barriers/capture/scoring).
- [ ] PRD-02 local FastMCP (MCP infra + orchestrator/state-machine).
- [ ] PRD-03 baseline / blind strategy.
- [ ] PRD-04 language & scent.
- [ ] PRD-05 public network / tunnel / league.
- [ ] PRD-06 security & cryptography (commit-reveal, Step-0).
- [ ] PRD-07 reporting, GUI, replay (Gmail gatekeeper, Live GUI, Replay Viewer).
- [ ] Collaborator (Rawey7) access - pending explicit instruction.

_No game logic, JSON schema, or protocol code has been implemented. Stage 1A is
specification-only._
