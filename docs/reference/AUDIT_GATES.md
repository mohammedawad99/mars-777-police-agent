# The two audit gates — evidence

Every counted sub-game is checked twice, by two different kinds of reasoning,
and the distinction is load-bearing: the first gate asks *"were these the bytes
you committed to?"*, the second asks *"could this game have happened at all?"*.
A transcript can pass the first and fail the second, which is exactly the case
worth catching — a peer that reveals honestly-hashed nonsense.

Both run locally on disclosed evidence. Neither needs the opponent to cooperate
beyond disclosing what the protocol already requires.

---

## Gate 1 — cryptographic commitment verification

**Question.** For every disclosed turn, does the commitment we were sent earlier
equal the hash of the payload and nonce revealed later?

| | |
|---|---|
| Authority | `app/audit_runtime.py`, `app/commitment_codec.py` |
| Inputs | the peer's per-turn commitments, its disclosed payloads, its `final_nonce_reveal` batch, the locked commitment codec |
| Computation | recompute `H(canonical(payload) ‖ nonce)` and compare to the commitment received **before** the reveal |
| Outputs | `VERIFIED` · `FAILED` · `NOT_CHECKABLE` |
| `NOT_CHECKABLE` when | the nonce for that `(step, role)` was never disclosed — recorded honestly rather than assumed innocent or assumed guilty |

**Source-binding.** The commit-then-reveal requirement and the "verify before
accepting" rule are book-mandated. The canonical byte framing is a
**project-frozen** decision recorded in `CANONICALIZATION_CONTRACT.md`, because
the source under-specifies it; a peer using another framing must negotiate it.

**A real defect this gate's evidence exposed.** A nonce lookup keyed by `step`
alone let the peer's nonce overwrite our own, producing a false `TAMPERED`
accusation against an honest opponent. The key is now `(step, role)`, and a
missing nonce yields `NOT_CHECKABLE` rather than a verdict. Accusing a
well-behaved peer of cheating is a worse failure than missing a cheat, and it is
tested as such.

---

## Gate 2 — semantic verification

**Question.** Given the authenticated config, the agreed geometry and the
disclosed transcript, is the sequence of actions one that could actually have
been played?

| | |
|---|---|
| Authority | `app/semantic_replay.py`, driven by `app/semantic_review.py` |
| Inputs | the locked `NegotiatedConfig` (grid, quota, horizon), both opening cells, every disclosed turn, the public barrier set per step |
| Computation | replay each turn against the board that actor really had, using the **same** `domain` rules production plays with |
| Outputs | `CONSISTENT` and eight refusal verdicts |

**The refusal verdicts, and what each one means:**

| verdict | caught when |
|---|---|
| `WRONG_START` | first disclosed cell is not the agreed opening |
| `BROKEN_TRAJECTORY` | a later cell does not follow from the previous action |
| `WRONG_BARRIER_SET` | the disclosed board disagrees with the barriers actually declared |
| `ILLEGAL_ACTION` | the action is not accepted by `domain.rules` / `domain.barriers` from that cell |
| `FALSE_CAPTURE_CLAIM` | a capture was declared that the replay does not produce |
| plus the tampering family | commitment/semantic contradictions |

**One ordering rule is what makes this fair.** Within a step both sides seal
before either reveals, so an actor could not have seen the opponent's same-step
placement. The replay therefore judges each turn against `board_after` — the
board that actor had once its **own** action landed — never against the combined
end-of-step board. Judging against the combined board would test a world the
actor never inhabited and would fail honest peers.

**`ILLEGAL_ACTION` is not theoretical.** Stage 9B-2 produced one in CI: an
integration harness handed this repository's police policy to a thief-role
actor, and the gate correctly refused a `BAR-004` placement from a thief,
recording `at_fault: thief`. The gate found a real defect that a green test
suite had missed.

---

## Blocking semantics for counted play

| condition | consequence |
|---|---|
| Gate 1 `FAILED` | counted-clean is refused; the finding is binding |
| Gate 2 anything but `CONSISTENT` | counted-clean is refused; provenance recorded in `audit_provenance.py` |
| Gate 1 `NOT_CHECKABLE` | recorded, not treated as pass and not treated as cheating |
| both clean | the sub-game may be closed and its result agreed |

A verdict is **evidence in the log**, not an accusation sent to the peer. The
project never emits a cheating claim on a wire; it records what it could and
could not verify, and refuses to certify what it could not.

---

## Evidence artifacts

Deterministic, produced by the test suite rather than by narration:

- `tests/audit/` — Gate 1 recomputation, the `(step, role)` nonce keying, and
  `NOT_CHECKABLE` on an undisclosed nonce.
- `tests/semantic/` — every Gate 2 verdict, each with a transcript constructed to
  trigger exactly that verdict and no other.
- `tests/series_lifecycle/`, `tests/boot/` — six real sub-games per side, each
  closing with `CONSISTENT` in a written `log_*.json`.
- `docs/evidence/gui/replay_verified.png` — the Replay Viewer showing a verified
  post-audit transcript.

**No external opponent audit is claimed.** Every artifact above comes from our
own processes or a pinned third-party kit. A counted audit against another
group's live agent is partner-dependent and has not occurred.
