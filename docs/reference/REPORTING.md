# Gmail reporting — group MaRs-777

**Status: CURRENT.** Added at Stage 9A-2C.

At the end of every legal game, each group sends its own completion report to
the lecturer, as an attached JSON file, through the Gmail API, behind a
token-bucket Gatekeeper. This document is the map from the source to the code.

## 1. What the source requires

| ID | Requirement | Kind | Source | Sanction |
|---|---|---|---|---|
| `REPORT-001` / E-32 | report the game result automatically through the Gmail interface | MUST | Ch 9 §9.3; App E rule 32 | absence of a report **disqualifies the points from that game** |
| `REPORT-002` / E-51 | send to the fixed lecturer reports address | MUST | Ch 9 §9.3; App E rule 51; App F Table 20 | — |
| `REPORT-003` / NET-002 / E-28 | a **token-bucket** rate limiter for the Gmail sends; respect `429`, back off, wait for the next window | MUST | Ch 9 §9.3.1–§9.3.2, p.95; App E rule 28; App F Table 19 | blind retry risks **account suspension** and paralyses the group's reporting |
| `SEC-001` / E-29 | a DOS detector that hard-locks API access on an anomalous send pattern | MUST | Ch 9 §9.3.1; App E rule 29 | prevents suspension of the reporting account |
| `SEC-002` / `SEC-006` / E-30 | send-only OAuth scope, `gmail.send` and nothing wider | MUST | App A §1.3; App E rule 30 | security violation → disqualification in code |
| `JSON-001` / E-33 | the report is a standard, machine-readable JSON structure | MUST | Ch 9 §9.3.3; App E rule 33 | a report code cannot parse **is rejected** |
| `JSON-002` / E-34 | the completion report goes **only as an attached JSON file**, never as free text | **MUST NOT** | Ch 9 §9.3.3; App E rule 34 | a non-JSON report is refused in processing → **grade 0** |
| `LEAGUE-002` / E-35 | agree the result with the opponent; each group sends its own separate report | MUST | Ch 9 §9.3.3; App E rule 35 | non-report by one side, or contradictory reports → **game disqualified, 0 to both** |
| E-36 | comprehensive mutual log audit at the end of each game | MUST | App E rule 36 | necessary precondition **before** agreeing the shared JSON result |

## 2. Trigger — after the agreement, never before

Ch 9 §9.3: *"at the end of every legal game against an opponent team … each of
the two groups is programmed to send, itself and separately, an automatic
summary message to the lecturer via the Gmail API; it is not enough that only
one side sends."*

So the trigger is **per game**, not per sub-game, and it sits after rule 36's
mutual audit and rule 35's agreement. In this codebase that point already has a
name: `ProtocolPhase.REPORT_READY`, which `STATE_MACHINE.md` reaches only from
`FINAL_AUDIT`, and which `series_runtime.persist_result` advances to *after*
refusing to write the result without `ResultExchange.is_agreed`.

`app/report_eligibility.py` refuses every other phase, and `app/report_source.py`
refuses any document that does not carry `mutual_agreement: true` and a
`result_sha256`. A friendly or KIT run produces neither, so it cannot be
reported — proved by `tests/kit_series/test_kit_not_counted.py`.

## 3. Recipient — fixed by the source, not configurable

Appendix F Table 20 defines `[agent reports address]` as
`rmisegal+uoh26finalgame@gmail.com`, *"destination of the JSON reports the agent
sends automatically"*, and states that the table is **reference-only, not part of
the agreed configuration file and not negotiable**. Ch 9 adds: *"this is the
single and binding address … it must be defined as the fixed target in the
mail-sending code of each of the two agents."*

It is therefore a constant in `app/report_values.py`. No environment variable,
launch document or peer term can redirect a counted report. Header injection into
it is refused rather than escaped.

## 4. Subject — source-open, so fixed by project decision

Chapter 9, Appendix E and Appendix F say nothing about a subject; Appendix A
shows `subject` only as a parameter of an illustrative function. The project
therefore fixes one deterministic minimal subject:

```
MaRs-777 <role> result <game_id>
```

It names the group, which side of the pair sent it and the game, so a grader can
attribute and sort without opening anything. It carries no score, no board state
and no secret, and it is refused if any component contains a control character.

## 5. Body and attachment — the report is the attachment

Ch 9 §9.3.3: *"the game report is not free text. It is packaged in a uniform,
binding JSON structure and **sent as an attached file** to the mail message."*
Appendix F Table 20 names that file `result_<game_id>.json` and calls it *"the
binding report sent by email"*.

That file already exists: it is the official result artifact the series wrote
after the agreement. **The reporting layer attaches those exact bytes** and
recomputes nothing — not the winner, not the scores, not the outcome, not the
digest.

The covering body carries identifiers only, in a fixed order, with no greeting,
no commentary, no signature and no Markdown:

```
game_id: <id>
group_id: <id>
role: <police|thief>
result_sha256: <hex>
attachment: result_<game_id>.json
```

The message is a `multipart/mixed` with a **fixed** boundary and explicit
`\r\n` line endings, so one report always serialises to the same bytes on Ubuntu
and on Windows. `tests/reporting/test_report_contract.py` is the golden vector.

## 6. Token bucket — the algorithm is source-binding

Appendix E rule 28 names it: *"implement a **token-bucket** based rate limiter
for sending the reports to Gmail."* That is an algorithm requirement, not a
description of quota behaviour, so the rolling-window admission Stage 9A-1C
shipped is **not** relabelled as one. Ch 9 §9.3.2 gives the rule, and
`app/gatekeeper_bucket.py` transcribes it:

```
tokens <- min(C, tokens + r * dt),    allow <=> tokens >= 1
```

The Gatekeeper gained an **admission chain** rather than a second gate. Ch 9
§9.3.1 describes one pattern with three cumulative mechanisms, and its figure
shows an outgoing report passing all three with a distinct exit at each:

| Mechanism | Module | Exit |
|---|---|---|
| Quota Manager | `app/gatekeeper_quota.py` | `Rejected (quota full)` — a refusal, not a wait |
| Token Bucket | `app/gatekeeper_bucket.py` | `Blocked (no token)` — a wait until one refills |
| DOS Detector | `app/gatekeeper_dos.py` | `LOCKED (anomaly)` — latched shut |

Every other operation keeps the rolling windows unchanged.

## 7. Appendix F Table 19 — the numeric authority

| # | Parameter | Example | Status | Where it is used |
|---|---|---|---|---|
| 1 | requests per minute | **30** | MINIMUM | `requests_per_minute: 30` → bucket refill `r = 30/60 = 0.5` tokens/s |
| 2 | parallel requests | **2** | MINIMUM | `concurrent_max: 2` |
| 3 | delay after error | **5 s** | MINIMUM | `retry_after_seconds: 5` |
| 4 | retries before failure | **3** | MINIMUM | `max_retries: 3` |
| 5 | queue depth under load | **100** | MINIMUM | `queue_depth: 100` |
| 6 | response time limit | 30 s | NEGOTIABLE | the adapter's request timeout |
| 7 | watchdog threshold | 60 s | NEGOTIABLE | owned by the peer protocol, not by reporting |

Appendix F defines MINIMUM as: *"the parties may negotiate the value, but only
in the direction that makes the game harder … never easing below the example
value. In the absence of an explicit agreement, the code must ensure the example
value is the default the group uses."* Every one of the five is therefore
configured at exactly its example value.

**Two values Table 19 does not give.** The bucket's capacity `C` and the Quota
Manager's daily threshold have no binding number anywhere in the book.

* `burst_capacity: 5` — the only capacity the source ever shows is `C = 5` in
  its own worked figure (§9.3.2, `r = 0.8, C = 5`). Reporting sends one message
  per game, so five is already far above any legitimate burst.
* `daily_quota: 50` — one report per game, a handful of games in a league day.
  Fifty leaves two orders of magnitude of headroom for retries and re-sends
  while still stopping a loop dead.
* `dos_burst_limit: 10` in `dos_window_seconds: 60` — Ch 9 asks *"what happens
  when an infinite loop starts firing thousands of messages a minute?"*. Ten
  sends in a minute cannot be an operator reporting games.

These three are recorded here as **project decisions over a source gap**, not as
Appendix F values.

## 8. `rate_limits.json` and the version

The Gmail policy is a service entry named `gmail.send_report`, beside `default`
and `ngrok.discover_tunnels`. `rate_limits.version` stays `"1.00"`: the
version-bump policy is written down in `shared/rate_limits.py` and says a
version rises only when an existing valid document would stop being valid or
change meaning. A new service entry is data, and the admission keys are optional
with defaults that reproduce the previous behaviour exactly, so every `1.00`
document remains valid and behaves identically.

## 9. Gmail mechanism and why no Google SDK

Appendix A binds the *mechanism*: the Gmail API, OAuth 2.0, the `gmail.send`
scope and nothing wider, and `users.messages.send` carrying the base64url MIME
message. Its Python snippet is introduced as *an illustration of the flow*, and
no clause requires a particular client library.

`infra/gmail_sender.py` therefore speaks that API directly over the standard
library, exactly as `infra/ngrok_ingress.py` already reads its provider. Three
reasons, in order of weight:

1. **Architecture.** `google-api-python-client` carries its own retry engine and
   fetches a discovery document of its own accord — a second limiter and a
   provider call outside the Gatekeeper, which is precisely what Ch 9 §9.3.1
   asks the Gatekeeper to prevent, and what this stage forbids.
2. **Testability.** The exact outgoing request is inspectable and golden-tested
   at the adapter seam, with no packet leaving the machine.
3. **Cost.** No dependency to resolve or install, which matters while
   independent verification is a scarce resource.

**Dependencies added by this stage: none.**

## 10. Credentials

Appendix A §1.4–§1.5: the operator creates a Desktop OAuth client, downloads
`credentials.json`, and the first authorisation run writes `token.json` holding
the access and refresh tokens. Both files are secrets and both are already in
`.gitignore`, as rule 40 requires.

This agent never runs the interactive consent flow; it reads `token.json` and
exchanges the refresh token for an access token when it needs one. One-time
setup, using the book's own Appendix A snippet:

```bash
uv run --with google-auth-oauthlib --with google-api-python-client python - <<'PY'
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)
open("token.json", "w").write(creds.to_json())
PY
```

Then point the agent at it:

```bash
export MARS777_GMAIL_TOKEN=./token.json
```

A token file that grants anything wider than `gmail.send` is **refused**, not
used. No token, client secret or refresh token is ever printed, logged, stored
in evidence or included in an exception message.

## 11. Sending a report

```bash
uv run python -m mars777_police.report_main \
    --result artifacts/result_<game_id>.json [--root artifacts]
```

| Code | Meaning |
|---|---|
| `0` | the provider accepted the report |
| `2` | a local refusal — no credential, an unreadable result, or a result with no mutual agreement. Printed as a sentence, never a traceback |
| `3` | the report was eligible and correctly built, but the provider did **not** accept it. Reporting is `REPORTING_INCOMPLETE` and must be retried |

Also available programmatically as `AgentSdk().send_game_report(...)` and, for a
dry check that reaches no provider at all, `AgentSdk().read_game_report(...)`.

## 12. Failure never rewrites a result

A game fact and a delivery status are different things, and only the second can
fail here. Whatever the provider does, `result_<game_id>.json` is untouched, the
agreed digest is untouched and the winner is untouched; a failed send leaves
`REPORTING_INCOMPLETE` and an explicit `provider_accepted: false` in the delivery
record. There is no silent success.

Delivery status is written to `<artifact root>/reporting/delivery_<game_id>.json`
— deliberately **outside** the official namespace, so the graded artifact set
stays exactly fourteen files whether or not an email ever went out.

## 13. Duplicate sends

The report identity is `(game_id, result_sha256)` — the agreed digest, not a
value invented for de-duplication, and nothing about it enters the binding JSON.
A process that already delivered an identity returns the first answer instead of
mailing the lecturer twice; a previous *failure* is not a delivery, so retrying
after one is a first send.

**Honestly stated residual ambiguity:** Gmail offers no server-side idempotency
key, and the delivery record is written after the response. If a send is
accepted but the response is lost, this process records a failure for a message
that was in fact delivered, and a retry would send a second copy. Both copies
carry the same agreed digest, so they are duplicates rather than contradictory
reports — which is what rule 35 actually sanctions.

## 14. Live sending

**`LIVE_GMAIL_SEND: NOT_PERFORMED`.** No real message has been sent by this
project. The live smoke requires three independent signals — `MARS777_RUN_LIVE_GMAIL=1`,
`MARS777_GMAIL_TOKEN` and `MARS777_LIVE_GMAIL_RECIPIENT` — and a credential that
merely exists on a machine authorises nothing. CI sets none of them and can
never send. When authorised, the smoke sends to the **operator's own** address
with a payload labelled `live_smoke`, never to the lecturer and never a
fabricated counted result.
