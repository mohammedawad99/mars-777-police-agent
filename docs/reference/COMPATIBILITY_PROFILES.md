# Compatibility Profiles — group MaRs-777

**Status: STAGE 2A-R2 — architecture-level profile definitions. No implementation.**

## The governing rule

> A compatibility profile may **ADD** accepted encodings, key names, nestings and
> conventions.
> A compatibility profile may **NEVER weaken a binding primary-book requirement** in
> **STRICT_COUNTED_MATCH** mode.

Profiles change **representation and tolerance**, never **semantics, sanctions,
Appendix-F values, or the official artifact filenames**.

## Profile 1 — `STRICT_COUNTED_MATCH` (default; the only profile used for a counted game)

| Aspect | Rule |
|---|---|
| Artifact filenames | **Always** Table 20: `declaration_<game_id>.json`, `config_<game_id>_g<NN>.json`, `log_<game_id>_g<NN>.json`, `result_<game_id>.json`. `<NN>` = `g01`…`g06` (JDEC-004) |
| Result content | Minimal mandatory semantics + `declaration_ref` join (JDEC-014). **Static metadata referenced, not duplicated** |
| Config emitted | App B parameter keys **only** — no `_note`, no extra pheromone key |
| Step-0 / config auth | **Keyed authentication** with a pre-supplied key; unkeyed SHA-256 alone is **not** accepted as producer authentication |
| Commitment | Locked 8-field sealed record, nonce **inside** the canonical payload |
| Numerics | Appendix F only; FIXED enforced, MINIMUM never lowered |
| Extras | No debug/presentation fields in emitted artifacts |
| Sanctions | Exactly the locked set (C-07, C-09, TAMPERED) — never softened |

## Profile 2 — `LECTURER_REFERENCE_COMPATIBILITY` (interop with reference-shaped peers)

Additive tolerances when negotiating with a peer built on the reference implementation:

| Aspect | Added tolerance |
|---|---|
| FastMCP tool names | Accept/propose `negotiate`, `receive_turn`, `submit_audit`, `receive_control` as **compatibility defaults** — **not** book-mandated |
| Commitment codec | May negotiate `LECTURER_REFERENCE_COMMITMENT` (`SHA256(canonical(payload) ‖ "\|" ‖ nonce)`) via the future `CommitmentCodec` abstraction, **only** by explicit pre-match agreement |
| Canonical JSON | Accept `ensure_ascii=False` (reference default) as the agreed serialization parameter |
| Config extras | **Recognise** `pheromone_min_center_intensity` and `_note`/`_axis_note` keys without letting them alter the three binding pheromone parameters or any Appendix-F semantic |
| Private timeouts | Tolerate a peer's private `turn_timeout_seconds` (e.g. 180 s); the **negotiated** `response_timeout_sec`/`watchdog_timeout_sec` remain the binding values |

**Never weakened:** keyed authentication, Appendix-F values, official filenames, C-07/C-08/C-09, commit-reveal mandatory semantics.

## Profile 3 — `LECTURER_ATTACHMENT_COMPATIBILITY` (align with the attachment example)

Goal: **make our normal output as close as safely possible to the attachment shape,
without ever declaring that shape a binding 1:1 schema.**

| Aspect | Alignment | Guard |
|---|---|---|
| Result field naming/nesting | Align with the extracted `4-final-result` example where harmless (`report_type`, `groups`, `num_sub_games`, `sub_games[]`, `final_result`, `mutual_agreement{sha256, confirmed}`, `links`, `timezone`) | Only where it does not conflict with a primary requirement |
| Static-metadata placement | **Adopt** the example's non-duplication convention — it agrees with Ch 9 p.78 + Table 20 | This is now our STRICT behaviour too (JDEC-014) |
| Per-sub-game fields | May add `roles`, `started_at`, `ended_at`, `winner_group`, `tie`, `audit` alongside our mandatory set | Mandatory fields (`github_commit`, `tokens`, scores, outcome) never dropped |
| Series fields | May add `sub_games_won`, `ties`, `series_tie`, `tokens_total_series`, `games_played_including_this`, `first_meeting_between_groups`, `diversity_reward_applied` | Values must derive from Appendix F; never invented scoring |
| Log filenames inside the result | **Always Table 20** (`log_<game_id>_g<NN>.json`) | The example's `police_match_S01R02G001.json` style **conflicts with Table 20 and is rejected** |
| Ed25519 | Accept `ED25519` as an `AuthProfile` if negotiated | Never marked SOURCE-MANDATORY; HMAC-SHA256 remains the project default |
| `_note` keys | A compatibility **parser** may accept explicitly negotiated metadata keys | Our **emitted** binding config excludes them; if present in a hashed config they participate in canonical bytes and **both peers must hold identical values**; they may never alter Appendix-F semantics |

## Profile selection rules

1. **STRICT_COUNTED_MATCH is the default** and is the only profile used to *emit* a
   counted-game artifact unless a deviation is explicitly negotiated pre-match and
   recorded as an NDEC.
2. **Compatibility profiles are primarily about what we ACCEPT**, not what we emit.
3. **Profiles are negotiated pre-match**, never switched mid-series.
4. A profile that would weaken a binding requirement is **rejected**, and the correct
   response is to **refuse counted play** rather than degrade.
5. Every active profile is recorded as evidence in the declaration/negotiation record so
   replay and reporting can reproduce the exact interpretation used.

## Architecture hooks (design only — no modules created)

| Concept | Purpose |
|---|---|
| `CompatibilityProfile` | Selects the active profile set; read-only at match time |
| `AuthProfile` | `HMAC_SHA256` (project default) · `ED25519` (attachment-compatibility) — plain SHA-256 is **not** a valid Step-0 producer-authentication profile |
| `CommitmentCodec` | `STRICT_PROJECT_COMMITMENT` (default) · `LECTURER_REFERENCE_COMMITMENT` (negotiated only) |
| `ResultProfile` | `STRICT_PROJECT_RESULT` (default) · `LECTURER_ATTACHMENT_COMPATIBILITY` |
| `SeriesLauncher` | Selects which independent role process runs each sub-game; **owns no game truth and is not a referee** |
