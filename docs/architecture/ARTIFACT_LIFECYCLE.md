# Artifact Lifecycle — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only. No artifact is produced yet.**

The four official artifact names are **locked** and must never be renamed
(`../spec/json/NAMING_AND_IDENTITY.md`).

| Artifact | Created | Writer | Immutable after | Canonicalized | Hash / auth relevance | Retention | In Git? | Submission evidence | Secret risk |
|---|---|---|---|---|---|---|---|---|---|
| `declaration_<game_id>.json` | Step-0, pre-game | `protocol.declaration` → `infra.artifacts` | exchange + verification | **Yes** | carries `step0_auth {auth_alg, key_id, auth_tag}`; `config_sha256` may be stored here | whole series | **Yes** (counted game) | **Yes** | `key_id` only — **never key bytes** |
| `config_<game_id>_g<NN>.json` | Config negotiation, per sub-game | `protocol.config_lock` | **`CONFIG_LOCKED`** | **Yes** (sorted keys, `(",",":")`, UTF-8, NFC, LF, no trailing NL) | three sections (Stage 5-R8): `config` = the 35-member core, `config_lock` = the authenticated `{context, auth}` evidence, `scent_model_evidence` = the full agreed model + `scent_model_sha256`. Both digests are computed over their own bytes and stored **outside** them | whole series | **Yes**, distinct name per game (App F §2.3–2.4) | **Yes** | none (`key_id` only — **never key bytes**) |
| `log_<game_id>_g<NN>.json` | Per sub-game, appended per turn | `infra.logger` | sub-game seal | **Yes** for hashed payloads | contains `H_commit` per turn; nonces appended **only at final audit** | whole series | **Yes** | **Yes** (replay) | nonce must not appear before audit |
| `result_<game_id>.json` | Series end | `infra.reporter` | after `result_sha256` agreed | **Yes** | `result_sha256` over the agreed core, stored **outside** the core | permanent | **Yes** | **Yes** (e-mailed as JSON attachment) | none |
| Replay/GUI evidence (screenshots, projection dumps) | On demand | `infra.gui` / operator | on write | no | none | as needed for submission | optional | possibly | must not show forbidden truth |
| Metrics (latency, retries, tokens, cost) | Continuous | `infra.metrics` | series end | no | none | series | aggregate only | tokens appear in result | none |
| Temporary files (scratch, partial writes) | Ad hoc | any writer | n/a | n/a | none | **deleted**; never committed | **No** (git-ignored) | no | must never hold secrets |

## Lifecycle rules

1. **Write-once, then sealed.** Once an artifact reaches its immutability point, it is
   never rewritten. Corrections create a new game/sub-game identity, never an edit.
2. **Atomic writes.** Write to a temporary file, fsync, then rename — a crash must never
   leave a half-written artifact that would fail replay.
3. **Canonical bytes for anything hashed.** Sorted keys, `(",",":")`, UTF-8, NFC, LF, no
   trailing newline (JDEC-002/NDEC-003). Cross-OS byte-identity is mandatory.
4. **Non-self-referential digests.** `config_sha256`, `result_sha256`, and every
   `auth_tag` are stored **outside** the bytes they cover.
5. **Identity binding.** All four artifacts of one game carry the same `game_id` **and**
   `game_uid`; filenames derive from `game_id`; `<NN>` is 2-digit (`g01`…`g06`) (INV-01/02, JDEC-004).
6. **Append-only logs.** The log grows forward; a rewritten log is `E-REPLAY-MISMATCH`
   ⇒ TAMPERED.
7. **Nonce timing.** Nonces enter the log **only** in the final-audit section.
8. **No secrets, ever.** No artifact contains key material, credentials, or tokens.
9. **Four-artifact-set self-containment (Stage 2A-R2).** Static game/team metadata
   (MCP endpoints, hardware specs, members, model, token cap, times) lives in the
   **declaration** (Ch 9 p.78; App F Table 20). The **result references** it via
   `game_uid`/`group_id` and does **not** duplicate it (JDEC-014, INV-10/12/13). The set
   — declaration + config + log + result — is what must be self-contained.
10. **Replay-sufficiency.** The artifact set alone must let an independent process verify
   the match with no live state and no network (REPLAY-001/002).

11. **Retention.** Counted-game artifacts are committed to the repository as delivery
    evidence; scratch is git-ignored and deleted.

12. **The config artifact is an envelope, not a fifth family (Stage 5-R8).** Its three
   sections are `config`, `config_lock` and `scent_model_evidence`, parsed by one strict
   schema that refuses an unknown member. A reader can recompute both identities from the
   bytes — `full model → scent_model_sha256 → the authenticated context` and, separately,
   `35-member core → config_sha256 → the same context` — which is what makes rule 10 true
   for the scent contract as well. **The stored `AuthProof` is not publicly verifiable:**
   it carries `key_id` and a tag, and checking authorship needs the out-of-band key, so the
   artifact proves internal consistency to anyone and authorship only to a key holder. The
   official set stays **four families / 14 files per series** (C-14, JDEC-017).
