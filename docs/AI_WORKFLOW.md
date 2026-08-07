# AI Workflow - group MaRs-777

> **Status: DRAFT.**

## Roles

- The **human** receives a prompt from the supervising reviewer.
- **Claude Code** performs repository and terminal work inside a single repository.
- Claude returns an **evidence report** (exact commands + results).
- Work is **reviewed** before any commit or push.

## Principles

- No implementation before an approved plan.
- No commit/push without explicit instruction.
- Exact command/result reporting; explicit statement of what was not verified.
- Stage prompt texts (e.g., Stage 0A through Stage 0C) may be recorded or
  referenced in `docs/PROMPTS.md` **without** including any secrets.
- Stage 0C established the two private GitHub remotes (owner mohammedawad99),
  pushed the initial commit over **SSH** (the OAuth token lacked the `workflow`
  scope), and achieved green CI on Ubuntu + Windows; commits and pushes happen
  only under explicit reviewer approval, and no authentication output or secret
  is ever recorded here.
- Stage 0D found that branch protection / rulesets are **unavailable** on the
  current GitHub plan for private repositories (a platform limitation, reported,
  not worked around).
- Stage 1A was a **specification-only** extraction of the authoritative 160-page
  book v3.0.0 into `docs/spec/` and the traceability/conflict artifacts. No game
  logic, JSON schema, or protocol code was written. All extracted requirements
  cite book pages. The Stage 1B independent cross-audit and the **supervising
  review (PASS)** have since accepted this corrected baseline; the four JSON
  contracts are deferred to Stage 1C (not started).
- Stage 1B independently re-audited the Stage 1A artifacts against the PDF and
  applied corrections (Appendix F has **32** parameter rows — 14 FIXED / 9 MINIMUM
  / 9 NEGOTIABLE — not 26; `technical_loss` 0/0 is binding via Ch 3 + App E #48 but
  is **not** an Appendix F row; `num_games` is **6, FIXED**; exact catalog modality
  MUST 76 / MUST NOT 9 / SHOULD 4 / MAY 2). Still specification-only; no code,
  schema, commit, or sibling access. Stage 1B review = PASS; the corrected
  baseline is approved for Stage 1C.
- Stage 1C defined **contracts** for the four mandatory JSON artifacts in
  `docs/spec/json/` — specification only, no JSON files/schemas/serializers/code.
  Every field is provenance-classified (SOURCE-EXPLICIT / SOURCE-SEMANTIC /
  PROJECT-CONTRACT / EXAMPLE-ONLY / REVIEW-REQUIRED); project decisions are JDEC-001…011.
  Contracts are **subject to supervising review**; **implementation has not begun**;
  **Stage 1D** will independently audit them before any synchronization or implementation.
- Stage 1D independently audited and **locked** the contracts for interoperability:
  `verdict` = `intent` (C-08); `game_uid` confirmed **source-named** (kept); `state`
  PROJECT-LOCKED; `config_sha256` non-self-referential; every interop dependency is
  SOURCE-LOCKED, PROJECT-LOCKED, or NEGOTIATED-PRE-MATCH — **0 blocking**. Still
  specification-only; no code/schema/commit/sibling access; pending review.
- Stage 1D.1 **corrected** the cryptographic/reporting contract: Step-0 and the config
  signature exchange are **keyed authentication with a pre-supplied key** (SOURCE-
  REQUIRED; HMAC-SHA256 default = PROJECT-CONTRACT, JDEC-013) — **not** unkeyed SHA-256
  digests and **not** invented PKI; the emailed result is **self-contained** (FastMCP +
  cryptographically-signed hardware declarations, K3); the reporting-sanction conflict
  (Ch 9 vs App E #35) is recorded as **C-09** with the strictest 0-both rule. Registers:
  NDEC-001…007, JDEC-001…013, INV-01…15. The crypto taxonomy is kept precise
  (HASH ≠ MAC ≠ PKI signature ≠ mutual acknowledgement); **no key material** in any
  artifact. Specification-only; no code/schema/commit/sibling access; pending review.
