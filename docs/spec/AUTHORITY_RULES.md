# Source Authority Rules — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS; Stage-1 JSON contracts now
reviewed and LOCKED (Stage 1C/1D/1D.1). Implementation remains prohibited
(NOT STARTED).**

This document records the interpretation rules that govern how every other
Stage 1 specification artifact reads the authoritative book. It does not
introduce requirements; it fixes the reading conventions.

## Authoritative document

- **Title (Hebrew):** מֵרוֹץ שוֹטֵר–גַּנָּב מְבֻזָּר בְּרֶשֶׁת עֲמִיתִים
- **Title (English):** *Distributed Cops-and-Robbers over a Peer-to-Peer Network*
- **Course:** "Orchestration of AI Agents" (אורקסטרציה של סוכני AI), Dept. of Computer Science, University of Haifa.
- **Author / © :** Dr. Yoram Reuven Segal (ד"ר יורם ראובן סגל), 2026.
- **Book version:** **3.0.0** (example-code version 3.0.0) — stated on PDF p.1.
- **Pages:** 160 PDF pages (front matter i–xvi + body 1–99 + References 100–103 + Appendices A–F 104–143).
- **SHA-256:** `7c9e1d7527582c3aef9afd71709981cea50ea60b8fabefe85efccab0a5fdd02e`
- **Local (git-ignored) copy:** `.project-spec/police_thief_p2p.pdf`
- **Parent source:** `../references/police_thief_p2p.pdf`
- **Language:** Hebrew (RTL) with embedded English technical terms; code listings and shell comments are English-only.

## Authority hierarchy (highest first)

1. **Book v3.0.0** — the authoritative project specification.
2. **Appendix E** (PDF p.142–150 / book 126–134) — consolidated mapping of every mandatory rule, prohibition, and recommendation, with sanctions. 55 numbered entries in 6 tables (Tables 7–12).
3. **Appendix F** (PDF p.151–160 / book 135–143) — the mandatory parameter table; the **only** binding authority for quantitative values.
4. Moodle (מוֹדל) instructions from the lecturer (submission form, per-member submission).
5. Professional software-submission guidelines ("Recommendations for writing & submitting software with AI agents", referenced in the course intro; PDF p.114).
6. Example simulator / reference code (Appendix D; `https://github.com/rmisegal/Game-P2P-Cop-Chase`) — **educational, non-binding**.

## Mandatory-vs-illustrative interpretation rule (the "default")

Source: PDF p.4 / book iv (הבהרה: מה מחייב ומה רק ממחיש), reinforced PDF p.5 / book v.

> **The default is that no rule is binding unless it is explicitly written to be
> binding.** All figures, examples, code fragments, and scenarios are
> *illustrations* of how the game may be run — they are **not** the rules of the
> game and do not bind the participants, unless it is explicitly stated beside
> them that they are part of the rules and bind the parties. Where a rule is not
> stated to be binding, each side may agree with its opponent on other behaviour,
> or act as it sees fit within the law.

Consequences applied throughout Stage 1:
- **Never turn a recommendation (המלצה) into a MUST.** Never weaken a MUST (חובה) / MUST NOT (איסור) into a recommendation.
- Examples remain **INFORMATIONAL** unless the book explicitly binds them.
- The single source of obligation for **quantitative** values is **Appendix F**; values shown mid-text are code-names in square brackets (e.g., `[ גודל הלוח ]` / "[board size]") whose actual numbers live only in Appendix F.

## Appendix E role

Appendix E is the consolidated "do / don't / recommend" (עשה, אל תעשה והמלצות) mapping. Column 2 ("פעולה") is one of:
- **חובה = MUST** (obligation);
- **איסור = MUST NOT** (prohibition);
- **המלצה = SHOULD/recommendation** (no mandatory sanction).

Each entry carries a **sanction (סנקציה)** clause stating the systemic consequence. Every Appendix E entry is expected to map to at least one `REQUIREMENT_CATALOG` ID (see `APPENDIX_E_CROSSWALK.md`).

## Appendix F numeric authority

Appendix F (PDF p.151–160) is the **only** binding authority for numeric values. The "Status" column (PDF p.155 / book 139) takes one of three binding meanings:
- **מינימום = MINIMUM** — parties may negotiate the value **only in the direction that makes the game harder** (usually increasing); **never** below the example. Absent explicit mutual agreement, the code must default to the example value.
- **קבוע = FIXED** — binding, not changeable at all; deviation disqualifies the team.
- **משא ומתן = NEGOTIABLE** — parties may agree on any value; absent agreement, the code must default to the example value.

**If a numeric value elsewhere in the book differs from Appendix F, Appendix F wins.** No earlier-chapter value may replace an Appendix F value.

## Non-numeric conflict treatment (academic freedom)

Source: PDF p.5 / book v (חופש אקדמי במקרה של סתירה).

> The book was written to be consistent, but a contradiction may be found — two
> places that seem to dictate different behaviour. In such a case you have the
> **academic freedom** to choose one option and proceed on it, **provided you
> state it explicitly in your report**: where you found the contradiction, what
> you chose, and why. A reasoned, documented choice will not count against you.
> The single binding source for quantitative values remains Appendix F.

Applied in Stage 1A: **do not resolve** non-numeric conflicts now. Record each in `docs/CONFLICT_REGISTER.md` with alternatives; a selected interpretation is deferred to a reviewed stage unless the book itself resolves it.

## Example-code status

The reference implementation / example simulator (Appendix D; the public
`Game-P2P-Cop-Chase` repo) is **educational and non-binding**. PDF p.141 / book 125:
"wherever the repository deviates from the book, the book and the mandatory
parameter table prevail." It is a learning starting point, **not a submission
skeleton** — the solution is measured against the full specification.

## Modality terminology used by this repository

| Book term (He) | Book term (En) | This repo modality |
|---|---|---|
| חובה | obligation | **MUST** |
| איסור | prohibition | **MUST NOT** |
| המלצה / מומלץ / מומלץ מאוד | recommended / strongly recommended | **SHOULD** |
| רשות / אופציונלי | optional | **MAY** |
| (illustrative example, no binding marker) | — | **INFORMATIONAL** |

Rules: one independently-testable requirement per catalog ID; a sanction is
recorded only when the book explicitly specifies one; verification methods
describe how we can later prove compliance and never change the requirement.

## Citation convention

Every extracted requirement cites, when available, **both**:
- the **PDF page number** (the physical page in `.project-spec/police_thief_p2p.pdf`), and
- the **printed/book page or appendix/section identifier**.

Format:

```
Source: PDF p.145 / App E Table 9 #19
Source: PDF p.153 / App F Table 15 (movement & barriers)
Source: PDF p.50 / book 34, §5.3 (Commit-Reveal)
```

Printed page numbers are given only where the book prints them; they are **not**
fabricated where unavailable. The body-to-PDF offset for this document is **+16**
(book page N ≈ PDF page N+16), verified against References (book 100 → PDF 116)
and Appendices E/F. Roman-numeral front matter occupies PDF p.1–16.

## Warning

No rule, numeric value, status, or JSON field may be reconstructed from memory.
Every element in the Stage 1 artifacts traces to a cited page of book v3.0.0.
Extraction ambiguities (imperfect Hebrew RTL extraction of a critical passage)
are marked **REVIEW REQUIRED** rather than guessed.
