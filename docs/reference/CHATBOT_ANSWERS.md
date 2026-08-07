# Chatbot Answer Register — group MaRs-777

# STATUS: CHATBOT REVIEW COMPLETE — ZERO QUESTIONS PENDING

**No answer was fabricated.** Q1–Q5 and Q9–Q10 were resolved by **source extraction**
supplied by the user from the lecturer's second chatbot (recorded verbatim in
`ATTACHMENT_EVIDENCE.md` as AE-01…AE-04, evidence level
**CHATBOT-SOURCE-EXTRACTION**) combined with our own **primary-PDF** re-reads.
Q6–Q8 were resolved directly from the **primary PDF**, which made further questions
unnecessary. **No further chatbot questions are required.**

## Authority policy for chatbot answers (unchanged)

1. A chatbot answer is **clarification evidence — NOT permission to override an
   explicit binding book rule.** Authority order: book → Appendix E → Appendix F →
   locked Stage-1 decisions → reference repository → chatbot → our engineering choices.
2. **Exact extracted text is preserved verbatim** (`ATTACHMENT_EVIDENCE.md`).
3. **Interpretation is recorded separately** from the quoted text.
4. **Conflicts with the book are flagged**, never silently absorbed.
5. **No code or architecture change is automatic**; changes require supervising review.
6. Chatbot-extracted text is **never** called independently verified primary evidence —
   we did not open the attachment bytes.

## Register

| Question ID | Question | Chatbot Answer / Evidence | Answer Date | Source / Link | Classification | Book Conflict? | Architecture Impact | Accepted Decision |
|---|---|---|---|---|---|---|---|---|
| **Q1** | Role alternation across a counted six-sub-game series? | **AE-01 (verbatim):** "Roles (cop/thief) switch across the sub-games, so no role and no sub_game_number appear here." Appears inside the example `_schema`, not as a MUST. | 2026-08-07 | `1-pre-game-declaration.txt` via chatbot (user-supplied) | **REFERENCE-ONLY / ATTACHED-EXAMPLE-CONVENTION** — PDF exhaustively silent | **No** | Series orchestration only; `SeriesLauncher` selects which independent role process runs each sub-game | **Support alternation at orchestration level. No new MUST. Two independent role repos retained; no role duplication.** |
| **Q2** | Are the reference FastMCP tool names required? | No extraction claims they are mandatory; PDF names no tools. | 2026-08-07 | PDF (silent) + reference repo | **REFERENCE-ONLY** | **No** | PRD-02/05; stays behind `PeerTransportPort`/`PeerServerPort` | **Keep `negotiate`/`receive_turn`/`submit_audit`/`receive_control` as compatibility defaults; not book-mandated.** |
| **Q3** | Is the commitment construction / sealed field set fixed? | No extraction fixes it; PDF requires a canonical sealed record + SHA-256 recompute. | 2026-08-07 | PDF Ch 5 §5.3–5.4 | **NEGOTIABLE-BETWEEN-TEAMS** | **No** | PRD-06; future `CommitmentCodec` | **Keep the locked 8-field contract (nonce inside canonical payload). Reference framing only via a negotiated codec.** |
| **Q4** | Step-0: HMAC, asymmetric, or plain SHA-256? | **AE-02 (verbatim):** `"signature": "ed25519:base64-signed-blob"` — Ed25519 appears **in the example**. PDF: "signed using a **pre-supplied key** … cannot be forged retroactively"; **no algorithm named**. | 2026-08-07 | `1-pre-game-declaration.txt`; PDF Ch 5 p.55–56 | **CLARIFIES-AMBIGUITY** (mechanism is producer authentication; algorithm open) | **No** | PRD-06; `AuthProfile` | **`AuthProfile` = HMAC_SHA256 (project default) or ED25519 (attachment-compatibility). Plain unkeyed SHA-256 does NOT satisfy strict Step-0 producer authentication. No crypto dependency added yet.** |
| **Q5** | Signed-config authentication primitive? | No extraction fixes it. PDF App B p.128 requires a pre-game signature exchange but names no algorithm; the explicit "pre-supplied key" wording belongs to **Step-0**, not config. | 2026-08-07 | PDF App B p.128 | **CLARIFIES-AMBIGUITY** | **No** | PRD-06 | **Byte-identity + auth-exchange semantic = SOURCE-REQUIRED; exact primitive = SOURCE-UNSPECIFIED. HMAC-SHA256 default; Ed25519 negotiable. Do not transfer Step-0's explicit key wording onto config.** |
| **Q6** | Parser-exact result schema? | Resolved from **primary PDF**: App F §3 calls the four attachments **examples**; AE-03 is internally inconsistent with Table 20 on log filenames. | 2026-08-07 | PDF App F §3; Table 20; AE-03 | **ATTACHED-SCHEMA-EXAMPLE — not a verified parser schema** | **No** | PRD-07; `ResultProfile` | **Source-complete equivalent structures acceptable; align with the attachment shape where safe (LECTURER_ATTACHMENT_COMPATIBILITY) but never declare it a 1:1 schema.** |
| **Q7** | Extra non-secret result fields tolerated? | PDF states the **mandatory** fields ("include…"), implying a floor rather than a closed set. | 2026-08-07 | PDF Ch 9 p.79 | **CLARIFIES-AMBIGUITY** | **No** | PRD-07 | **Strict profile emits the minimal mandatory surface; compatibility profile may add attachment-shaped fields. No debug/presentation extras in strict mode.** |
| **Q8** | Is `g01`…`g06` required? | PDF writes `g<NN>` without a width. | 2026-08-07 | PDF App F Tbl 20 / §2.3 | **CLARIFIES-AMBIGUITY** | **No** | PRD-07 | **Keep JDEC-004 `g01`…`g06` as a project convention; not relabelled SOURCE-MANDATORY.** |
| **Q9** | Is `pheromone_min_center_intensity` binding? | Absent from Appendix F **and** from the reported attachment; present only in the reference repo. | 2026-08-07 | PDF App F Tbl 16; AE-04 scope | **REFERENCE-ONLY** | **No** | PRD-01/06 | **Not a binding parameter. Compatibility adapter may recognise it; it may never alter the three binding pheromone values.** |
| **Q10** | May the signed config contain `_note` keys? | **AE-04:** exactly two (`_note`, `world._note`); the reference repo has three (adds `_axis_note`, `_hint_max_words_note`) — the examples **disagree with each other**. No rule extracted. | 2026-08-07 | `2-agreed-config.txt`; reference repo | **ATTACHED-EXAMPLE-CONVENTION** | **No** | PRD-06 | **Strict emitted config excludes `_note`. Compatibility parser may accept explicitly negotiated metadata keys; if present in a hashed config they participate in canonical bytes and both peers must hold identical values. Not added to the binding FIELD_MATRIX.** |

## Outcome

**Zero questions pending. Zero book conflicts found.** One project-contract correction
followed (result static-metadata placement, F-4 in `STAGE1_CLARIFICATION_IMPACT.md`);
everything else was a convention, a compatibility option, or already resolved by the
primary PDF.
