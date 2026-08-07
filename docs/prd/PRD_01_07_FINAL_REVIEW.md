# PRD-01…07 Final Phase-2 Review — group MaRs-777

**Status: STAGE 2-CLOSE — final adversarial audit of the complete seven-PRD set.**
All **BLOCKING** and **HIGH** findings are resolved. This review supersedes nothing:
`PRD_01_04_REVIEW.md` and `PRD_05_07_REVIEW.md` remain valid historical records of what
was found and fixed at their stages.

## 1. Closure findings resolved in this stage

| # | Severity | Issue | Resolution | Status |
|---|---|---|---|---|
| **F1** | **BLOCKING** | **Series convention secretly added to the declaration.** Stage-2C said the convention was *"recorded in the declaration"*, but the locked declaration contract has **16 fields and no convention/profile slot** — this would have been a hidden schema extension and a silent FIELD_MATRIX change. | Mechanically verified: **no such slot exists**. The convention is now **NEGOTIATED-PRE-MATCH protocol metadata** — proposed, echoed, mutually agreed, **authenticated as pre-series negotiation evidence**, frozen no later than `CONFIG_LOCKED`, recorded in the **negotiation record / profile evidence** (the same already-approved mechanism used for NDEC-001/002/003). **PRD05-FR-034/034a/034b** forbid representing it as a declaration field. **No field added, no JDEC created, matrix stays 75.** | **RESOLVED** |
| **F2** | **BLOCKING** | **Static declaration endpoint described as mutable.** Stage-2C allowed *"endpoint changes → re-advertise → continue"*, which contradicts the declaration's locked role as **static whole-series data**. | Cardinality verified: `teams.<g>.mcp_endpoint` is **1/team — a group-level ingress, not per role**. **PRD05-FR-015** now fixes it as a **stable group-level public ingress for the declared series**; **FR-015a** permits local bind/process/role changes behind it; **FR-015b** forbids silent declaration mutation and requires pause + recovery + an explicit re-negotiation / new declaration-game boundary if the ingress itself must change; **FR-015c** keeps it a transport failure with **no invented sanction**. | **RESOLVED** |

## 2. Global attack matrix

| # | Severity | Attack | Defence | Status |
|---|---|---|---|---|
| G-01 | BLOCKING | **Hidden artifact field** added to satisfy a PRD | F1 resolution; matrix re-verified **16/39/9/11 = 75** post-change | **RESOLVED** |
| G-02 | BLOCKING | Series convention in declaration | PRD05-FR-034a explicit prohibition | **RESOLVED** |
| G-03 | BLOCKING | Static endpoint treated as mutable | PRD05-FR-015/015a/015b | **RESOLVED** |
| G-04 | BLOCKING | Dynamic tunnel URL silently invalidating the declaration | PRD05-FR-015b: pause, recover, or re-negotiate — never silent continuation | **RESOLVED** |
| G-05 | BLOCKING | Role alternation requiring shared runtime | PRD05 §13.5a routing model: stable ingress → local routing → **separate processes**, no shared state, no cross-import (ARCH-001/002) | **RESOLVED** |
| G-06 | BLOCKING | Central router becoming a referee | PRD05 §13.5a + PRD05-FR-042 + PRD02-FR-012: ingress/launcher hold no game truth, validate nothing | **RESOLVED** |
| G-07 | HIGH | Stale endpoint after role switch | PRD05-FR-043: local route re-verified; different ingress governed by FR-015b | **RESOLVED** |
| G-08 | BLOCKING | Source example promoted to MUST | Compatibility audit §5: 10 items checked, none SOURCE-MANDATORY | **RESOLVED** |
| G-09 | HIGH | Local FR missing provenance | Mechanical scan: **0** FR rows with empty/dash provenance across all seven PRDs | **RESOLVED** |
| G-10 | HIGH | Duplicate local PRD ID | Mechanical scan: **0** duplicates across FR/NFR/AC/T in all seven PRDs | **RESOLVED** |
| G-11 | BLOCKING | Duplicate primary ownership | Crosswalk: **0** duplicates over 91 requirements | **RESOLVED** |
| G-12 | BLOCKING | Unmapped source requirement | **0** unmapped; 91/91 owned exactly once | **RESOLVED** |
| G-13 | BLOCKING | Hard-coded NEGOTIABLE value | Numeric audit: every binding value config-sourced with Appendix-F status; no bare 30/60 constant | **RESOLVED** |
| G-14 | BLOCKING | `technical_loss` attributed to Appendix F | PRD01-FR-074 / PRD07-FR-083: **0/0 via Ch 3 + App E #48, explicitly not an App F row** (C-07) | **RESOLVED** |
| G-15 | BLOCKING | **Nonce revealed during ordinary Reveal** | PRD06-FR-080: ordinary Reveal discloses **Move + Hint only**; **FR-065** keeps the nonce secret until **final audit**; PRD07-FR-122 restricts nonces to the final-audit log section | **RESOLVED** |
| G-16 | BLOCKING | Unkeyed Step-0 downgrade | PRD06-FR-021/022/028: keyed auth required, plain `SHA256(terms‖nonce)` rejected, **no silent downgrade** | **RESOLVED** |
| G-17 | BLOCKING | `config_sha256` conflated with authentication | PRD06-FR-041/044: four artefacts separated; equality alone is **not** authentication; INV-15 requires both | **RESOLVED** |
| G-18 | BLOCKING | Result hash self-reference | PRD06-FR-142/143 + AC-017 regression guard | **RESOLVED** |
| G-19 | BLOCKING | Live opponent-truth leak | PRD07-FR-003/004/009 whitelist schema; PRD01-FR-021 (no such field exists) | **RESOLVED** |
| G-20 | BLOCKING | Replay duplicating crypto | PRD07-FR-025 + PRD06-NFR-005: exactly one implementation | **RESOLVED** |
| G-21 | BLOCKING | Gmail recipient typo | PRD07-FR-141 constant + AC-030 test | **RESOLVED** |
| G-22 | BLOCKING | Plaintext report | PRD07-FR-142/143: JSON attachment only, plaintext rejected before send | **RESOLVED** |
| G-23 | BLOCKING | Secret leakage | PRD06-FR-161/162, PRD05-FR-051, PRD07-FR-145/150; scans across artifacts/logs/metrics/errors/prompts | **RESOLVED** |
| G-24 | HIGH | Real internet/Gmail required in CI | PRD05-NFR-002/003, PRD07-NFR-003: suites offline with fakes; real tunnel and real Gmail are **explicitly deferred manual E2E gates** | **RESOLVED — legitimate external gate** |
| G-25 | BLOCKING | PRD status claiming implementation | All seven PRDs state **Implementation status: NOT STARTED**; no PRD uses IMPLEMENTED/DONE | **RESOLVED** |

## 3. Result

**25 BLOCKING/HIGH attacks + 2 closure findings — all resolved.**
**No BLOCKING or HIGH finding remains open.** Two LOW items stay deliberately open as
design choices (tunnel provider, GUI toolkit), both reversible and neither affecting a
binding contract.

## 4. Artifact-contract integrity (post-closure)

| Check | Result |
|---|---|
| FIELD_MATRIX | **75** = declaration **16** / config **39** / log **9** / result **11** |
| Hidden field introduced by F1 or F2 | **NONE** |
| New JDEC created for PRD wording | **NONE** (register stays JDEC-001…014) |
| Official filenames | unchanged (four Table-20 names) |
| Registers | NDEC-001…007 · INV-01…15 · C-01…C-09 unchanged |
| Requirements | **91** (76/9/4/2) unchanged |

**Expected closure outcome achieved: NO Stage-1 contract change.**
