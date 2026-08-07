# Appendix E Raw Crosswalk — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. Approved baseline (input to
Stage 1C). Approved counts: 55 total, MUST 45, MUST NOT 9, SHOULD 1 (E-25).**

Systematic processing of **every** Appendix E entry (PDF p.142–150 / book 126–134),
Tables 7–12, entries 1–55. Action column: **MUST** = חובה, **MUST NOT** = איסור,
**SHOULD** = המלצה. "Sanction" is quoted/translated from the book's סנקציה clause.
Every entry maps to at least one `REQUIREMENT_CATALOG.md` ID. English renderings
are working translations of the Hebrew source.

## Table 7 — Network architecture, decentralization, local epistemology (PDF p.142–144 / book 126–127)

| # | Action | Rule (translated) | Sanction (translated) | Catalog IDs |
|---|---|---|---|---|
| 1 | MUST | Run thief and police code in two completely separate processes. | Total failure; breaks the Zero-Trust model. | ARCH-001 |
| 2 | MUST NOT | Never share memory or variables between the two sides. | Immediate disqualification for information leakage. | ARCH-002 |
| 3 | MUST | Define the orchestrator component as the single entry point to the sub-systems. | Technical instability and loss. | STATE-001 |
| 4 | MUST | Manage game states with a proper state machine. | Technical loss via deadlock. | STATE-002 |
| 5 | MUST | Reject any illegal state-transition attempt in the state machine. | Logic error leading to loss. | STATE-003 |
| 6 | MUST | Implement a deadline-tracking mechanism to prevent freezing while waiting for the opponent. | System paralysis and loss on timeout. | STATE-004 |
| 7 | MUST | Run a watchdog to monitor process crashes and controlled data extraction. | Game crash and loss of official documentation. | STATE-005 |
| 8 | MUST | Display **local truth only** in the live UI. | Disqualification of system legality (info breach). | GUI-001 |
| 9 | MUST NOT | Do not display the full objective board state in the live UI. | Disqualification for illegal advantage. | GUI-002 |
| 10 | MUST | Use a tunnelling tool to expose the local server to the public internet. | Inability to compete in the league. | NET-001 |

## Table 8 — Spatial mechanics, physics, board constraints (PDF p.144 / book 128)

| # | Action | Rule | Sanction | Catalog IDs |
|---|---|---|---|---|
| 11 | MUST | Verify the config file is byte-for-byte identical on both sides. | Game disqualification for symmetry breaking. | GAME-001 |
| 12 | MUST | Raise minimum values in the parameter table **by agreement only**, never lower them. | Threshold violation → score disqualification. | GAME-002 |
| 13 | MUST | Move only in orthogonal directions. | Illegal move and technical loss. | GAME-003 |
| 14 | MUST NOT | Do not make diagonal moves. | Move rejected by opponent → loss. | GAME-004 |
| 15 | MUST | Declare openly every barrier placement. | Board forgery → automatic loss in audit. | BAR-001 |
| 16 | MUST NOT | Do not lie about the barrier placement location. | Severe disqualification cause. | BAR-002 |

## Table 9 — Cryptography, log integrity, zero-knowledge (PDF p.145 / book 129)

| # | Action | Rule | Sanction | Catalog IDs |
|---|---|---|---|---|
| 17 | MUST | Use a commit-reveal protocol based on SHA-256. | Absence of mechanism → solution is illegal. | CRYPTO-001 |
| 18 | MUST | Keep the nonce completely secret until the end of the game. | Defence disqualified (dictionary-attack risk). | CRYPTO-002 |
| 19 | MUST | Technically disqualify a game on any hash mismatch at audit. | Iron rule: score 0 to the forging team. | CRYPTO-003 |
| 20 | MUST | Build a viewer app to replay and verify the game log. | Threshold for approving audits and for submission. | REPLAY-001 |
| 21 | MUST | Declare truth only when capturing a thief. | Immediate disqualification for denying reality. | CRYPTO-004 |
| 22 | MUST NOT | Do not falsely declare a capture; a false claim → immediate disqualification. | Score 0 and technical loss, no appeal. | CRYPTO-005 |
| 23 | MUST | Cryptographically lock the scent-emission model before the game starts. | A decay-formula deviation voids the game. | SCENT-001 |
| 24 | MUST | Perform a cryptographic hardware declaration before the game starts (Step-0). | Denial of eligibility for the computational-fairness bonus. | CRYPTO-006 |

## Table 10 — Strategy, language, public network (PDF p.146 / book 130)

| # | Action | Rule | Sanction / note | Catalog IDs |
|---|---|---|---|---|
| 25 | **SHOULD** | Do not hand the LLM the decision on the movement itself; use it for text processing and behavioural profiling only. | **No mandatory sanction**, but blind reliance may cause hallucinations, illegal moves, technical loss. | LLM-001 |
| 26 | MUST | Communicate in free natural language only. | Preserves the psychological-challenge nature. | LLM-002 |
| 27 | MUST NOT | Do not use a direct numeric-positions protocol. | Disqualifies the game's defined character. | LLM-003 |
| 28 | MUST | Implement a token-bucket rate-limiter for sending reports to Gmail. | Prevents 429 blocking that would paralyse reporting. | NET-002 |
| 29 | MUST | Define a DOS-prevention detector to hard-protect network resources. | Locks the interface to prevent account blocking. | SEC-001 |
| 30 | MUST | Use send-only permission for the Gmail interface. | Security violation → disqualification in code. | SEC-002 |

## Table 11 — League fairness, admin procedures, competition purity (PDF p.147–148 / book 131–132)

| # | Action | Rule | Sanction | Catalog IDs |
|---|---|---|---|---|
| 31 | MUST | Play a minimum mandatory number of counted games against **different** teams. | Not meeting the minimum → no passing grade. | LEAGUE-001 |
| 32 | MUST | Report game results automatically via Gmail. | No report → points from that game are disqualified. | REPORT-001 |
| 33 | MUST | Format the game report as a standard JSON data structure. | Code can't process free text → report rejected. | JSON-001 |
| 34 | MUST NOT | Do not send a completion report in free text — only as an attached JSON file. | Non-JSON report rejected → score 0. | JSON-002 |
| 35 | MUST | Agree with the opponent on the result; each team sends a separate completion report. Non-report by one side or a conflicting report → game disqualified, score 0 to **both** teams. | Main enforcement mechanism against reporting fraud. | LEAGUE-002 |
| 36 | MUST | Perform comprehensive mutual log audit at the end of each game. | Necessary condition before agreeing on the shared JSON result. | CRYPTO-007 |
| 37 | MUST | Declare precisely the number of games actually played at the start of each game. | Threshold for computing the true competition factor. | LEAGUE-003 |
| 38 | MUST NOT | Do not falsely declare the number of games; a false declaration disqualifies the project. | Total disqualification for discipline/integrity violation. | LEAGUE-004 |
| 39 | MUST NOT | Never push secrets and credentials to the repository — even if private and shared only with the lecturer. | Severe security failure and project failure. | SEC-003 |
| 40 | MUST | Add the credential and secret files to `.gitignore`. | Mandatory protection against Gmail API credential leak. | SEC-004 |
| 41 | MUST | Tag the submission version in the repo with a documented Git tag. | Administrative condition letting the lecturer check the final version. | GIT-001 |
| 42 | MUST | Write and attach a comprehensive academic report as a readable file in the repo (model, dilemmas, strategy, images, RL curves). | Without it the project is academically incomplete. | DOC-001 |
| 43 | MUST | Download a submission form from Moodle, fill it, save as PDF; do not change or move fields. | Bureaucratic condition for a grade. | SUB-001 |
| 44 | MUST | Submit the assignment in Moodle separately for each group member. | Without individual submission the student gets no grade. | SUB-002 |
| 45 | MUST | Enter a unique **8-character group ID** with no spaces. | Organisational failure preventing automatic report attribution. | SUB-003 |

## Table 12 — Additions found when cross-checking the book (PDF p.149–150 / book 133–134)

| # | Action | Rule | Book source | Catalog IDs |
|---|---|---|---|---|
| 46 | MUST | A barrier placed on the cell where the thief currently stands counts as a capture (police wins). | Ch 3 | BAR-003 |
| 47 | MUST | A thief locked with no legal move is also considered captured. | Ch 3 | GAME-005 |
| 48 | MUST | Score every end scenario per the scoring table (capture thief 5 / cop 20; survival thief 10 / cop 5; technical loss 0/0). | Ch 3 + App F | GAME-006 |
| 49 | MUST | Submit two separate GitHub repos (police, thief) with README cross-link, two links in the Moodle submission, and four links in both teams' JSON. | Ch 9 | SUB-004 |
| 50 | MUST | Include in each repo at least: README, config files (`config/`), PRD files, a PLAN file, TODO files. | Ch 9 | GIT-002 |
| 51 | MUST | Send the automatic completion reports to the lecturer's address `[ agent reports address ]`. | Ch 9 | REPORT-002 |
| 52 | MUST | Exactly one counted game per opponent (no repeats for score accumulation); non-counted warm-up games are allowed. | Ch 9 | LEAGUE-005 |
| 53 | MUST | Record in the Step-0 declaration the commit hash played; code may change between games, but each game must update the commit hash. | Ch 5 | GIT-003 |
| 54 | MUST | Report in the completion JSON the total tokens consumed in the game (and series). | Ch 5, Ch 9 | PERF-001 |
| 55 | MUST | Give a self-score for code quality only — not for the league game result. | Ch 11 | DOC-002 |

## Coverage tally

- **Total Appendix E entries reviewed: 55 / 55.**
- **Entries mapped to a catalog ID: 55 / 55.**
- **Unmapped mandatory entries: 0.**
- **Exact modality split (Stage 1B, re-derived from tables):** **MUST 45 · MUST NOT 9 · SHOULD 1** = 55. Per table: T7 (8/2/0), T8 (4/2/0), T9 (7/1/0), T10 (4/1/1), T11 (12/3/0), T12 (10/0/0). MUST NOT entries: 2,9,14,16,22,27,34,38,39.
- **Ambiguous entries: 0** at the mapping level. (Entry 48 numbers are cross-checked against Appendix F Table 17 — see the ordering note in `CONFLICT_REGISTER.md` C-06; entry 48's "per the parameter table" for technical-loss is an App F omission, see C-07. The mapping itself is unambiguous.)
- Modality note: **entry 25 is the only SHOULD** (recommendation, explicitly "no mandatory sanction"); all other 54 entries are MUST/MUST NOT. No recommendation was upgraded to a MUST and no MUST was weakened.
