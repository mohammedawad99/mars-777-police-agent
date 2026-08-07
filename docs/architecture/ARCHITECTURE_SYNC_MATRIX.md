# Architecture Sync Matrix — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — classification of every architecture document.**

Both repositories are **independent**. Where the design is genuinely common, the two
copies are kept **byte-identical** so the shared contract cannot drift. Where role
behaviour legitimately differs, the difference is **explicit and intentional** — byte
equality is never forced at the cost of hiding a real role difference.

Classifications:
- **COMMON-EXACT** — byte-identical in both repositories.
- **COMMON-WITH-ROLE-SECTIONS** — same document, containing both roles' sections, with a
  small adapted header stating which role *this* repository implements.
- **ROLE-SPECIFIC** — content necessarily differs (package root, role obligations).

| Document | Classification | Police-specific content | Thief-specific content |
|---|---|---|---|
| `SYSTEM_ARCHITECTURE.md` | **COMMON-EXACT** | none | none |
| `DEPENDENCY_RULES.md` | **COMMON-EXACT** | none | none |
| `STATE_OWNERSHIP.md` | **COMMON-EXACT** | none | none |
| `STATE_MACHINE.md` | **COMMON-EXACT** | none | none |
| `ERROR_MODEL.md` | **COMMON-EXACT** | none | none |
| `API_BOUNDARIES.md` | **COMMON-EXACT** | none | none |
| `DATA_FLOW.md` | **COMMON-EXACT** | none | none |
| `CONCURRENCY_MODEL.md` | **COMMON-EXACT** | none | none |
| `CONFIG_ARCHITECTURE.md` | **COMMON-EXACT** | none | none |
| `ARTIFACT_LIFECYCLE.md` | **COMMON-EXACT** | none | none |
| `LLM_BOUNDARY.md` | **COMMON-EXACT** | none | none |
| `OBSERVABILITY.md` | **COMMON-EXACT** | none | none |
| `TEST_ARCHITECTURE.md` | **COMMON-EXACT** | none | none |
| `SECURITY_ARCHITECTURE.md` | **COMMON-EXACT** | none | none |
| `QUALITY_GATES.md` | **COMMON-EXACT** | none | none |
| `ARCHITECTURE_TRACEABILITY.md` | **COMMON-EXACT** | none (POLICE-scoped rows retained in both) | none |
| `ARCHITECTURE_REVIEW.md` | **COMMON-EXACT** | none | none |
| `ARCHITECTURE_SYNC_MATRIX.md` | **COMMON-EXACT** | none | none |
| `ROLE_RESPONSIBILITIES.md` | **COMMON-WITH-ROLE-SECTIONS** | header states this repo is **POLICE**; §4 POLICE obligations are *this agent's*; barrier declaration/quota/capture-by-barrier and the "never falsely declare a capture" prohibition are owned here | header states this repo is **THIEF**; §4 THIEF obligations are *this agent's*; survival horizon, scent emission, hint/`intent` honesty are owned here. Both sections appear in both copies (the opponent's obligations must be understood and validated) |
| `STRATEGY_ARCHITECTURE.md` | **COMMON-WITH-ROLE-SECTIONS** | title/§7 mark POLICE as this repository's strategy: belief tracking, scent inference, interception, choke-point/barrier planning, capture-by-barrier | title/§7 mark THIEF as this repository's strategy: escape-risk, police/barrier prediction, exit preservation, trap avoidance, scent deception |
| `../reference/LECTURER_REFERENCE_AUDIT.md` | **COMMON-EXACT** | none | none |
| `../reference/REFERENCE_ARCHITECTURE_DELTA.md` | **COMMON-EXACT** | none | none |
| `../reference/CHATBOT_QUESTION_PACK.md` | **COMMON-EXACT** | none | none |
| `../reference/CHATBOT_ANSWERS.md` | **COMMON-EXACT** | none | none |
| `../reference/ATTACHMENT_EVIDENCE.md` | **COMMON-EXACT** | none | none |
| `../reference/COMPATIBILITY_PROFILES.md` | **COMMON-EXACT** | none | none |
| `../reference/STAGE1_CLARIFICATION_IMPACT.md` | **COMMON-EXACT** | none | none |
| `MODULE_BOUNDARIES.md` | **ROLE-SPECIFIC** | package root **`mars777_police`** throughout | package root **`mars777_thief`** throughout |
| `../prd/PRD-01…07` (blueprints) | **ROLE-SPECIFIC** | titled POLICE; role-scoped requirement emphasis | titled THIEF; role-scoped requirement emphasis |

## Summary

| Classification | Count (architecture docs) |
|---|---|
| COMMON-EXACT | **25** (18 architecture + 7 reference) |
| COMMON-WITH-ROLE-SECTIONS | **2** |
| ROLE-SPECIFIC | **1** (+ 7 PRD blueprints per repo) |
| **Total documents per repo** | **28** (21 architecture + 7 reference) |

## Drift-control rule

The 25 COMMON-EXACT documents must remain **byte-identical** across the two
repositories. Any future change to one must be mirrored to the other in the same
reviewed stage, exactly as the Stage-1 specification was. A divergence in a
COMMON-EXACT document is an architecture defect, not a role difference.
