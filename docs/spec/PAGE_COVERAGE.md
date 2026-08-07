# Page-Coverage Ledger — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. Approved baseline (input to Stage 1C).**

Accounts for **all 160 PDF pages** of `.project-spec/police_thief_p2p.pdf`
(v3.0.0, SHA-256 `7c9e1d…dd02e`). Body-to-PDF offset is **+16** (book page N ≈
PDF N+16); roman front matter = PDF 1–16. Extraction tool: `pdftotext -enc UTF-8`
(+ `-layout`), `pdfinfo` (page count = 160). Hebrew RTL; English technical terms
and code listings cross-checked. No PDF page is omitted.

Legend — Status: **REVIEWED** = read and accounted; **REVIEW REQUIRED** = a
critical passage needs re-extraction. Requirement domains use the prefixes in
`REQUIREMENT_CATALOG.md`.

| PDF pp. | Book pp. | Chapter / Appendix | Section headings | Read status | Requirements found | Numeric code-names (App F links) | Conflict candidates | JSON material | Submission material | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | i | Title page | Title (He/En), author, © , **version 3.0.0** | REVIEWED | version identity (INFORMATIONAL) | — | — | — | — | REVIEWED |
| 2 | ii | Front — Abstract (תקציר) | project overview | REVIEWED | INFORMATIONAL scope | — | — | mentions 4 JSON docs, 2 GitHub repos | 2 repos, signed JSON | REVIEWED |
| 3 | iii | Front — Personal word | why strict rules | REVIEWED | INFORMATIONAL | — | — | — | — | REVIEWED |
| 4 | iv | Front — Clarification (הבהרה) | **binding-vs-illustrative default**; code-name key | REVIEWED | ARCH/authority meta-rules | intro to App F code-names | — | — | — | REVIEWED |
| 5 | v | Front — General guidelines | **academic-freedom-on-conflict**; book structure (11 ch, 6 app) | REVIEWED | authority meta-rules; conflict handling | App F = sole numeric authority | conflict-handling rule | — | — | REVIEWED |
| 6–11 | vi–xi | Table of Contents | full chapter/appendix map | REVIEWED | — (navigation) | — | — | lists App B config, 4 JSON | App C submission | REVIEWED |
| 12 | xii | List of Figures | figures 1–13 | REVIEWED | — | — | — | — | — | REVIEWED |
| 13–16 | xiii–xvi | List of Figures/Tables (cont.) | figure/table indexes | REVIEWED | — (navigation) | — | — | — | — | REVIEWED |
| 17–23 | 1–7 | **Ch 1** Theoretical framework (Dec-POMDP) | 1.1 goals; 1.2 single→orchestration; 1.3 Dec-POMDP; 1.4 uncertainty; 1.5 summary | REVIEWED | INFORMATIONAL (partial observation → underlies local-truth GAME/GUI rules) | — | — | — | README §1 (Dec-POMDP model) | REVIEWED |
| 24–32 | 8–16 | **Ch 2** P2P architecture & FastMCP | 2.1 goals; 2.2 full decentralization; 2.3 MCP+LLM; 2.4 tunneling & env separation; 2.5 summary | REVIEWED | ARCH, NET, STRAT (server/client symmetry; @mcp.tool; tunneling; process/config separation) | — | example board `10×10` vs App F `7×7` (INFORMATIONAL) | — | 2 repos rationale | REVIEWED |
| 33–39 | 17–23 | **Ch 3** Physics, board, scoring | 3.2 discrete space/contract; 3.3 board & start; 3.4 movement, barriers; 3.5 win conditions & scoring; 3.6 summary | REVIEWED | GAME, BAR (movement, no diagonals, barrier rule, capture, scoring table) | board size, start pos, barrier quota, step ceiling, survival threshold, scoring | example `5×5`/`10×10` vs App F `7×7` | config physics fields | — | REVIEWED |
| 40–47 | 24–31 | **Ch 4** Dynamic pheromones | 4.2 indirect coordination; 4.3 emission & decay; 4.4 scent-map tactics; 4.5 summary (+ pre-series scent lock) | REVIEWED | SCENT, CRYPTO (emission/decay formula; scent model crypto-lock before series) | scent center 0.9, decay 0.10, field 5×5 | — | scent params in config | — | REVIEWED |
| 48–56 | 32–40 | **Ch 5** Cryptographic security & zero-knowledge | 5.2 temptation; 5.3 Commit-Reveal/SHA-256/Nonce; 5.4 mutual audit; 5.5 Step-0 & fairness; 5.6 summary | REVIEWED | CRYPTO, STATE, PERF, GIT (4-step protocol, canonical JSON, Step-0 hardware+commit hash, token lock) | — | code example canonical serialization | log/declaration JSON fields; `github_commit`, tokens | commit-hash per game | REVIEWED |
| 57–68 | 41–52 | **Ch 6** Strategy module & decision | 6.2 why separate; 6.3 RL optional; 6.4 Manhattan/belief; 6.5 LLM prompt-engineering; 6.6 summary | REVIEWED | STRAT, LLM (LLM never decides moves; 3 equal policies; 4 bluff modes; agreed-LLM-move exception) | word limit 15, game arena, token estimate | example belief map `10×10` vs App F `7×7` | — | — | REVIEWED |
| 69–76 | 53–60 | **Ch 7** GUI & Replay simulator | 7.2 live vs retrospective; 7.3 live GUI heatmap/turn banner; 7.4 Replay Viewer & integrity; 7.5 verification engine; 7.6 summary | REVIEWED | GUI, REPLAY (local-truth heatmap; Replay Viewer mandatory; Verified OK / TAMPERED→disqualify) | — | log JSON verified per step | Replay/GUI screenshots required | REVIEWED |
| 77–84 | 61–68 | **Ch 8** Agent architecture & reliability | 8.2 separation of concerns; 8.3 Orchestrator & state machine; 8.4 Deadline Tracker & Watchdog; 8.5 summary | REVIEWED | STATE, ARCH (single-gateway orchestrator; legal-only state machine; deadline tracker; watchdog) | response timeout, watchdog threshold | — | — | — | REVIEWED |
| 85–98 | 69–82 | **Ch 9** League, fairness, reporting | 9.2 league structure/tie; 9.3 Gmail automation/Gatekeeper/token-bucket; 9.3.3 signed JSON report; 9.4 GitHub submission/two repos; 9.5 summary | REVIEWED | LEAGUE, NET, REPORT, JSON, GIT, SUB, SEC (Gatekeeper trio, token bucket, 4 JSON docs, two repos, 429) | games/series, diversity reward, min/max games, RPM, concurrent, backoff, retries, queue, timeouts | **all four JSON docs' semantics** | two repos, cross-link, 2+4 links, README | REVIEWED |
| 99–106 | 83–90 | **Ch 10** Recommended dev priorities | 10.2 build in layers; 10.3 seven PRD stages; 10.4 milestones; 10.5 summary | REVIEWED | DOC, SUB (SHOULD: 7-PRD layered build; milestones) | — | — | — | PRD/PLAN/TODO files (via Ch 9/App E) | REVIEWED |
| 107–115 | 91–99 | **Ch 11** Summary & outlook | 11.2 arc; 11.3 systems not coding; 11.4 four success metrics; 11.5 final checklist; 11.6 outlook | REVIEWED | DOC, SUB (4 success metrics; final pre-submission checklist; self-score code-quality-only) | min games to pass | — | JSON report reaffirmed | Moodle per-member, 8-char group id, PDF form, self-score | REVIEWED |
| 116–119 | 100–103 | References | bibliography [1]–[34] | REVIEWED | INFORMATIONAL (citations only) | — | — | — | — | REVIEWED |
| 120–125 | 104–109 | **Appendix A** Gmail API & OAuth 2.0 | A.1 five setup steps; A.2 access vs refresh token; A.3 send-only flow; A.4 required files | REVIEWED | REPORT, SEC (gmail.send least-privilege; credentials.json+token.json secret; .gitignore mandatory; rotate on leak) | — | — | — | secret handling for submission | REVIEWED |
| 126–132 | 110–116 | **Appendix B** Unified config file | B.1 why shared constitution; B.2 JSON vs TOML; B.3 signed shared `config/game.json`; B.4 private `config/game.toml` | REVIEWED | JSON, ARCH, CRYPTO (config schema; byte-identical; JSON overlay wins TOML; canonical config_sha256) | **all config fields ↔ App F** | **config JSON + private TOML full structure** | config attached to repo | REVIEWED |
| 133–137 | 117–121 | **Appendix C** GitHub submission & academic report | C.1 repo/branches/tagging; C.2 README academic report; C.3 submission checklist (Table 6) | REVIEWED | GIT, SUB, SEC, DOC (annotated tag; README; .gitignore; no secrets; Table 6 checklist) | — | result JSON emailed | **full submission checklist** | REVIEWED |
| 138–141 | 122–125 | **Appendix D** Example code repo | D.1 what it shows; D.2 layout; D.3 how to run; D.4 usage terms | REVIEWED | INFORMATIONAL (non-binding); educational-license; book prevails over repo | — | — | — | non-binding reference | REVIEWED |
| 142–150 | 126–134 | **Appendix E** Mandatory rules mapping | Tables 7–12 (arch/spatial/crypto/strategy/league/additions), **entries 1–55** | REVIEWED | **ALL domains** — 55 numbered MUST/MUST NOT/recommendation with sanctions | cross-refs to App F | — | JSON report rules (33,34) | tag, README, Moodle, group-id (41–45) | REVIEWED |
| 151–160 | 135–143 | **Appendix F** Mandatory parameter table | Tables 13–22; status defs; mandatory rules; file variables; LLM modes; strategy selection; "end of book" | REVIEWED | binding numeric values + file naming + addresses + LLM/strategy selection | **every quantitative value** | 4 JSON file variables & naming | example repo, lecturer addresses | REVIEWED |

## Coverage summary

- **PDF pages accounted for: 160 / 160.** No gap.
- **Chapters 1–11:** all REVIEWED.
- **Appendices A–F:** all REVIEWED.
- **REVIEW REQUIRED pages/sections: none** at the requirement level. Residual note: figures rendered as scattered numeric labels in text extraction (e.g., token-bucket plot PDF p.91, belief-map PDF p.64, scent field PDF p.44) were read for their captions/semantics, not pixel values; binding values come from Appendix F regardless.
- Front-matter pages (1–16), References (116–119) and Appendix D (138–141) carry **no mandatory requirement** but are accounted with an explicit status, as required.
