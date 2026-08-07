# Project Plan - group MaRs-777 (POLICE)

> **Status: DRAFT.**
> **Purpose:** Sequence the work from foundation to a compliant, competitive
> POLICE agent.
> **Authoritative source:** book v3.0.0 (`.project-spec/police_thief_p2p.pdf`);
> Appendix E (rules/sanctions); Appendix F (numeric values).
> **To extract later:** the concrete milestones and acceptance criteria implied
> by the book once the full 160-page extraction is done.
> **Note:** No requirement is approved merely because this file exists.

## Phases (provisional)

- **Stage 0A - Environment audit.** Complete.
- **Stage 0B / 0B.1 - Local foundation + evidence audit.** Complete.
- **Stage 0C - Initial commit + SSH push + cross-platform CI.** Complete (CI green Ubuntu+Windows).
- **Stage 0D - Repository protection.** Assessed; branch protection/rulesets unavailable on the current GitHub plan for private repos (platform limitation, not a failure).
- **Stage 1A - Authoritative book extraction.** Complete: `docs/spec/` = AUTHORITY_RULES, PAGE_COVERAGE (160/160), REQUIREMENT_CATALOG (**91** reqs), APPENDIX_E_CROSSWALK (55/55), APPENDIX_F_NUMERIC_INVENTORY, HIGH_RISK_REQUIREMENTS, JSON_SOURCE_MAP; plus expanded CONFLICT_REGISTER + REQUIREMENTS_TRACEABILITY. **No implementation.**
- **Stage 1B - Independent cross-audit + corrections.** Complete: confirmed App F = **32** parameter rows (14 FIXED / 9 MINIMUM / 9 NEGOTIABLE); corrected `technical_loss` provenance (not an App F row; C-07); closed `num_games` (=6, FIXED); exact catalog modality (MUST 76 / MUST NOT 9 / SHOULD 4 / MAY 2); all 55 App E entries (45/9/1) and 26 sampled citations re-verified. Evidence in `docs/spec/STAGE_1B_CROSS_AUDIT.md`.
- **Stage 1B supervising review = PASS.** The corrected Stage 1A/1B specification baseline is **approved** as the input to Stage 1C. Stage 1C (JSON contracts) has **not** started; JSON field/key/nesting items remain REVIEW REQUIRED; implementation remains prohibited.
- **Stage 1C - JSON contract construction** (the four mandatory documents) from the reviewed source map. Pending.
- **Stage 2 - Game logic & movement legality.** Pending (PRD-01).
- **Stage 3 - Local FastMCP protocol.** Pending (PRD-02).
- **Stage 4 - Baseline strategy.** Pending (PRD-03).
- **Stage 5 - Language & scent.** Pending (PRD-04).
- **Stage 6 - Public network.** Pending (PRD-05).
- **Stage 7 - Security & cryptography.** Pending (PRD-06).
- **Stage 8 - Reporting, GUI, replay.** Pending (PRD-07).
- **Stage 9 - Submission delivery.** Pending.
