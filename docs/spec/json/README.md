# JSON Contract Index — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED.
SPECIFICATION-CONTRACT only — no JSON files, schemas, serializers, or code.**

Source of truth: book v3.0.0 (`.project-spec/police_thief_p2p.pdf`, SHA-256
`7c9e1d…dd02e`). This directory specifies **contracts** for the four mandatory
JSON artifacts before any code is written. It builds on the reviewed Stage 1A/1B
baseline at HEAD `2113e68`.

## The four official artifacts (names are fixed — never rename)

| # | Filename | Scope | Producer | Consumer / verifier | Byte-identical on both peers? |
|---|---|---|---|---|---|
| 1 | `declaration_<game_id>.json` | per **game** (all sub-games) | each team (agreed) | opponent + lecturer; anchors Step-0 fairness | content agreed; each team sends its own |
| 2 | `config_<game_id>_g<NN>.json` | per **sub-game** | negotiated by both teams | both agents (enforce physics) + Replay | **YES — byte-identical, crypto-locked** |
| 3 | `log_<game_id>_g<NN>.json` | per **sub-game** | each agent (own moves) | opponent + Replay Viewer (audit) | not identical (each logs its side); mutually reconstructable |
| 4 | `result_<game_id>.json` | per **game** (series) | **each** team separately | lecturer (league scoring) | each team sends its own; results must **agree** |

Source: Appendix F Table 20 (PDF p.157) for the names; Chapter 9 §9.3.3 (PDF p.94–95)
for content; the four share a common **`game_uid`** and names derive from
**`game_id`** (+ `g<NN>` for the two per-sub-game files). **Both `game_uid` and
`game_id` are named by the book** (Ch 9 p.95) — SOURCE-EXPLICIT, not project
inventions (Stage 1D D3).

## Lifecycle / order (from the book)

```
        pre-game negotiation
                │
   ┌────────────┴─────────────┐
   ▼                          ▼
declaration_<game_id>.json   config_<game_id>_g<NN>.json
 (Step-0: hardware, model,    (agreed physics/scoring;
  commit hash, token cap,      byte-identical; crypto-locked
  identities, times)           per sub-game; App F values)
   │                          │
   └────────────┬─────────────┘
                ▼
       sub-game execution (per turn):
       Commit → Acknowledge → Reveal → (end-of-game) Audit
                │
                ▼
       log_<game_id>_g<NN>.json
       (per-turn commit/reveal record; nonce revealed at final audit)
                │
                ▼
       mutual log audit  ──►  Replay Viewer: Verified OK / TAMPERED
                │
                ▼  (both teams agree the result)
       result_<game_id>.json  (per-sub-game + cumulative scores,
                               4 GitHub links, commit hashes, tokens,
                               SHA-256 mutual approval)
                │
                ▼
       Gmail report (each team sends its own result JSON as an attachment)
```

Sequencing basis: Ch 3 §3.2 (config is the pre-agreed contract), Ch 5 §5.3–5.5
(Commit→Ack→Reveal→Audit; Step-0), Ch 7 §7.4 (replay), Ch 9 §9.2–9.4 (agree
result → each team emails its result JSON).

## Provenance classification (used in every contract doc)

| Class | Meaning |
|---|---|
| **SOURCE-EXPLICIT** | the book gives the exact JSON key/name or structural element |
| **SOURCE-SEMANTIC** | the book explicitly requires the information/meaning, but not an exact key/nesting |
| **PROJECT-CONTRACT** | the book leaves the representation open; this project fixes it (an engineering decision, recorded as a JDEC) |
| **EXAMPLE-ONLY** | key/value appears only in non-binding illustrative material |
| **REVIEW-REQUIRED** | source too ambiguous to choose a representation now without risking a spec violation |

Rules (per `AUTHORITY_RULES.md`): a **PROJECT-CONTRACT** field is **not** claimed
to be lecturer-specified; each cites the semantic source + the academic-freedom
basis + the reason for the choice (see `PROJECT_CONTRACT_DECISIONS.md`).
**Never** promote EXAMPLE-ONLY → SOURCE-EXPLICIT; **never** hide REVIEW-REQUIRED by
inventing a key.

## Cryptographic / replay / reporting relevance (summary)

- **config** — crypto-locked, canonically hashed (`config_sha256`); both peers byte-identical; replay verifies against it.
- **declaration** — Step-0 hardware+tokens+commit signed; anchors computational-fairness and reproducibility.
- **log** — per-turn Commit-Reveal record; the Replay Viewer recomputes SHA-256 per step (Verified OK / TAMPERED → disqualify).
- **result** — SHA-256-backed mutual approval; emailed to the lecturer as the binding league report.

## File-naming derivation (see `NAMING_AND_IDENTITY.md`)

Names derive from `game_id`; the two per-sub-game files add `g<NN>`. Exact
`game_id` format and `<NN>` zero-pad width are **not** specified by the book →
PROJECT-CONTRACT conventions (JDEC-004, JDEC-005).

## Compatibility / versioning policy (see `VERSIONING.md`)

The book prints a `schema_version` key in the App B example (value `"1.2"`) but
**binds no specific version**. Version value is EXAMPLE-ONLY; a minimal
PROJECT-CONTRACT versioning convention is defined (JDEC-003).

## Documents in this directory

`README.md` (this) · `NAMING_AND_IDENTITY.md` · `CONFIG_CONTRACT.md` ·
`DECLARATION_CONTRACT.md` · `LOG_CONTRACT.md` · `RESULT_CONTRACT.md` ·
`CANONICALIZATION_CONTRACT.md` · `VERSIONING.md` ·
`SIGNATURE_AND_HASH_PROVENANCE.md` · `PROJECT_CONTRACT_DECISIONS.md` (JDEC
register) · `FIELD_MATRIX.md` (master field matrix) · `CROSS_ARTIFACT_INVARIANTS.md`
· `ADVERSARIAL_REVIEW.md`.

**Stage 1D interoperability lock:** `PROTOCOL_TIMELINE.md` (when each field first
exists) · `INTEROPERABILITY_NEGOTIATION.md` (NDEC-001…006) ·
`INTEROPERABILITY_BLOCKERS.md` (former REVIEW-REQUIRED → resolved; **0 blocking**) ·
`STAGE_1D_AUDIT.md` (D1–D5, dependency classification, exact counts, JDEC/NDEC audit).
Final interoperability statuses: LOCKED-SOURCE / LOCKED-PROJECT /
NEGOTIATED-PRE-MATCH / LOCAL-ONLY / EXAMPLE-ONLY.

All example JSON lives **inside Markdown fences only**; no `.json`/`.jsonschema`
file is created anywhere.
