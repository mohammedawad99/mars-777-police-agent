# Reporting record — counted game vs `ahk-yosi`, 2026-08-24

## OBSERVED

- **No `reporting/` directory was produced** under the run's artifact root.
- **No `result_<game_id>.json` was produced.** The artifact root holds exactly one
  official file, `declaration_MaRs-777-vs-ahk-yosi.json`.
- Automatic reporting is gated on a result artifact carrying `mutual_agreement:
  true` and a `result_sha256` (`app/report_source.py`). Neither exists, so the
  automatic reporter was never eligible and **did not send**.
- The gateway did report `COUNTED_SERIES_WRITER = ARMED` before Step-0, so the
  reporting path itself was provisioned; it was never reached.

## INFERRED

- Because the result core is assembled only from six settled rows, and the
  gateway collected none, no `RESULT_APPROVAL_CORE` was built and therefore no
  digest, no agreement and no report could follow.

## OPERATOR ACTION

- The operator sent the lecturer report **manually**, outside the project's
  automatic reporter, after the automatic path did not send.
- A correction message was subsequently prepared by the operator, because the
  first manual send attached `ahk-yosi`'s own report document rather than a
  MaRs-777 one.

## UNKNOWN

- `recipient`: not captured in local evidence.
- `manual send timestamp`: not captured in local evidence.
- `gmail message_id`: **UNKNOWN / not captured.**
- `attachment sha256 as actually sent`: not captured in local evidence.

No Gmail lookup was performed and no second email was sent.

## NOT DONE, DELIBERATELY

- No second lecturer email.
- No automatic-report retry.
- No fabricated `mutual_agreement`, `result_sha256` or `reported_by`.
- No modification of any artifact produced during the live run.
