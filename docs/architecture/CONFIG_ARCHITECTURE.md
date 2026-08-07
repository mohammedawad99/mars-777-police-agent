# Configuration Architecture — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only. No configuration implemented.**

## 1. Four strictly separated configuration kinds

| # | Kind | Example content | Shared with opponent? | In Git? | Authority |
|---|---|---|---|---|---|
| **1** | **Binding negotiated game config** | Appendix B keys: board, world, movement/barriers, scoring, pheromones, network/league, rate-limiter | **Yes — byte-identical, hashed and keyed-authenticated** | Yes (per counted game, distinct filename) | **Appendix F** (sole numeric authority) |
| **2** | **Local application/runtime settings** | tunnel URL, bind host/port, log level, GUI on/off, artifact dir, strategy seed | No | Yes (defaults only, non-sensitive) | Local operator |
| **3** | **Secrets** | pre-shared keyed-auth key, Gmail credential, LLM API key | **Never** | **Never** | Environment only |
| **4** | **Development/test settings** | fake peer address, deterministic clock, fixture seeds | No | Yes (test scope) | Test harness |

## 2. Hard rules

- **R1** Binding config (kind 1) contains **only** the Appendix B keys. No project field
  may be added — it would break byte-identity (D4 minimalism, JDEC-010).
- **R2** Local config (kind 2) **must not silently alter binding rules.** If a local
  setting would change a game rule, it is rejected at start-up as a defect, not applied.
- **R3** **Secrets never enter game JSON**, logs, docs, e-mail, error text, or Git. Only
  the non-secret `key_id` is ever serialized (JDEC-013, SEC-003/004).
- **R4** Environment-specific endpoints (tunnel URL, mail settings) stay local; the
  *published* FastMCP endpoint appears in declaration/result but **carries no secret**.
- **R5** Appendix-F status semantics are enforced by a **future validator**:
  **FIXED** — reject any deviation; **MINIMUM** — accept only ≥ floor (raising is the
  "harder direction"); **NEGOTIABLE** — any mutually agreed value. Defaults are the
  Appendix F values (floor for MINIMUM).
- **R6** `num_games` for a counted series is **6 / FIXED**; the Appendix B illustrative
  `1` is never used for a counted game (C-05, closed).
- **R7** `technical_loss` is a real config key with binding value **0/0** whose numeric
  provenance is Ch 3 + App E #48, **not** Appendix F (C-07). No App F row may be invented.
- **R8** After `CONFIG_LOCKED`, the binding config is **immutable** for that sub-game.

### Comment/metadata keys in the signed config (Stage 2A-R2)

The attachment example carries `_note` and `world._note`; the reference repo carries
three such keys. They **disagree**, which shows the keys are presentational.
**Strict emitted config excludes them.** A compatibility parser may accept explicitly
negotiated metadata keys, but if such a key is present in a **hashed** config it
participates in the canonical bytes and **both peers must hold identical values**. Such
keys may **never** alter Appendix-F semantics and are **not** binding FIELD_MATRIX fields.
`pheromone_min_center_intensity` is likewise **REFERENCE-ONLY** and never binding.

## 3. Precedence (highest wins) — for **local** settings only

```
1. explicit CLI argument
2. environment variable
3. local settings file (git-ignored for anything sensitive)
4. committed non-sensitive defaults
5. built-in fallback default
```

**Precedence does not apply to binding game config.** Kind 1 has exactly one source:
the negotiated, hashed, authenticated, locked artifact. There is no override chain —
an attempt to override it is `E-LOCAL-DEFECT`.

**Secrets precedence:** environment only. If a required secret is missing, the process
**refuses to start a counted match** rather than degrading (fail closed).

## 4. Validation order at start-up (future)

1. Load kind 2/3/4 (local, secrets, test) → structural validation.
2. Refuse start if a required secret is absent.
3. Negotiate kind 1 → validate every value against Appendix F status.
4. Canonicalize → `config_sha256` → keyed auth tag → exchange → verify → **lock**.
5. Only then may the state machine leave `CONFIG_LOCKED`.

## 5. What is explicitly NOT decided here

- Concrete file format/paths for kind 2 (Stage 2B/2C).
- CLI flag names.
- Any secret storage mechanism beyond "environment, never persisted".
