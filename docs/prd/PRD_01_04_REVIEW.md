# PRD-01…04 Red-Team Review — group MaRs-777

**Status: STAGE 2B — adversarial review of the four drafted PRDs.**
All **BLOCKING** findings are resolved below; nothing blocking remains open.

Severity: **BLOCKING** (must resolve before PASS) · **HIGH** · **MEDIUM** · **LOW**.

| # | Severity | PRD | Issue | Resolution | Status |
|---|---|---|---|---|---|
| **B-01** | BLOCKING | 01 | **Score ordering could be reversed** (cop/thief swapped), a silent scoring defect. | PRD01-FR-070 mandates a **role-keyed** structure, never a positional pair; PRD01-AC-009 fails on a reversed mapping. | **RESOLVED** |
| **B-02** | BLOCKING | 01 | **`technical_loss` falsely attributed to Appendix F.** | PRD01-FR-074 states 0/0 with provenance **Ch 3 Table 2 + App E #48**, explicitly *not* an Appendix-F row; AC-010 asserts the provenance. | **RESOLVED** |
| **B-03** | BLOCKING | 01/02 | **Hard-coded NEGOTIABLE values** (30 s, 60 s, 35, 14, 7) would break negotiation. | Every numeric is read from the locked config with its Appendix-F status (PRD01-FR-001/060/075/090-092; PRD02-FR-051/052/053). AC PRD02-AC-007 uses a **45 s** config to prove no hard-coded 30. | **RESOLVED** |
| **B-04** | BLOCKING | 01/03 | **Strategy could see opponent truth** if `Observation` grew a field. | PRD01-FR-021/023 forbid the field existing; PRD03 §11 lists forbidden inputs; PRD03-AC-001 is a contract test that fails if such a field is added. | **RESOLVED** |
| **B-05** | BLOCKING | 02 | **Hidden central referee** — an orchestrator holding both peers' truth. | PRD02-FR-012 (SeriesLauncher owns no truth, not a referee), FR-071 (Gatekeeper decides protocol validity only), PRD01-FR-055 (capture by deterministic evaluation on both peers). AC PRD02-AC-018 asserts no truth accessor. | **RESOLVED** |
| **B-06** | BLOCKING | 02 | **Concurrent mutation of one turn** — indistinguishable from cheating. | PRD02-FR-041/043/044: single serialized executor + turn-cursor guard + idempotency; AC PRD02-AC-006. | **RESOLVED** |
| **B-07** | BLOCKING | 04 | **LLM becoming mandatory** — game validity depending on a provider. | PRD04-FR-030/041/042: T0 always available and able to complete a full series; degradation ladder; AC PRD04-AC-001 runs a whole series with the advisor disabled. | **RESOLVED** |
| **B-08** | BLOCKING | 03/04 | **LLM bypassing the validator.** | PRD04-FR-034/035 (every output validated, no privileged path) + PRD03-FR-042 + GAME-009; AC PRD04-AC-007. | **RESOLVED** |
| **B-09** | BLOCKING | 04 | **Dual truth from `verdict` + `intent`** if the reference's both-keys payload were accepted naively. | PRD04-FR-017/018: sealed record carries **`intent` only**; a peer `verdict` maps to it; **disagreement ⇒ malformed, rejected**. AC PRD04-AC-009/010. | **RESOLVED** |
| **B-10** | BLOCKING | all | **Reference/example conventions promoted to SOURCE-MUST.** | Role alternation (PRD02-FR-011), FastMCP tool names (PRD02-FR-034), Ed25519, `_note`, `pheromone_min_center_intensity` (PRD01-FR-044, PRD04-FR-006), reference commitment codec — each labelled REFERENCE-COMPATIBILITY / attachment convention, never source-required. | **RESOLVED** |
| **B-11** | BLOCKING | 03 | **Thief baseline could walk into a dead end**, losing by GAME-005. | PRD03-FR-015 mobility guard + FR-016 escape-room preservation + FR-017 corner penalty; AC PRD03-AC-021/022. | **RESOLVED** |
| **B-12** | BLOCKING | all | **Acceptance criteria requiring the public internet** would make CI meaningless. | PRD02-NFR-001 and PRD04-NFR-004 require offline execution with fake peer/advisor; every AC in 01–04 is offline-runnable. | **RESOLVED** |
| **B-13** | BLOCKING | all | **Windows/Linux nondeterminism** (hash randomisation, set order, locale). | PRD01-FR-043/§21, PRD03-FR-034, PRD04-FR-013/050: canonical sorting, integer arithmetic, NFC normalisation, no hash-order dependence; cross-OS ACs (PRD01-AC-015, PRD03-AC-003, PRD04-AC-013). | **RESOLVED** |
| **H-01** | HIGH | 01/04 | **Duplicated scent ownership** (physics vs interpretation). | Crosswalk §1/§4: PRD-01 owns physics, PRD-04 owns interpretation and is explicitly forbidden from recomputing it (PRD04-FR-001); AC PRD04-AC-011 asserts byte-identical physics. | **RESOLVED** |
| **H-02** | HIGH | 01/03 | **Duplicated belief ownership.** | PRD-01 owns the type/authority; PRD-03 keeps a derived working copy that may never be promoted to truth (PRD01-FR-022; PRD03 §15). | **RESOLVED** |
| **H-03** | HIGH | 01/03 | **Duplicated legality logic** — strategy re-implementing rules would drift. | PRD03-FR-010 requires the *same* deterministic rules; §16 keeps the validator authoritative; AC PRD03-AC-005. | **RESOLVED** |
| **H-04** | HIGH | 01 | **Police/Thief semantic divergence** — two different rulebooks. | Crosswalk §3 + PRD-01 §5.3: only action space and scoring perspective differ; the rest is semantically identical and deployed from one source. | **RESOLVED** |
| **H-05** | HIGH | 03 | **Vague "good" baseline** — untestable quality claim. | Replaced with measurable NFR-004: strictly beats a uniform-random legal policy over **≥200 seeded sub-games**; AC PRD03-AC-016/028. | **RESOLVED** |
| **H-06** | HIGH | 03 | **Plain-Manhattan pursuit oscillating against a barrier wall.** | PRD03-FR-014 mandates **barrier-aware BFS distance**; Manhattan only as a tie-break; AC PRD03-AC-012 fails a Manhattan-only implementation. | **RESOLVED** |
| **H-07** | HIGH | 04 | **Numeric-position hint encoding** would violate LLM-003 while looking like "natural language". | PRD04-FR-011 requires a deterministic pre-send detector; FR-014 replaces the hint; AC PRD04-AC-003. | **RESOLVED** |
| **H-08** | HIGH | 04 | **Prompt injection via peer hint text.** | PRD04-FR-019/037: peer text is data, sanitized and bounded, never instruction; AC PRD04-AC-016 (T-016). | **RESOLVED** |
| **H-09** | HIGH | 02 | **Secret leakage through error strings or metric labels.** | PRD02-FR-070 (only `key_id`/alg/verdict) + AC PRD02-AC-017 scan; PRD04-FR-048 for prompts. | **RESOLVED** |
| **H-10** | HIGH | 02 | **Compatibility profile weakening STRICT mid-series.** | PRD02-FR-080/081: selected pre-play, **frozen at `CONFIG_LOCKED`**, weakening ⇒ refuse counted play; AC PRD02-AC-014. | **RESOLVED** |
| **M-01** | MEDIUM | 01 | Requirements without provenance. | Every FR table row carries a *Traces to* column citing a source ID, JDEC/NDEC/INV/C, or an architecture section. Audit result: **0 unexplained**. | **RESOLVED** |
| **M-02** | MEDIUM | all | Banned vague words ("robust", "efficient", "proper"). | Scanned; remaining uses are paired with measurable criteria (latency targets, counts, ordered ladders). | **RESOLVED** |
| **M-03** | MEDIUM | 03 | **Idle STAY** wasting turns. | Anti-passivity requirements PRD03-FR-016 (police) / FR-019 (thief); ACs PRD03-AC-015 / AC-026. | **RESOLVED** |
| **M-04** | MEDIUM | 03 | Nondeterministic tie-breaking. | Total documented tie-break orders (PRD03-FR-033 both roles); property test PRD03-T-010/T-011. | **RESOLVED** |
| **M-05** | MEDIUM | 04 | Token budget overrun. | PRD04-FR-046 degrades T1→T0 before the budget is exceeded; AC PRD04-AC-015. | **RESOLVED** |
| **M-06** | MEDIUM | 02 | Private `turn_timeout` (reference 180 s) mistaken for the negotiated deadline. | PRD02-FR-056 explicitly separates them (C-02). | **RESOLVED** |
| **M-07** | MEDIUM | 01 | Capture asserted by a peer rather than evaluated. | PRD01-FR-055: deterministic evaluation on both peers; a claim inconsistent with validated state is rejected (CRYPTO-004/005). | **RESOLVED** |
| **L-01** | LOW | 02 | FastMCP signatures still unfixed. | Deliberate (PRD02-FR-035); resolved in Stage 2C with the negotiated profile. | **ACCEPTED** |
| **L-02** | LOW | 04 | Provider/SDK unchosen. | Deliberate (PRD04-FR-038); T0 must work regardless. | **ACCEPTED** |
| **L-03** | LOW | all | PRDs could be read as "implementation complete". | Every PRD's §2 status is **DRAFT COMPLETE — AWAITING SUPERVISING REVIEW**, and §29 marks implementation **not started**. | **RESOLVED** |

## Summary

**13 BLOCKING findings — all RESOLVED.** 10 HIGH resolved · 7 MEDIUM resolved ·
2 LOW deliberately accepted (both are scheduled deferrals, not defects).
**No blocking issue remains open.**

## Provenance audit result

Every Functional Requirement in PRD-01…04 carries an explicit *Traces to* entry
(source requirement ID, JDEC/NDEC/INV/C, or architecture document section).
**Unexplained requirements: 0.**

## Compatibility-discipline audit result

| Item | Stated as | Anywhere claimed SOURCE-MUST? |
|---|---|---|
| Role alternation | REFERENCE/ATTACHMENT convention, orchestration-only, default off | **No** |
| FastMCP tool names | REFERENCE-COMPATIBILITY DEFAULT | **No** |
| Ed25519 | attachment-example `AuthProfile` option | **No** |
| HMAC-SHA256 | PROJECT default (JDEC-013) | **No** |
| `pheromone_min_center_intensity` | REFERENCE-ONLY, cannot alter results | **No** |
| `_note` keys | example/compatibility metadata | **No** |
| `g01…g06` | PROJECT convention (JDEC-004) | **No** |
| Reference commitment codec | negotiated `CommitmentCodec` only | **No** |

**STRICT_COUNTED_MATCH cannot be weakened by any profile** (PRD02-FR-081).
