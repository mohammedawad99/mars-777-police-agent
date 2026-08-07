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
  baseline is approved for Stage 1C (not started).
