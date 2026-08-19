# Versioning Audit — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

## Every `schema_version` occurrence in the book

| Location | Text | Class | Binding? |
|---|---|---|---|
| App B `config/game.json` example (PDF p.129) | `"schema_version": "1.2"` | key SOURCE-EXPLICIT (appears in the printed example); value EXAMPLE-ONLY | **No** — the value `1.2` is illustrative |
| App B `config/game.toml` example (PDF p.131) | `version = "1.10"` | EXAMPLE-ONLY (private TOML, not a JSON contract) | No |
| Title page / book identity (PDF p.1) | "book version 3.0.0 / example-code version 3.0.0" | document identity, not a JSON field | n/a |

## Findings

- The **key** `schema_version` is source-explicit (it appears in the App B config
  example), but the book **binds no specific value** and **defines no compatibility
  rules** for it.
- Therefore `1.2` is **not mandatory**. We do **not** claim `1.2` is required.

## Project-contract versioning convention (JDEC-003)

Minimal convention only:
- Each JSON artifact **may** carry a `schema_version` string identifying this
  project's contract revision (e.g., `"mars777-1"`).
- It is **informational**, not a negotiated term; it does not alter any Appendix F
  value and is not part of the physics agreement.
- Compatibility policy: additive changes bump the suffix; the field is **optional**
  and its absence is not an error (the book mandates no version handshake).

This is **PROJECT-CONTRACT**, not lecturer-specified. See
`PROJECT_CONTRACT_DECISIONS.md` JDEC-003.

## Stage 1D correction

Because `schema_version` sits **inside the signed `config/game.json`** (App B
structure), its **value affects `config_sha256`** ⇒ both peers must carry an
**identical** value for byte-identity. It is therefore **NEGOTIATED-PRE-MATCH**
(NDEC-004, default `"mars777-1"`), not a unilateral optional field. The
**declaration** `schema_version` was **removed** (REMOVE-REDUNDANT, D4) — it is not
source-required and would enlarge the Step-0 **keyed-authentication** payload
(`"step0" ‖ core`) for no benefit (K1; NDEC-005).

## Stage 9A-1B1F — local support, added

The two facts above describe what the value *means* between peers. A third was
missing: what this **build** can represent.

- `SUPPORTED_CONFIG_SCHEMA_VERSIONS` in `domain/config_schema.py` names every
  revision this code can run — today exactly `"mars777-1"`, the JDEC-003 value.
- `NegotiatedConfig` refuses any other revision at construction, so an
  unsupported configuration is not a value this code produces, from any source.
- This is **local support**, not a negotiated term and not a peer contract. The
  negotiated semantics recorded above are unchanged, `config_sha256` is
  unchanged, and no wire field was added.
- Two peers agreeing on an unsupported revision still cannot run it: agreement
  is byte-identity, compatibility is representability, and the guideline's
  startup-validation clause asks for the second.
