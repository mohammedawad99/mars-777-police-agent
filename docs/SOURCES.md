# Sources & Source-of-Truth - group MaRs-777

**Status: DRAFT (foundation).**

## Authoritative document

- **Title:** Distributed Police-Thief Peer-to-Peer - Project Book
- **Version:** 3.0.0
- **Pages:** 160
- **Expected SHA-256:** `7c9e1d7527582c3aef9afd71709981cea50ea60b8fabefe85efccab0a5fdd02e`
- **Local (git-ignored) copy:** `.project-spec/police_thief_p2p.pdf`
- **Parent source:** `../references/police_thief_p2p.pdf`

The local copy under `.project-spec/` must have the **same SHA-256** as the
parent source. It is a static, ignored, read-only reference - never runtime
state, never committed.

## Source hierarchy

1. Book v3.0.0.
2. Appendix E - mandatory rules, prohibitions, sanctions, recommendations.
3. Appendix F - mandatory numeric parameters and status definitions.
4. Moodle instructions from the lecturer.
5. Professional software-submission guidelines.
6. Example simulator - non-binding reference only.

## Warning

**No rule, numeric value, status, or JSON schema may be reconstructed from
memory.** Every such element is extracted from the book with a page/section
citation.

## Extraction status (Stage 1A)

The full 160-page extraction **has** been performed (specification-only, no
implementation) and lives under `docs/spec/`:

- `AUTHORITY_RULES.md` - reading conventions, hierarchy, citation format.
- `PAGE_COVERAGE.md` - all 160 PDF pages accounted for.
- `REQUIREMENT_CATALOG.md` - 79 source-cited requirements across 18 domains.
- `APPENDIX_E_CROSSWALK.md` - all 55 mandatory entries mapped.
- `APPENDIX_F_NUMERIC_INVENTORY.md` - every binding numeric value.
- `HIGH_RISK_REQUIREMENTS.md` - compliance-risk audit.
- `JSON_SOURCE_MAP.md` - sources for the four JSON docs (no schema yet; Stage 1C).

Plus expanded `../CONFLICT_REGISTER.md` and `../REQUIREMENTS_TRACEABILITY.md`.
All of it was independently cross-audited (Stage 1B) and **accepted by supervising
review (PASS)** as the approved specification baseline. Numeric values are governed
by **Appendix F**; the four JSON contracts were built and reviewed in
**Stage 1C/1D/1D.1** (now **LOCKED**) with their field/key/nesting details resolved.
