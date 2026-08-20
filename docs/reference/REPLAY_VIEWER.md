# Replay Viewer — group MaRs-777

**Status: CURRENT.** Added at Stage 9A-2A.

`REPLAY-001` requires a viewer that replays a game log **and cryptographically
verifies it**, and Appendix E rule 20 makes it a threshold for approving audits
and for submission. This is that viewer.

## 1. Running it

```bash
uv run python -m mars777_police.replay_main \
    --log    artifacts/police/log_<game_id>_g01.json \
    --config artifacts/police/config_<game_id>_g01.json
```

| Option | Meaning |
|---|---|
| `--log` | an official sub-game log |
| `--config` | the config artifact that log names |
| `--root` | an evidence root every path must stay inside |
| `--summary` | print the verdict only, for CI or a grader |
| `--step N` | print one step instead of all of them |

## 2. Exit status

| Code | Meaning |
|---|---|
| `0` | the replay ran and everything it could check verified |
| `2` | the evidence could not be read or replayed — a local refusal, printed as a sentence, never as a traceback |
| `3` | the replay ran and **found something**: a digest that did not correspond, or a step the rules say could not have happened |

A grader can gate on `3` without reading a word of output.

## 3. What the board shows

```
P police   T thief   # barrier   . empty   ! both
```

`!` is not decoration: the capture rules make one cell holding both agents
meaningful, so it gets its own symbol rather than an arbitrary precedence.

## 4. How to read the verification column

| Status | Meaning |
|---|---|
| `Verified OK` | the recomputed digest equals the stored commitment (`REPLAY-002`'s own words) |
| `TAMPERED` | the recomputed digest differs. Immediate disqualification, no appeal |
| `NOT_CHECKABLE` | a commitment exists but its nonce was never disclosed to this side |
| `NOT_APPLICABLE` | this record carries no commitment to check |

`NOT_CHECKABLE` is **never** rendered as `Verified OK`. Missing evidence is not
proof, and calling it tampering would be the opposite error.

The **semantic** line is a separate question, from a separate authority: whether
the disclosed trajectory could have happened at all — start cell, movement
legality, barrier set, capture honesty. A sub-game can be cryptographically
`Verified OK` and semantically inconsistent, or the reverse, and the viewer
shows both rather than one summary word.

## 5. What it can and cannot replay

**Official artifacts.** A sub-game log plus the config artifact it names. The
config is checked against the log before a single step is replayed: if it does
not hash to the `config_sha256` the log records, the two files do not describe
the same sub-game and the viewer refuses them.

**Development (friendly) evidence cannot be replayed, by construction.** A
friendly contribution carries settled facts only — outcomes, step counts,
commitment chains — and its own contract states that it *"deliberately cannot
carry a board, a position, a barrier set or a nonce"*. There is nothing to
reconstruct a board from, so the viewer refuses it and says why rather than
inventing the missing half.

**Authorship is not claimed.** A reader without the provisioned key can verify
every digest and every rule; it cannot verify who signed the configuration, and
the viewer says so instead of implying a guarantee it did not check.

## 6. Partial replay policy

- **Structural corruption stops the replay.** Bytes that are not JSON, a missing
  file, an absent `entries` list, a commit with no step or no sealed state: the
  viewer refuses, because continuing would require inventing state.
- **A verification failure does not stop it.** A `TAMPERED` digest or an
  inconsistent step is a *finding*, so every remaining step is still shown —
  forensic mode — and the summary marks the whole replay accordingly. Nothing is
  invented to continue: the later steps are the disclosed values, replayed.

## 7. Security model

The viewer is the one place this project reads files somebody else may have
written.

- `--root` confines every path; containment is checked **after** resolution, so a
  symlink pointing outside the root is refused by the same rule as `../`.
- Files are size-bounded (8 MB) before they are read.
- Parsing is `json` only — no `pickle`, no `eval`, no `exec`, no import of
  anything the evidence names.
- No secret is printed: the viewer shows disclosed evidence, never key material,
  never a private belief, never an internal runtime object.

## 8. What it is not

It is not a second game engine. Legality comes from `domain.rules` and
`domain.barriers`, trajectory consistency from `app.semantic_replay` — the same
engine the live audit used — and the digest from the commitment port. A
structural test asserts the viewer computes no hash of its own and imports no
rule module. A replay that judged for itself could disagree with the audit, and
the disagreement would be indistinguishable from a real finding.

The graphical interface `GUI-001/002/003` requires is a separate requirement and
a later stage; it will consume this same replay projection rather than a second
one, and **this terminal viewer is not counted as the GUI screenshot `DOC-001`
still needs**.
