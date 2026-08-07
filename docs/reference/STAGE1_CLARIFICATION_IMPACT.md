# Stage-1 Clarification Impact — group MaRs-777

**Status: STAGE 2A-R2 — audit of whether the newly available evidence requires any
correction to the locked Stage-1 specification.**

**Hard boundary honoured:** no MUST/MUST NOT was changed, no Appendix-E/F content was
changed, no numeric value, no official filename, no C-07/C-08/C-09, no `num_games`, no
commit-reveal mandatory semantic, and the Step-0 pre-supplied-key requirement was **not**
removed. Only **project-contract representation** and **provenance precision** were
touched.

## Findings

| # | Topic | Evidence | Classification | Action |
|---|---|---|---|---|
| **F-1** | **Role alternation** | AE-01 (attachment example) + reference `role_for()`; **PDF silent** (exhaustive search) | **NO-CHANGE** | No Stage-1 edit. No new MUST. Requirement count stays **91**. Recorded as ATTACHED-EXAMPLE-CONVENTION + REFERENCE-COMPATIBILITY-CONVENTION + PROJECT-SUPPORTED-BEHAVIOR; architecture supports it at series-orchestration level only |
| **F-2** | **Ed25519** | AE-02 example field `"ed25519:base64-signed-blob"`; PDF names no algorithm | **PROVENANCE-CORRECTION** (note only) | Added to `SIGNATURE_AND_HASH_PROVENANCE.md` as an **attachment-example mechanism** and an `AuthProfile` option. **Not** marked SOURCE-MANDATORY. JDEC-013 (HMAC-SHA256 default) unchanged |
| **F-3** | **Config `_note` keys** | AE-04 (2 keys) vs reference (3 keys) — they disagree; no rule extracted | **NO-CHANGE** | Not added to the binding FIELD_MATRIX. Strict emitter excludes them; compatibility parser may accept negotiated metadata keys |
| **F-4** | **Result duplicating static declaration metadata** | AE-03 + **PDF Ch 9 p.78 four-file list**, **Ch 9 p.79 mandatory report fields**, **App F Table 20** | **PROJECT-CONTRACT-CORRECTION** | **Applied — see below.** Stage-1D.1's K3 over-read §9.3.3 |
| **F-5** | **Config-auth exact primitive** | PDF App B p.128 (signature exchange, no algorithm); Ch 5 p.55–56 is the *explicit* pre-supplied-key wording | **PROVENANCE-CORRECTION** | Clarified that Step-0's explicit "pre-supplied key" wording is **not** transferred verbatim onto the less specific config wording. Config: byte-identity + auth-exchange semantic = SOURCE-REQUIRED; **exact primitive = SOURCE-UNSPECIFIED**; HMAC-SHA256 = project default; Ed25519 = negotiable option |
| **F-6** | **Attachments are examples** | PDF App F §3 verbatim: "ארבעה קובצי JSON **לדוגמה**" | **PROVENANCE-CORRECTION** (note) | Recorded in `ATTACHMENT_EVIDENCE.md`; no contract change |
| **F-7** | **`<NN>` format** | No new evidence | **NO-CHANGE** | JDEC-004 `g01`…`g06` retained as **project convention**, not relabelled SOURCE-MANDATORY |
| **F-8** | **`pheromone_min_center_intensity`** | Reference only; absent from Appendix F **and** from the reported attachment | **NO-CHANGE** | Stays REFERENCE-ONLY. Not a binding parameter |
| **F-9** | **FastMCP tool names** | Reference only | **NO-CHANGE** | Compatibility defaults; application stays behind `PeerTransportPort` / `PeerServerPort` |
| **F-10** | **Commitment codec** | Reference differs (nonce outside payload) | **NO-CHANGE** | Locked 8-field semantic contract retained; reference framing only via a future negotiated `CommitmentCodec` |

## The one applied Stage-1 correction (F-4)

**What was wrong.** Stage-1D.1 finding **K3** concluded that the emailed
`result_<game_id>.json` must itself carry FastMCP endpoints, full hardware declarations
and `hardware_auth`, on the strength of §9.3.3 (p.77) which lists those items among the
report's contents.

**Why it was wrong.** Re-reading the primary PDF directly:

- **Ch 9 p.78 (four-file list)** assigns to the **DECLARATION** *"all the constant data
  of the whole game … the police and thief repository addresses, **the MCP server
  addresses, the hardware specifications**, the language model, the agreed token cap,
  and the start/end times"*.
- **Ch 9 p.78** describes the **RESULT** as *"the final results report … per-sub-game
  scores and the cumulative result, for league-score weighting"*.
- **Ch 9 p.79** states the **mandatory report fields**: *"the GitHub links of both
  groups, the commit identifier of each sub-game, and the total tokens consumed"*.
- **App F Table 20** independently splits the roles the same way and is explicitly
  *"a reference table only … not negotiable"*.

§9.3.3 describes the **information scope of the reporting package**; Table 20 and the
four-file list define **physical placement**. AE-03 (secondary) agrees with placement in
the declaration. Duplicating declaration-owned static metadata into the result was
therefore a **project-contract over-read**, not a book requirement.

**What changed (representation only):**

| Item | Before | After |
|---|---|---|
| Result self-containment | RESULT-FILE self-containment | **FOUR-ARTIFACT-SET self-containment** |
| Result rows in FIELD_MATRIX | 13 | **11** |
| Grand total | 77 | **75** |
| Removed result rows | `teams.<g>.mcp_endpoint`, `teams.<g>.hardware`, `teams.<g>.hardware_auth` | declaration-owned; referenced |
| Added result row | — | `declaration_ref` join (**JDEC-014**) |
| INV-10 | "verify from the result alone" | **corrected** to four-artifact-set self-containment |
| INV-12 / INV-13 | asserted these live in the result | **retargeted** to the declaration |
| JDEC register | 001–013 | **001–014** |

**What did NOT change:** requirement count **91** (76/9/4/2) · Appendix E **55**
(45/9/1) · Appendix F **32** (14/9/9) · `num_games` **6/FIXED** · C-07 · C-08 · C-09 ·
the four official filenames · commit-reveal semantics · Step-0 keyed-authentication
requirement · INV-01…09, 11, 14, 15 · NDEC-001…007 · declaration and config field sets.

**Files edited (both repos, symmetrically):** `docs/spec/json/RESULT_CONTRACT.md`,
`docs/spec/json/FIELD_MATRIX.md`, `docs/spec/json/CROSS_ARTIFACT_INVARIANTS.md`,
`docs/spec/json/PROJECT_CONTRACT_DECISIONS.md` (JDEC-014),
`docs/spec/json/STAGE_1D_AUDIT.md` (counts + K3 superseding note).

## Why no other Stage-1 change was necessary

Every remaining finding is either (a) the book being **silent**, in which case a
project convention or compatibility profile is the correct home and a new MUST would be
an invention; or (b) an **example** (attachment or reference) that the PDF itself
labels non-binding. Promoting either into the locked specification would violate the
authority order and inflate the binding requirement set — so it was not done.
