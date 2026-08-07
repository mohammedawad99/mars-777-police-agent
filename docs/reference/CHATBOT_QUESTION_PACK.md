# Chatbot Question Pack — group MaRs-777

# STATUS: RESOLVED — CHATBOT REVIEW COMPLETE, ZERO QUESTIONS PENDING

**All ten questions are answered.** Q1–Q5, Q9–Q10 were resolved by user-supplied
**source extraction** from the lecturer's second chatbot (verbatim in
`ATTACHMENT_EVIDENCE.md`, AE-01…AE-04); Q6–Q8 were resolved directly from the primary
PDF. Outcomes are recorded in `CHATBOT_ANSWERS.md`. **No further questions are
required.** The text below is retained as the historical record of what was asked.

**How to use.** Ask the lecturer-provided chatbot each question **verbatim**, one at a
time, and paste the answer **exactly as returned** into `CHATBOT_ANSWERS.md` (do not
paraphrase). Each question is self-contained, cites its source, isolates **one**
ambiguity, and is answerable **without seeing our code**.

**Why these.** Every question below is one whose answer could materially change
architecture, interoperability, league validity, or submission. Questions already
answered unambiguously by Appendix F are deliberately **excluded** (grid size, scoring,
barrier quota, max moves, survival threshold, pheromone values, rate-limiter values,
timeout defaults, diversity reward, min/max games, token budget).

---

### Q1 — Role alternation across a counted series
**Source:** Ch 9 / Appendix F Table 18 (`[games per series]`); reference repository
`src/police_thief/sdk/series.py::role_for()`.

> In a counted six-sub-game series, must the two groups **alternate the Police and
> Thief roles** between sub-games (as the reference implementation does — natural role
> on odd sub-games, opposite on even), or may each agent keep a single fixed role for
> the whole series? If alternation is required, is it required per sub-game, and does a
> group satisfy it by activating its own separate Police repository and Thief
> repository in turn?

*Why it matters:* determines the series driver and which repository is active per
sub-game. **Architecture impact: potentially high. No change made pending the answer.**

---

### Q2 — FastMCP tool surface
**Source:** Ch 8 (FastMCP requirement); reference `infra/mcp_server.py` exposes
`negotiate`, `receive_turn`, `submit_audit`, `receive_control`.

> For cross-team interoperability, are the **exact FastMCP tool names and
> request/response structures** used in the reference repository **required**, or may
> two teams agree on equivalent FastMCP tools before a match?

*Why it matters:* a tool-surface mismatch makes a match impossible to play.
**Architecture impact: high (PRD-02/PRD-05).**

---

### Q3 — Commitment payload and construction
**Source:** Ch 5 §5.3–5.4 (sealed record; SHA-256 commit-reveal); reference
`domain/crypto.py` computes `SHA256(canonical_json(payload) + "|" + nonce)`.

> Is the **exact commitment construction** fixed — specifically, must the nonce be
> concatenated **outside** the canonical JSON payload as in the reference
> implementation — or is any construction acceptable provided both peers can
> deterministically recompute and verify the same SHA-256 commitment? Likewise, is the
> exact set of sealed fields fixed, or is it agreed between the peers before the match?

*Why it matters:* if the two peers frame the commitment differently, every turn fails
verification and reads as TAMPERED. **Architecture impact: high (PRD-06).**

---

### Q4 — Step-0 authentication primitive
**Source:** Ch 5 §5.5 (p.55–56): the Step-0 specification is "cryptographically signed
using a pre-supplied key (מפתח המסופק מראש) so that it cannot be forged retroactively".

> For the Step-0 declaration, is **HMAC-SHA256 with an agreed pre-shared key**
> acceptable as the "cryptographic signing with a pre-supplied key", or is an
> **asymmetric digital signature** (public/private key pair) expected? Is an **unkeyed
> SHA-256 digest alone** sufficient?

*Why it matters:* determines the cryptographic primitive and key-provisioning channel.
Note the reference implements only an unkeyed SHA-256. **Architecture impact: high
(PRD-06).**

---

### Q5 — Signed-configuration authentication
**Source:** Appendix B p.128 — the pre-game **signature exchange** that "refuses to play
on any mismatch".

> For the shared configuration, is the required pre-game **signature exchange**
> satisfied by both peers exchanging and comparing an **unkeyed SHA-256** of the agreed
> terms, or must it be a **keyed** authentication (e.g. HMAC with a pre-shared key) or
> an asymmetric signature?

*Why it matters:* decides whether config equality alone suffices or a keyed tag is also
required before counted play. **Architecture impact: high (PRD-06).**

---

### Q6 — Result JSON strictness
**Source:** Ch 9 §9.3.3 (p.94–96) — required report contents; no printed schema.

> Does `result_<game_id>.json` have a **parser-exact required schema and key set**, or
> are **equivalent JSON structures** acceptable provided every required semantic element
> is present (identities, four repository links, FastMCP endpoints, hardware
> declarations, per-sub-game scores/outcome/commit/tokens, cumulative totals, timestamp,
> mutual agreement, result hash)?

*Why it matters:* a strict grader parser could reject a semantically complete report.
**Architecture impact: medium (PRD-07).**

---

### Q7 — Additional fields in the emailed result
**Source:** Ch 9 §9.3.3; Appendix E #49/#54.

> Are **additional non-secret fields** tolerated in the emailed result JSON, or should
> it contain **only** the minimal required semantic surface?

*Why it matters:* determines how conservative the emitted report must be.
**Architecture impact: medium (PRD-07).**

---

### Q8 — Sub-game filename numbering `<NN>`
**Source:** Appendix F Table 20 / §2.3–2.4 — filenames `config_<game_id>_g<NN>.json`,
`log_<game_id>_g<NN>.json`.

> Is the sub-game suffix required to be **two-digit zero-padded** (`g01`…`g06`), is that
> merely recommended, or is the format unconstrained provided the sub-games are
> distinguishable?

*Why it matters:* filename identity must match what the grader expects.
**Architecture impact: low but submission-relevant (PRD-07).**

---

### Q9 — Extra pheromone key in the signed configuration
**Source:** Appendix F Table 16 lists three pheromone parameters (centre intensity 0.9,
decay 0.10, grid size 5). The reference `config/*/game.json` additionally contains
`pheromone_min_center_intensity: 0.5`.

> Is `pheromone_min_center_intensity` a **binding parameter** that must appear in the
> shared signed configuration, or is it a **reference-implementation extra**? If binding,
> what is its Appendix F status (FIXED / MINIMUM / NEGOTIABLE)?

*Why it matters:* any extra key changes the canonical bytes and therefore the
configuration hash both peers must match. **Architecture impact: medium (PRD-01/PRD-06).**

---

### Q10 — Comment-style keys inside the signed configuration
**Source:** Appendix B §B.3 key list; reference `game.json` contains `_note`,
`_axis_note`, `_hint_max_words_note`.

> May the shared signed configuration contain **comment-style keys** (e.g. `_note`), or
> must it contain **only** the Appendix B parameter keys so that both peers can hold a
> byte-identical file?

*Why it matters:* comment keys change the hashed bytes; both peers must agree exactly.
**Architecture impact: medium (PRD-06).**

---

## Question index

| ID | Topic | Impact | Blocks |
|---|---|---|---|
| Q1 | Role alternation in a six-sub-game series | High | Series driver (PRD-02), match orchestration |
| Q2 | FastMCP tool names / shapes | High | PRD-02, PRD-05 interop |
| Q3 | Commitment construction + sealed field set | High | PRD-06, cross-peer verification |
| Q4 | Step-0 authentication primitive | High | PRD-06, key provisioning |
| Q5 | Signed-config authentication primitive | High | PRD-06, pre-match gate |
| Q6 | Result JSON strictness | Medium | PRD-07 |
| Q7 | Extra result fields | Medium | PRD-07 |
| Q8 | `<NN>` filename format | Low | PRD-07, submission |
| Q9 | `pheromone_min_center_intensity` | Medium | PRD-01, PRD-06 |
| Q10 | Comment keys in signed config | Medium | PRD-06 |

**Not asked (already unambiguous in Appendix F):** grid size, agent count, move set,
barrier quota, max moves, survival threshold, all scoring values, the three pheromone
values, response/watchdog timeouts, rate-limiter parameters, diversity reward,
min/max games, token budget, `hint_max_words`.
