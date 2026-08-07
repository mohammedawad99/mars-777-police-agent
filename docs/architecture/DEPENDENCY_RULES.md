# Dependency Rules — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

## 1. Layers (dependencies point inward only)

```
        infrastructure   (FastMCP, files, clock, Gmail, GUI, LLM, metrics)
              │  implements ports, may import protocol + app.ports + domain
              ▼
        protocol / adapters   (canonical bytes, commitment, keyed auth, messages)
              │  may import domain
              ▼
        application / orchestration   (state machine, orchestrator, turn service, ports)
              │  may import domain
              ▼
        domain   (board, rules, scoring, scent, barriers, truth, belief)
                 imports NOTHING from outer layers
```

**Rule D1 — inward only.** An inner layer never imports an outer layer.
**Rule D2 — no cycles.** The import graph is a DAG. Any cycle is an architecture defect.
**Rule D3 — ports, not adapters.** Application depends on **abstract ports**; concrete
adapters are injected at composition time (a single wiring module in `infra`).
**Rule D4 — one composition root.** Exactly one place constructs concrete adapters.

## 2. Mandated decoupling (from the design principles)

| Requirement | Rule |
|---|---|
| Strategy must not couple to networking/crypto/persistence/GUI/Gmail/parsing | **Strategy imports only `app.strategy_api` + `domain` value types.** It receives an `Observation` and returns a `ProposedAction`. It has no transport, no file, no clock, no key material. |
| GUI consumes projections/events, not internals | **GUI subscribes to emitted view events.** It never imports `domain.truth` or holds a reference to a mutable aggregate. |
| Replay consumes persisted evidence, not live state | **`infra.replay` imports `infra.artifacts` + `protocol.commitment` only.** Importing `app` or `domain` live state from replay is forbidden — replay must be able to run in a fresh process against files alone. |
| Reporting consumes finalized artifacts, not mutable state | **`infra.reporter` reads sealed artifacts.** It has no write path into domain/app. |
| No shared runtime state between repos | **No import may cross the package roots** `mars777_police` ↔ `mars777_thief`. |

## 3. Explicitly forbidden couplings

| Forbidden | Why |
|---|---|
| `domain` → `infra` / `protocol` / `app` | Breaks purity, determinism, and unit-testability |
| `app` → concrete adapter class | Breaks substitutability and offline testing |
| strategy → `infra.mcp_client` / `infra.reporter` / `protocol.commitment` | Strategy could leak, cheat, or forge (STRATEGY_ARCHITECTURE §4) |
| strategy → nonce/hash material | Commitment integrity must not be strategy-influenced |
| `infra.gui` → `domain.truth` / belief internals | Private-truth leak risk (GUI-001/002) |
| `infra.replay` → `app` / live `domain` | Replay would no longer be independent evidence (REPLAY-001/002) |
| `infra.reporter` → domain mutation | A report must never change a score |
| `infra.llm` → `domain.rules` bypass | Every LLM output must pass the validator (LLM-001) |
| any module → sibling repository package | Role isolation (ARCH-001/002, TB-3) |
| circular imports anywhere | Rule D2 |

## 4. Enforcement plan (future, not implemented)

- An **import-linter / dependency test** in CI asserting the layer matrix and the
  forbidden list above (planned in `TEST_ARCHITECTURE.md` → CONTRACT layer).
- `ruff` isort/banned-import rules for the sibling package root.
- A **composition-root test** asserting `domain` has zero outward imports.
- Coverage of the forbidden list is itself a Repository-Gate criterion.
