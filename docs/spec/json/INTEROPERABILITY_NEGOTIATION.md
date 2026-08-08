# Interoperability Negotiation Contract (NDEC) — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every legitimate **NEGOTIATED-PRE-MATCH** dependency — representations two peers
must agree on to complete/verify a counted match. **Not** used to negotiate FIXED
Appendix F values, to weaken MINIMUM values, or to avoid fixing project contracts
that can safely be locked. Each has a PROJECT-LOCKED **default** so agreement is
usually just confirmation.

| NDEC | Item | Default (project-locked) | Allowed alternatives | Exchange | Both-peer ack | Lock / immutability | Identity/hash reference | If no agreement | Counted play? |
|---|---|---|---|---|---|---|---|---|---|
| **NDEC-001** | Sealed commitment-record composition | fields `{state, move, intent, hint, step, role, sub_game, nonce}`, keys sorted, `intent` carries the truth/lie "verdict" (no separate `verdict`) | reorder is irrelevant (sorted keys); adding/removing a field is **not** allowed unless both agree | in the pre-match config/declaration exchange | echo the agreed field list | frozen for the series; referenced by `config_sha256` context | recorded in declaration | **no counted play** | requires agreement |
| **NDEC-002** | `state` representation in the sealed payload | `{config_sha256, self_pos:[r,c], barriers:[[r,c]…] sorted, step, role}` (own-known only; no opponent truth) | any deterministic superset **both** accept | pre-match | echo | frozen for the series | via `config_sha256` | no counted play | requires agreement |
| **NDEC-003** | Canonicalization parameters | `sort_keys=true`, `separators=(",",":")`, UTF-8, `ensure_ascii` agreed value, LF, no trailing newline in hashed payload, locale-independent numbers | any deterministic serializer both accept | pre-match | echo | frozen for the series | — | no counted play | requires agreement |
| **NDEC-004** | Config equality + MINIMUM/NEGOTIABLE values + `schema_version` value | App F floors/defaults; `schema_version` = `"mars777-1"` | raise MINIMUMs; any NEGOTIABLE both accept (**never** below floor; **never** change FIXED) | exchange full config; both compute `config_sha256` | compare `config_sha256` (must be equal) | byte-identical signed config; hash locked | `config_sha256` (stored in declaration/sidecar) | **refuse to play** | requires equal hash |
| **NDEC-005** | **Step-0 keyed authentication** (K1) | **HMAC-SHA256** over `"step0" ‖ canonical(Step-0 core)`, pre-shared key by `key_id` (JDEC-013); envelope `{auth_alg,key_id,auth_tag}` in the declaration | asymmetric signature if both agree (source requires **keyed** auth, not HMAC) | key **out-of-band/pre-supplied**; envelope in declaration | verify each other's `auth_tag`; `key_id` matches | frozen per game; **key never in any artifact** | `auth_tag` (non-self-referential) | **refuse counted play** if no compatible key/mechanism | requires shared key + verified tag |
| **NDEC-006** | Result-approval hashing | SHA-256 over the canonical **RESULT APPROVAL CORE** — `game_id`, `game_uid`, `declaration_ref`, team `group_id`s, four GitHub links, per-sub-game {`sub_game`, scores, `outcome`, `github_commit`, `tokens`}, `cumulative`, `total_tokens`, `timestamp` — **excluding** `result_sha256` itself, the `mutual_agreement` flag and any reporter-local presentation metadata (**Stage 2A-R2**: static declaration-owned metadata is referenced, not included). Both peers build that core independently, each computes `result_sha256`, the two digests are exchanged and compared, and **only once they are equal** does each local result record carry the identical `result_sha256` **and**, as a **separate top-level field**, `mutual_agreement = true` *(Stage 4E-R2-FIX1: this cell previously wrote `mutual_agreement.sha256` and `mutual_agreement.confirmed = true`, the nested object form `RESULT_CONTRACT.md` withdrew at Stage 4F-R1 in favour of the bool its field table, scoring rule and JSON example define; the exclusion semantics and the 11-field result count are unchanged, and no replacement nested object is introduced)* | any hash both accept | dual result emails | both `result_sha256` equal | frozen at report time | `result_sha256` (non-self-referential) | **0 to both** (E-35, C-09) | requires equal hash |
| **NDEC-007** | **Config keyed authentication (signature exchange)** (K2) | **HMAC-SHA256** over `"config" ‖ canonical(config core)`, pre-shared key by `key_id` (JDEC-013; same-or-distinct key from Step-0 unspecified → agree pre-match); envelope in a config sidecar | asymmetric signature if both agree | key out-of-band; envelope in sidecar | verify tag + `config_sha256` equality | frozen per sub-game; key never stored | `auth_tag` (non-self-referential; distinct `context` from Step-0) | **refuse counted play** on bad tag/hash mismatch | requires verified tag + equal hash |

## Rules

- **FIXED Appendix F values are never negotiated** here; **MINIMUM values only rise**;
  these NDECs cover *representation*, not the binding physics numbers.
- Defaults are PROJECT-LOCKED so that, with a compliant opponent who accepts them,
  no per-match negotiation is strictly required beyond confirming equality.
- Detection is a **hash/tag comparison** (config, commitment, result, keyed auth);
  failure behaviour is refuse-to-play (pre-game) or disqualify/0-both (report).
- **Keyed authentication (NDEC-005/007)** uses a **pre-supplied out-of-band key**
  (JDEC-013); **no key material** appears in any artifact — only a `key_id`. The
  source requires keyed authentication (Ch 5 p.55–56; App B p.128); the algorithm
  (HMAC-SHA256 default) is our choice. If the two sides cannot establish a
  compatible key/mechanism, **counted play is refused**.
- IDs NDEC-001…NDEC-007, unique.
- **NDEC-006 scope limit (Stage 4E-R2-FIX1).** NDEC-006 freezes the result-approval
  **procedure** (build the core → compute `result_sha256` → exchange → compare → set
  `mutual_agreement`) and the **result-record shape** (two separate fields). It does
  **not** freeze the Event-14 *peer-message* flow: whether the exchange is one message,
  request/response, offer + confirm, a digest echo or another pattern; whether the
  semantic message carries `game_id`/`game_uid` or relies on session context; and
  whether disagreement is signalled by `false` or by absence plus the `E-REPORT-DISAGREE`
  / C-09 path. Those remain unfrozen, so the peer-visible **Mutual result agreement**
  family stays `BLOCKED-BY-PAYLOAD-SHAPE`. A record shape is not a message shape.
