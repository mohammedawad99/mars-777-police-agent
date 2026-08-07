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
- **Stage 1C - JSON contract construction** (the four mandatory documents). **Done (specification only; pending review):** `docs/spec/json/` = README (lifecycle) + CONFIG/DECLARATION/LOG/RESULT contracts + NAMING_AND_IDENTITY, CANONICALIZATION_CONTRACT, VERSIONING, SIGNATURE_AND_HASH_PROVENANCE, PROJECT_CONTRACT_DECISIONS (JDEC-001…011), FIELD_MATRIX, CROSS_ARTIFACT_INVARIANTS (INV-01…09), ADVERSARIAL_REVIEW. No JSON files, schemas, serializers, or code. Provenance-classified (SOURCE-EXPLICIT / SOURCE-SEMANTIC / PROJECT-CONTRACT / EXAMPLE-ONLY / REVIEW-REQUIRED). num_games=6/FIXED and technical_loss C-07 preserved. **Not approved until supervising review.**
- **Stage 1D - Independent contract audit + interoperability lock.** Done (specification only; pending review): confirmed D1 (`verdict` = `intent`, C-08), refuted D3 (`game_uid` is source-named — kept), reclassified all interop dependencies (SOURCE-LOCKED / PROJECT-LOCKED / NEGOTIATED-PRE-MATCH), locked `state` (JDEC-012), made `config_sha256` non-self-referential, defined NDEC-001…006, and confirmed **0 blocking** items (`docs/spec/json/INTEROPERABILITY_BLOCKERS.md`). Exact counts, no approximates. New docs: PROTOCOL_TIMELINE, INTEROPERABILITY_NEGOTIATION, INTEROPERABILITY_BLOCKERS, STAGE_1D_AUDIT.
- **Stage 1D.1 - Cryptographic & reporting contract corrections.** Done (specification only; no code/commit): corrected four defects the Stage-1D review found. **K1** Step-0 is **keyed authentication with a pre-supplied key** (SOURCE-REQUIRED, Ch 5 p.55–56), **not** an unkeyed SHA-256 digest — project default HMAC-SHA256 (JDEC-013, PROJECT-CONTRACT); **K2** the config carries a source-required **signature exchange** (App B p.128) beyond `config_sha256` equality (NDEC-007); **K3** the emailed result must be **self-contained** — FastMCP endpoints + cryptographically-signed hardware declarations (`hardware_auth`) are mandatory (INV-10/12/13); **K4** the **reporting-sanction conflict** (Ch 9 per-side non-credit vs App E #35 game-void/0-both) is documented as **C-09**, strictest 0-both adopted. `game_uid` kept (K5); `verdict`=`intent` kept (K6, C-08). Registers now NDEC-001…007, JDEC-001…013, INV-01…15; the field matrix was reconciled **row-exact** at Stage 1-CLOSE (77 semantic-field rows: declaration 16, config 39, log 9, result 13; provenance total = status total = 77; 0 blocking); **no key material** in any artifact. Crypto taxonomy kept precise: HASH ≠ MAC ≠ PKI signature ≠ mutual acknowledgement.
- **Stage 1 completion** (pending review): commit the reviewed specification + JSON-contract baseline; then a controlled sync of the reviewed *common* spec into the thief repo. **No implementation until the PRD/architecture phase.**
- **Stage 2 - Game logic & movement legality.** Pending (PRD-01).
- **Stage 3 - Local FastMCP protocol.** Pending (PRD-02).
- **Stage 4 - Baseline strategy.** Pending (PRD-03).
- **Stage 5 - Language & scent.** Pending (PRD-04).
- **Stage 6 - Public network.** Pending (PRD-05).
- **Stage 7 - Security & cryptography.** Pending (PRD-06).
- **Stage 8 - Reporting, GUI, replay.** Pending (PRD-07).
- **Stage 9 - Submission delivery.** Pending.
