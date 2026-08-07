# Cross-Artifact Invariants — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Invariants that must hold **across** the four artifacts. Each is classified by
provenance; none is invented without source support.

| ID | Invariant | Provenance | Source |
|---|---|---|---|
| **INV-01** | All four files of one game carry the same `game_id` **and** `game_uid`. | **SOURCE** — both identifiers are **named by the book** (Ch 9 p.95: "four files carry a shared `game_uid`"; filenames derive from `game_id`) | Ch 9 p.95; App F Tbl 20 |
| **INV-02** | `config` and `log` for the same sub-game carry the same `<NN>`/`sub_game`. | SOURCE-SEMANTIC (per-sub-game files; no mixing) | App F Tbl 20; App F §2.3 |
| **INV-03** | The `config_sha256` referenced in a `log` equals the hash of the exact `config` used to play that sub-game (played config = locked config). | SOURCE-SEMANTIC (byte-identical crypto-locked config; replay verifies against it) | Ch 3 p.34; Ch 5 p.127; App F §2.1 |
| **INV-04** | The `result` carries **four** GitHub links (both teams' police + thief), matching the repos declared in `declaration`. | SOURCE-SEMANTIC (four links required) | Ch 9 p.96; App E #49 |
| **INV-05** | The `github_commit` recorded in `declaration` (Step-0) for a game equals the `github_commit` reported for that game's sub-games in `result`. | SOURCE-SEMANTIC (played commit declared **and** reported; per-game update) | Ch 5 p.56; App E #53/#54; GIT-003 |
| **INV-06** | Every `log` entry's commitment recomputes: `SHA256(canonical(sealed_record)) == entries[].commit`; any mismatch ⇒ TAMPERED ⇒ game void. | SOURCE-EXPLICIT/SEMANTIC (recompute-and-compare) | Ch 5 §5.4; Ch 7 §7.4; App E #19 |
| **INV-07** | `result` scores derive from the played sub-games and use only Appendix F scoring values (capture/survival/tie) + the Ch 3/E-48 technical-loss 0/0. | SOURCE-SEMANTIC | Ch 9 p.95; App F T17; E-48; C-07 |
| **INV-08** | Both teams' `result` files for the same game **agree** on the outcome (mutual agreement); disagreement or one-sided report ⇒ game disqualified, 0 to both. | SOURCE-EXPLICIT rule | Ch 9 p.94; App E #35 |
| **INV-09** | The `config`'s `num_games` for a counted series is `6` (FIXED); the illustrative `1` is not used for counted games. | SOURCE (App F) | App F T18; C-05 (closed) |
| **INV-10** | **[CORRECTED Stage 2A-R2]** The **four-artifact set** is self-contained: `declaration` + `config` + `log` + `result` share one `game_uid`, and the `result` carries the identifiers, four GitHub links, per-sub-game commits/scores/tokens and agreement data needed to **join** the set. Static metadata (MCP endpoints, hardware, members) lives in the **declaration** and is referenced, **not duplicated**. | SOURCE-SEMANTIC (Ch 9 p.78 four-file list; App F Tbl 20 role split) | Ch 9 p.78–79; App F Tbl 20; App E #49/#54 |
| **INV-11** | Both teams' `result` reports must be **present and matching** — equal `result_sha256`, `mutual_agreement:true`. A required report **missing from either side** **or** **contradictory** reports ⇒ **game invalid, 0 to both** (strictest rule). | SOURCE-EXPLICIT rule; **Ch 9 vs E-35 severity resolved by C-09** | Ch 9 p.94; App E #35; **C-09** |
| **INV-12** | **[RETARGETED Stage 2A-R2]** Each team's **FastMCP/MCP endpoint** is recorded in the **`declaration`** (Ch 9 p.78 assigns MCP addresses to the declaration). The `result` references it via `game_uid`/`group_id`; it is **not duplicated** in the result. | SOURCE-SEMANTIC | Ch 9 p.78; App F Tbl 20 |
| **INV-13** | **[RETARGETED Stage 2A-R2]** Each team's **hardware declaration** and its **keyed-authentication evidence** (`step0_auth {auth_alg,key_id,auth_tag}`) live in the **`declaration`** (Ch 9 p.78; Ch 5 p.55–56). The `result` references them via `game_uid`; they are **not duplicated** in the result. **No key material** crosses any artifact. | SOURCE-SEMANTIC + PROJECT primitive | Ch 9 p.78; Ch 5 p.55–56 |
| **INV-14** | For each sub-game, the `declaration` Step-0 `step0_auth.auth_tag` verifies against the pre-supplied key referenced by `key_id` over `"step0" ‖ canonical(Step-0 core)`; failure ⇒ **refuse counted play** (pre-game). | SOURCE-REQUIRED (signed Step-0, K1) + PROJECT primitive (JDEC-013) | Ch 5 p.55–56; NDEC-005 |
| **INV-15** | For each sub-game, the `config` authentication `auth_tag` verifies over `"config" ‖ canonical(config core)` **and** both peers' `config_sha256` are equal; either failure ⇒ **refuse counted play** (pre-game). | SOURCE-REQUIRED (signature exchange, K2) + PROJECT primitive (JDEC-013) | App B p.128; NDEC-004/007 |

## Provenance tags (Stage 1D / 1D.1)

INV-01 **SOURCE** · INV-02 SOURCE · INV-03 SOURCE (mechanism) + PROJECT (hash storage, JDEC-010) · INV-04 SOURCE · INV-05 SOURCE · INV-06 SOURCE · INV-07 SOURCE · INV-08 SOURCE · INV-09 SOURCE · **INV-10 SOURCE · INV-11 SOURCE (C-09) · INV-12 SOURCE · INV-13 SOURCE + PROJECT primitive · INV-14 SOURCE-REQUIRED + PROJECT primitive · INV-15 SOURCE-REQUIRED + PROJECT primitive**. `game_uid` equality is **retained** (it is source-named — D3, not retired). The keyed-auth invariants (INV-13/14/15) reference **only** the non-secret `key_id`/`auth_tag`; **no key material** is asserted to exist in any artifact.

## Notes

- INV-03/INV-05/INV-06/INV-08 are the integrity/anti-fraud backbone (H-02, H-03,
  H-04, H-08 in `HIGH_RISK_REQUIREMENTS.md`); **INV-11/INV-13/INV-14/INV-15** extend
  it with the reporting-sanction (C-09) and keyed-authentication (K1/K2/K3) rules.
- **Not invented:** no cross-file equality is asserted beyond what the book
  supports. Where the book is silent (e.g., exact signature storage), that is
  handled as REVIEW-REQUIRED in `SIGNATURE_AND_HASH_PROVENANCE.md`, **not** as an
  invented invariant.
