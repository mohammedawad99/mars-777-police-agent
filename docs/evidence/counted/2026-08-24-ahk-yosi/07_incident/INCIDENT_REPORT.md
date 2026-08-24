# Incident report — counted game MaRs-777 vs ahk-yosi, 2026-08-24

Every statement is tagged **OBSERVED**, **INFERRED**, **OPERATOR ACTION** or
**UNKNOWN**. Nothing here is reconstructed from memory.

---

## 1. Game identity — OBSERVED

From `02_protocol/declaration_MaRs-777-vs-ahk-yosi.json`, the merged Step-0
declaration:

| | |
|---|---|
| `game_id` | `MaRs-777-vs-ahk-yosi` |
| `game_uid` | `5ed16f3b-4e6b-4e9d-65bf-8f5abab699f2` |
| `game_start` | `2026-08-24T19:15:00Z` |
| opponent | `ahk-yosi` |
| MaRs-777 police commit | `feeee6542810d5a87eca001a4f9320ff0475b574` |
| MaRs-777 thief commit | `e49faa5184601037bdc4d872124c1e2ad8073c3b` |
| ahk-yosi commit (both roles) | `093d55122d8e44ed20f9e0a69cd3f63d8eaed402` |
| Step-0 authentication | HMAC-SHA256, `key_id mars777-ahk-yosi-20260824-02` |

The declaration is merged (both participant subtrees present), which this
project's runtime produces **only** after the peer's HMAC proof verifies.

Declaration written **2026-08-24 19:41:00.78Z** (file mtime).

---

## 2. What happened during the game

**OBSERVED — all six windows were played.** Our two role backends recorded three
sub-games each, in `03_subgames/`:

| gNN | our role | entries (ours) | peer records | opponent chain verified | cop | thief |
|---|---|---|---|---|---|---|
| g01 | police | 34 | 71 | **true** | 5 | 10 |
| g02 | thief | 15 | 15 | **true** | 20 | 5 |
| g03 | police | 34 | 71 | **true** | 5 | 10 |
| g04 | thief | 15 | 15 | **true** | 20 | 5 |
| g05 | police | 34 | 71 | **true** | 5 | 10 |
| g06 | thief | 11 | 11 | **true** | 20 | 5 |

**OBSERVED — totals: MaRs-777 30, ahk-yosi 90.** ahk-yosi's own filed report
gives identical per-window scores and the same totals.

**OBSERVED — anomalies before play:**

- Our two role backends bound at 19:12Z, exited on their peer-wait budget
  (`StaleMessageError: the opponent went silent past our own budget; no turn was
  ever applied`; thief `TimeoutError`), and were restarted at 19:43:01Z. The
  gateway was never restarted, so the merged declaration survived.
- Our ngrok tunnel agent stopped passing traffic while the gateway remained
  healthy (`local 46647 -> 406`, public edge `000`). Only the tunnel was
  restarted, at 19:31Z. The gateway process was left running throughout.

**OBSERVED — the defect that decided the outcome.** The gateway's log contains
**zero** row-contribution calls, and its artifact root holds only the
declaration. The per-sub-game rows our backends settled never reached the
gateway's result assembler.

**INFERRED.** Because the result core is built only from six settled rows plus
both participants' contributions, no `RESULT_APPROVAL_CORE` was assembled, no
`result_sha256` was computed, no result agreement ran, and the official
fourteen-file set was never written. The backends' own evidence documents are
labelled `evidence_class: DEVELOPMENT_EVIDENCE`, which is the backend-local
contribution form, not the counted official set.

---

## 3. Automatic reporting — OBSERVED: **DID NOT SEND**

No `reporting/` directory and no `result_<game_id>.json` exist. Automatic
reporting requires a result artifact with `mutual_agreement: true` and a
`result_sha256` (`app/report_source.py`); neither exists, so the reporter was
never eligible and never ran.

The gateway did print `COUNTED_SERIES_WRITER = ARMED` before Step-0, so the
reporting path was provisioned. It was never reached.

**This is not a PASS. Automatic reporting did not happen.**

---

## 4. Manual report — OPERATOR ACTION

The operator sent the lecturer report manually after the automatic path did not
send. See `06_reporting/REPORTING_RECORD.md`.

- recipient: **UNKNOWN / not captured**
- timestamp: **UNKNOWN / not captured**
- gmail `message_id`: **UNKNOWN / not captured**

No second email was sent. No Gmail lookup was performed. The project's automatic
reporter did **not** perform the manual send and is not claimed to have.

---

## 5. Artifact integrity — OBSERVED

Expected official set for a counted series: **14** files
(1 declaration + 6 config + 6 log + 1 result).

**Present: 1 of 14.**

| family | expected | present | missing |
|---|---|---|---|
| declaration | 1 | **1** | — |
| config g01–g06 | 6 | **0** | all six |
| log g01–g06 | 6 | **0** | all six |
| result | 1 | **0** | 1 |

No placeholder was created for any missing file. The per-sub-game play *is*
preserved, in the two backend contribution documents in `03_subgames/`, which
carry the commitments, record counts, audit verdicts and scores for all six
windows — but those are backend-local evidence, **not** the official artifacts.

---

## 6. Opponent's filed report — OBSERVED

ahk-yosi filed a report that:

- sets `mutual_agreement: true` while its own `result_agreement.agreed` is
  `false`, `result_agreement.sent` is `false`, and
  `series_consensus.sha_match` is `false`;
- names `groups.opponent.group_id` as the literal string `"opponent"`, with
  empty `members` and `repos`, rather than `MaRs-777`.

Its per-window scores agree with ours exactly. We do not dispute the sporting
result: **ahk-yosi won 90–30**, and our audit verified their commitment chain in
all six windows.

---

## 7. Submission impact

- All available evidence from the completed run is preserved and committed.
- The defect is documented rather than concealed.
- **No artifact produced during the live run was modified**, re-rendered or
  re-ordered; the game JSON documents are byte-for-byte as written.
- No `mutual_agreement`, `result_sha256` or `reported_by` was fabricated.
- No result was invented to make the count reach fourteen.
- The repository state reflects the actual run, including its failure.
