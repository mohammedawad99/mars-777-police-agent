# LLM Boundary — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only. No provider or SDK chosen.**

## 1. Default posture

- **Movement is algorithmic. Always.** Movement legality and movement selection default
  to deterministic code (LLM-001 SHOULD / E-25; GAME-003). **Legality is never delegated
  to an LLM** — that is a hard rule of this project, not a preference.
- **The LLM's primary legitimate role is language**: producing and interpreting bounded
  natural-language hints, including deliberate bluffs whose truth/lie status is recorded
  in `intent` (LLM-002/003/004).

## 2. The three tiers

| Tier | Use | Authority | Condition |
|---|---|---|---|
| **T0 — none** | Fully deterministic play, template hints | Full | Always available; **zero-token fallback** |
| **T1 — language assistance** | Hint generation/interpretation, bluff phrasing | **Advisory only** | Default when tokens/budget allow |
| **T2 — tactical suggestion** | Move *suggestion* | **Advisory only** | **Only** under the locked, documented **mutual-agreement exception** (LLM-005 MAY); otherwise forbidden |

T2 is never enabled unilaterally. Without a signed, documented mutual agreement the
architecture behaves as if T2 does not exist.

## 3. Mandatory validation gate

```
   LlmAdvisorPort ──► suggestion ──► domain.rules (deterministic validator)
                                          │ reject ──► deterministic fallback
                                          ▼ accept
                                   ProposedAction → normal turn pipeline
```

**No LLM output ever reaches game state without passing the same validator that governs
any other proposal.** There is no privileged path (`DEPENDENCY_RULES.md` forbids
`infra.llm → domain.rules` bypass). A malicious, hallucinated, or malformed suggestion
is simply rejected.

## 4. Fallback and budget

- **Zero-token operation must remain viable at all times**: provider outage, budget
  exhaustion, rate-limit, timeout, or offline CI all degrade to T0 with no protocol
  impact (`E-LLM-UNAVAILABLE` is non-fatal).
- Token consumption is metered and reported (`tokens`, `total_tokens`) — it feeds
  computational-fairness scoring (PERF-001/002, E-54).
- A token budget per series is a negotiated config value (`token_budget_per_series`,
  NEGOTIABLE). Approaching the cap degrades T1→T0 rather than overrunning.
- Decisions are **time-boxed**: an advisor that misses its budget is abandoned, not awaited.

## 5. Privacy and safety constraints

- Prompts may contain **only** data the strategy itself may legally see
  (`Observation`-derived). Never: nonces, key material, credentials, opponent forbidden
  truth, or raw artifacts.
- LLM provider is an **untrusted advisor** across TB-4; its output is data, never code,
  never a command.
- Provider responses are never logged verbatim if they could contain injected content
  that mimics protocol messages; only bounded, sanitized summaries plus token metrics.
- No LLM call is on the critical path of integrity verification.

## 6. Deliberately deferred

- Provider, model, and SDK selection (no dependency added at Stage 2A).
- Prompt templates and hint-quality tuning (Stage 2B/2C, PRD-04).
- Whether T2 is ever enabled — requires a documented mutual agreement first.
