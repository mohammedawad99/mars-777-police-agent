# Data Flow and Privacy Flow — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

Tags: **PRI**=private/local · **PUB**=public/shared · **OPP**=opponent-supplied
(untrusted until validated) · **DER**=derived · **PER**=persisted · **HSH**=hashed ·
**AUT**=keyed-authenticated.

## 1. Startup / Step-0

| Step | Data | Tags |
|---|---|---|
| Load local settings + key from env | settings; **key material** | PRI (key never leaves process, never PER) |
| Build Step-0 core (hardware, OS/CPU/RAM/GPU, model, code version, `github_commit`, token cap, identities, times) | Step-0 core | PUB, PER |
| Compute `step0_auth` over `"step0" ‖ canonical(core)` | `{auth_alg, key_id, auth_tag}` | AUT, PER (**key not stored**) |
| Exchange with peer; verify peer tag | peer Step-0 + tag | OPP → validated PUB |
| Persist | `declaration_<game_id>.json` | PER |

**Failure:** no compatible key/mechanism ⇒ **refuse counted play** (INV-14).

## 2. Config negotiation → lock

| Step | Data | Tags |
|---|---|---|
| Propose MINIMUM/NEGOTIABLE values (FIXED never touched) | proposed config | PUB |
| Canonicalize config core | canonical bytes | PUB |
| Compute `config_sha256` (unkeyed) | digest | HSH, PER (stored **outside** core) |
| Compute config auth tag over `"config" ‖ core` | tag | AUT, PER |
| Exchange; compare hash **and** verify tag | peer hash/tag | OPP → validated |
| Lock (immutable) | locked config | PUB, PER |

**Failure:** hash inequality **or** bad tag ⇒ refuse counted play (INV-15).

## 3. Per-turn decision

```
domain.truth (PRI) ─┐
domain.barriers(PUB)├─► domain.observation ──► Observation (role-legal) ──► StrategyPort
domain.scent  (PUB) │                                                          │
domain.belief (DER) ┘                                                          ▼
                                                              ProposedAction (PRI, pre-commit)
                                                                               │
                                                          domain.rules validator (deterministic)
                                                                               │ accept
                                                                               ▼
                                                                   sealed record fields
```

**Privacy proof (strategy).** `Observation` is constructible **only** from
LOCAL-TRUTH + PUBLIC + BELIEF + *validated* OPPONENT-PROVIDED. Opponent true position
is never received over the wire and therefore has no source in this process — the
strategy cannot read what does not exist here (GUI-001/002, ARCH-002).

## 4. Commit → Ack → Reveal

| Step | Data | Tags |
|---|---|---|
| Draw nonce (CSPRNG) | nonce | **PRI/secret until audit** |
| Seal `{state, move, intent, hint, step, role, sub_game, nonce}` | sealed record | PRI |
| `H_commit = SHA256(canonical(sealed))` | digest | HSH, PUB, PER |
| Send commit | `H_commit` only | PUB |
| Receive ack | ack | OPP → validated, PER |
| Reveal (move + hint; **nonce withheld**) | reveal | PUB after send, PER |
| Receive peer reveal | peer move/hint | OPP → validated |
| Validate legality/capture | verdict | DER, PER |
| Final audit: disclose audit material (full log incl. nonces), recompute every `H_commit` | audit material + nonces | PUB at audit, PER |
| Final audit: local verdict from that recomputation *(4E-R10-R1)* | `FinalAuditVerdict` | **DER, PER — local; never transmitted** (C-11) |

**Privacy proof (nonce).** Exactly one custodian (`protocol.commitment`) and one
release point (`FINAL_AUDIT`). No log, GUI event, report, or LLM prompt path can read
it earlier (CRYPTO-002/010).

## 5–7. Scent, barriers, score

| Flow | Data | Tags |
|---|---|---|
| Scent update | own reading from signed field params (0.9 / 0.10 / 5) | PUB, DER, PER |
| Barrier update | declared placement, quota, irreversibility | PUB (openly declared), PER |
| Score update | outcome → Appendix F values (+ technical_loss 0/0, C-07) | DER → PUB, PER |

## 8. Log / replay evidence

Logger receives **events**, not the live aggregate. Records: config hash ref, per-turn
commit/ack/reveal, validation verdicts, final nonces, audit result. Append-only,
canonical bytes. Replay reads **files only** and recomputes independently.

**Never logged:** key material, credentials, LLM API keys, opponent forbidden truth,
nonce before audit.

## 9. GUI projection

```
app events ──► GuiProjectionPort ──► view model ──► render
```
Carries: own position, public barriers, own scent view, **belief labelled as belief**,
step, score, protocol status. **Never** the objective board or opponent true position
(GUI-001/002). GUI has no write path.

## 10. Result construction

Assembles from **sealed artifacts**: identities, four GitHub links, FastMCP endpoints,
hardware declaration + `hardware_auth` evidence, per-sub-game scores/outcome/commit/
tokens, cumulative, total tokens, timestamp, `mutual_agreement`, `result_sha256`
(computed over the agreed core, stored outside it). Self-contained (INV-10/12/13).

## 11. Gmail reporting

```
result_<game_id>.json (sealed) ──► ReportPort ──► e-mail with JSON attachment
```
One-way. Cannot mutate game state. Both teams must send matching reports; missing from
either side **or** contradictory ⇒ **0 to both** (C-09, INV-11).

## Privacy assertions (enforced by tests)

| Assertion | Enforcement |
|---|---|
| No opponent private truth reaches **strategy** | `Observation` has no such field; contract test |
| …reaches **GUI** | the live view is projected from `Observation` itself, so no field one could arrive in exists; `tests/gui/test_live_projection.py` asserts the field set, and `tests/gui/test_gui_privacy.py` asserts that no live module so much as names the objective board state. The replay view may show it, and only after the audit point (`PRD07-FR-023`) |
| …reaches **logs** | Logger schema whitelist; negative test scans log for forbidden keys |
| …reaches **reports** | Reporter reads sealed artifacts only; schema test |
| Nonce not disclosed before audit | Timeline test asserts absence in all pre-audit outputs |
| No secret in any artifact | Repository-gate secret scan (SEC-003/004) |
