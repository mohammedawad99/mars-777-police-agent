# PRD-05…07 Red-Team Review — group MaRs-777

**Status: STAGE 2C — adversarial review of PRD-05, PRD-06 and PRD-07.**
All **BLOCKING** and **HIGH** findings are resolved, or explicitly demonstrated to be a
legitimate later external gate.

Severity: **BLOCKING** · **HIGH** · **MEDIUM** · **LOW**.

| # | Severity | PRD | Issue | Resolution | Status |
|---|---|---|---|---|---|
| **C-01** | BLOCKING | 05 | **Localhost accidentally accepted for a counted match** — the single easiest way to invalidate a whole league game. | PRD05-FR-002/004 reject loopback/private endpoints (`E-NET-NOT-PUBLIC`); PRD05-FR-020 makes a healthy local process explicitly insufficient; AC-001/AC-002. | **RESOLVED** |
| **C-02** | BLOCKING | 05 | **Stale public endpoint** — playing against a URL that no longer serves the participating process. | PRD05-FR-013 staleness check per `game_uid`/sub-game; FR-015 re-advertise + acknowledge; FR-043 post-switch staleness; AC-004/AC-005/AC-008. | **RESOLVED** |
| **C-03** | BLOCKING | 05 | **Silent series-convention disagreement** — one peer assuming fixed roles, the other alternation. Stage-2B's "default off" wording permitted exactly this. | Convention is now an **explicit pre-series agreement** with **no silent default**: unset ⇒ `E-NET-CONVENTION-UNSET`, mismatch ⇒ `E-NET-CONVENTION-MISMATCH`, neither value wins; recorded and frozen at lock. PRD05-FR-030…035; AC-011/AC-012. PRD-02 FR-011 updated to point at this rule. | **RESOLVED** |
| **C-04** | BLOCKING | 05 | **Provider credential leak** into config/artifacts/logs/Git. | PRD05-FR-050…053: env-only, never serialized, git-ignored, rotation required, no token-like values in docs/tests; AC-009. | **RESOLVED** |
| **C-05** | BLOCKING | 05/06 | **Network failure misread as cryptographic failure** (or vice-versa) — would produce false TAMPERED or false "retry the auth". | PRD05-FR-060…066 keeps the taxonomies **disjoint**; FR-064 forbids retrying integrity errors; FR-065 forbids cross-labelling; AC-006. | **RESOLVED** |
| **C-06** | BLOCKING | 06 | **Unkeyed `SHA256(terms‖nonce)` accepted as strict Step-0 authentication** — the exact defect the reference implementation exhibits. | PRD06-FR-022 explicitly rejects it; FR-021 requires keyed producer auth; FR-028 forbids silent downgrade; AC-002 is a dedicated rejection test. | **RESOLVED** |
| **C-07** | BLOCKING | 06 | **HMAC called a digital signature** (or Ed25519 called a MAC) — terminology drift that hides a real security difference. | Taxonomy table §8 defines all seven terms; PRD06-FR-024 mandates correct usage in code/docs/logs; **AC-022 + T-025 are a terminology lint**. | **RESOLVED** |
| **C-08** | BLOCKING | 06 | **`config_sha256` conflated with authentication** — hash equality treated as proof of authorship. | PRD06-FR-041 separates four artefacts; **FR-044: equality alone is NOT authentication**; INV-15 requires both; AC-006 proves refusal when the hash matches but the tag fails. | **RESOLVED** |
| **C-09** | BLOCKING | 06 | **Nonce reuse** — destroys the binding property of commit-reveal. | PRD06-FR-063 fresh CSPRNG nonce per commitment; **FR-064 reuse detected and rejected**; AC-010, T-011. | **RESOLVED** |
| **C-10** | BLOCKING | 06 | **Early nonce disclosure** — reveals the move before it is due. | PRD06-FR-065 secret until final audit, absent from every message/log/GUI/report/metric/prompt; AC-011 scan; PRD07-FR-122 restricts nonces to the final-audit log section. | **RESOLVED** |
| **C-11** | BLOCKING | 06 | **Profile downgrade** — peer offering weaker crypto after agreement. | PRD06-FR-048 freezes profiles at lock; FR-124 rejects downgrade attempts; FR-123 forbids any profile that weakens strict mode; AC-015. | **RESOLVED** |
| **C-12** | BLOCKING | 06 | **Result-hash self-reference** — hashing bytes that contain the hash is undefined and forgeable. | PRD06-FR-142/143 exclude the digest and agreement state from the core; **AC-017 + T-022 are an explicit non-self-reference regression guard**. | **RESOLVED** |
| **C-13** | BLOCKING | 06 | **Reference commitment codec promoted to source-MUST.** | PRD06-FR-120/121: the reference codec is REFERENCE-COMPATIBILITY, available only by explicit mutual agreement; strict project codec is the default. | **RESOLVED** |
| **C-14** | BLOCKING | 07 | **GUI leaks opponent truth** — breaks the entire information model. | PRD07-FR-003/004 forbid it; **FR-009 makes the GUI event schema a whitelist**, so adding such a field is a build/test failure; AC-002. | **RESOLVED** |
| **C-15** | BLOCKING | 07 | **GUI becomes authoritative** (mutates state, or its failure stops play). | PRD07-FR-007 no write path; FR-008 lossy channel, failure never halts the game; AC-004/AC-005. | **RESOLVED** |
| **C-16** | BLOCKING | 07 | **Replay depends on live state** — verification would be circular and worthless. | PRD07-FR-021 artifacts-only, fresh process, no network; AC-010/AC-013 (dependency test). | **RESOLVED** |
| **C-17** | BLOCKING | 07 | **Duplicate crypto implementation in replay** — two implementations drift and one will be wrong. | PRD07-FR-025 requires calling PRD-06 interfaces; **PRD06-NFR-005 permits exactly one implementation**; AC-013. | **RESOLVED** |
| **C-18** | BLOCKING | 07 | **Incorrect artifact filename** — grader cannot locate/join evidence. | PRD07-FR-040 exact Table-20 names; FR-041 `g01…g06`; **FR-087 official filenames always beat the attachment example**; AC-020; T-009. | **RESOLVED** |
| **C-19** | BLOCKING | 07 | **Result duplicating or omitting the wrong fields.** | PRD07-FR-080 mandatory set; FR-081 no declaration-owned duplication; FR-082 minimal surface; AC-023/AC-025. | **RESOLVED** |
| **C-20** | BLOCKING | 07 | **Exact played commit missing or inferred** ("latest main"). | PRD07-FR-100/101 require capture from the running checkout and **forbid branch inference**; AC-024; INV-05 join. | **RESOLVED** |
| **C-21** | BLOCKING | 07 | **Gmail recipient typo** — silently unreported game. | PRD07-FR-141 exact constant `rmisegal+uoh26finalgame@gmail.com`, validated by a constant test; AC-030; T-016. | **RESOLVED** |
| **C-22** | BLOCKING | 07 | **Plaintext report instead of a JSON attachment** — rejected report, lost league points. | PRD07-FR-142/143: JSON attachment named `result_<game_id>.json`; plaintext/prose forbidden and rejected **before** sending; AC-031/AC-032/AC-033. | **RESOLVED** |
| **C-23** | BLOCKING | 07 | **OAuth secret committed or logged.** | PRD07-FR-145 (local, git-ignored, never logged/attached), FR-150 sanitized errors, PRD06-FR-161/162; AC-034; T-023. | **RESOLVED** |
| **C-24** | BLOCKING | 07 | **Reporting failure mutating game history.** | PRD07-FR-170 delivery status separate from game result; FR-171/172 reporter is read-only w.r.t. history; AC-038. | **RESOLVED** |
| **C-25** | BLOCKING | 07 | **C-09 softened** — treating a missing/contradictory report as a per-side inconvenience. | PRD07-FR-191/192 apply the **stricter** locked resolution (missing from either side **or** contradictory ⇒ credit invalidated); FR-193 forbids silent reconciliation; AC-039. | **RESOLVED** |
| **C-26** | BLOCKING | 05/07 | **Actual Gmail / public internet required in normal CI** — would make CI unrunnable and unreliable. | PRD05-NFR-002/003 and PRD07-NFR-003 keep the full suites offline with fakes; **real tunnel (PRD05-T-015) and real Gmail (PRD07-T-025) are explicitly deferred MANUAL/E2E gates**; AC PRD05-AC-016 / PRD07-AC-035. | **RESOLVED — legitimate external gate** |
| **C-27** | BLOCKING | 06/07 | **Windows/Linux canonicalization drift** — different bytes ⇒ mutual false TAMPERED. | PRD06-FR-009 golden-vector byte equality; FR-003/004/006 (NFC, LF, number form); PRD07-FR-046 artifacts use PRD-06 bytes; AC PRD06-AC-019, PRD07-AC-014; CI on both OSes. | **RESOLVED** |
| **H-01** | HIGH | 05 | Readiness probe used to **bypass Step-0 auth**. | PRD05-FR-024 forbids it; AC-015 tests the bypass attempt. | **RESOLVED** |
| **H-02** | HIGH | 05 | One-way reachability accepted as READY. | PRD05-FR-022 requires **bidirectional** proof; AC-003. | **RESOLVED** |
| **H-03** | HIGH | 05 | Provider lock-in making the architecture ngrok-specific. | PRD05-FR-005 provider-neutral port; NFR-005 no provider identifiers outside one adapter; AC-013 adapter swap. | **RESOLVED** |
| **H-04** | HIGH | 05 | Tunnel exposure granting access to internal state/filesystem/strategy. | PRD05-FR-071 limits reachability to the declared FastMCP surface; FR-070 routes all inbound through Gatekeeper + PRD-06. | **RESOLVED** |
| **H-05** | HIGH | 06 | Post-lock mutation of binding terms/profiles/convention. | PRD06-FR-048/049 enumerate what becomes immutable and make a change attempt a defect/rejection. | **RESOLVED** |
| **H-06** | HIGH | 06 | Cross-object tag replay (Step-0 tag reused as config tag). | PRD06-FR-023/043 authenticate `context ∈ {"step0","config"}` **with** the payload (domain separation). | **RESOLVED** |
| **H-07** | HIGH | 06 | Duplicate/stale commitment replacing an original. | PRD06-FR-086 rejects rather than overwrites; AC-013; T-018. | **RESOLVED** |
| **H-08** | HIGH | 06 | Overstated memory-erasure guarantee for keys. | PRD06-FR-165 states best-effort clearing and **explicitly disclaims** guaranteed erasure in Python — an honest limitation rather than a false claim. | **RESOLVED** |
| **H-09** | HIGH | 06 | Adding a crypto dependency prematurely (e.g. for Ed25519). | PRD06-NFR-003: strict mode uses only the standard library; Ed25519 would require a justified dependency and is **not adopted now**. | **RESOLVED** |
| **H-10** | HIGH | 07 | Rendering error masking or altering a verification verdict. | PRD07-FR-027 makes the verdict evidence-driven and headless-available; AC-015. | **RESOLVED** |
| **H-11** | HIGH | 07 | Mail-send loop / quota abuse. | PRD07-FR-146 token bucket (NET-002), FR-147 DOS detector/circuit breaker (SEC-001), FR-148 429 back-off (REPORT-003), FR-149 idempotency-aware attempts; AC-037. | **RESOLVED** |
| **H-12** | HIGH | 07 | Over-broad Gmail scope. | PRD07-FR-144 exactly `gmail.send`, send-only (SEC-002/SEC-006); AC-036. | **RESOLVED** |
| **H-13** | HIGH | 07 | Half-written artifact after a crash breaking replay. | PRD07-FR-045 atomic temp→fsync→rename; FR-125 failure-safe log persistence; AC-027. | **RESOLVED** |
| **H-14** | HIGH | 07 | Orphan artifact accepted as counted evidence. | PRD07-FR-064 rejects artifacts whose identity does not join; AC-022. | **RESOLVED** |
| **H-15** | HIGH | 07 | Attachment example treated as a binding 1:1 schema. | PRD07-FR-087 states it is not a verified parser schema and official filenames win; crosswalk §4. | **RESOLVED** |
| **M-01** | MEDIUM | 05 | Readiness window presented as an Appendix-F value. | PRD05-NFR-001 and crosswalk §5 mark 60 s a **local setting, explicitly not Appendix F**. | **RESOLVED** |
| **M-02** | MEDIUM | 05 | Uncounted warm-ups blurring into counted play. | PRD05-FR-007 permits non-public warm-ups but requires them to be **recorded as uncounted** (LEAGUE-005). | **RESOLVED** |
| **M-03** | MEDIUM | 06 | Nonce length claimed as sourced. | PRD06-FR-066 declares 16 bytes a **PROJECT default, not sourced**. | **RESOLVED** |
| **M-04** | MEDIUM | 06 | C-07/C-08/C-09 merged into a generic "tamper" concept. | PRD06-FR-106 keeps them distinct and assigns C-09 to PRD-07. | **RESOLVED** |
| **M-05** | MEDIUM | 07 | League bookkeeping (min 2 different opponents, one counted per opponent, max 10) unowned. | PRD07-FR-088/089 own LEAGUE-001/003/004/005/007 with truthful declaration; T-024. | **RESOLVED** |
| **M-06** | MEDIUM | 07 | Screenshots treated as authoritative. | PRD07-FR-211 states they are supporting evidence only. | **RESOLVED** |
| **L-01** | LOW | 05 | Tunnel provider not chosen. | Deliberate (open decision); provider-neutral design makes the choice reversible. | **ACCEPTED** |
| **L-02** | LOW | 07 | GUI toolkit not chosen. | Deliberate; must not influence the projection contract. | **ACCEPTED** |

## Summary

**27 BLOCKING — all resolved** (one, C-26, resolved *by design* as a legitimate deferred
external gate rather than a CI requirement). **15 HIGH — all resolved.** 6 MEDIUM
resolved. 2 LOW deliberately accepted as open design choices.

**No BLOCKING or HIGH finding remains open.**

## Provenance audit result

Every Functional Requirement in PRD-05, PRD-06 and PRD-07 carries an explicit
**Provenance** column drawn from the approved vocabulary (SOURCE-MANDATORY /
SOURCE-PROHIBITED / SOURCE-RECOMMENDED / SOURCE-PERMITTED / PROJECT-CONTRACT /
NEGOTIATED-PRE-MATCH / REFERENCE-COMPATIBILITY / ATTACHMENT-COMPATIBILITY /
ARCHITECTURE-CONSTRAINT), or a concrete source ID, JDEC/NDEC/INV/C reference, or named
architecture section. **Unexplained requirements: 0. No source requirement ID was invented.**
