"""Knowing *when* this side's final audit is complete, without owning the fact.

A sub-game cannot be closed until this process has accepted the peer's audit
disclosure - `semantic_review` needs the peer's own positions and refuses
without them. In one interpreter that ordering arrived for free, because both
drivers interleave in a single event loop. Two independent OS processes do not
provide it: whichever reaches closure first finds `disclosure` still `None` and
raises `E-LOCAL-DEFECT`.

So the audit gains a **signal**, not a second truth. `AuditRuntime` still owns
the nonce batch, the disclosure, the verdict and the phase; the event only says
that all of them are already installed - which is why it is set last.

**One signal is enough, and the existing contract is why.** A disclosure is
refused unless the phase is `AWAITING_DISCLOSURE`, and only the accepted nonce
batch moves the phase there. `COMPLETE` therefore implies both arrivals, in
order, so no separate `final_nonce_seen` event has to exist.
"""

import asyncio

import audit_builders as build
import pytest

from mars777_police.app.audit_values import AuditPhase
from mars777_police.app.capture_transcript import TranscriptMismatchError
from mars777_police.app.protocol_errors import StaleMessageError


def test_a_disclosure_before_the_nonce_batch_is_refused_and_never_signals() -> None:
    """The invariant the single-signal design rests on, stated as a test."""
    audit = build.runtime()
    assert audit.phase is AuditPhase.AWAITING_NONCES

    with pytest.raises(StaleMessageError, match="cannot arrive while"):
        audit.accept_audit_disclosure(build.document())

    assert audit.disclosure is None
    assert not audit.milestones.complete.is_set()


def test_the_nonce_batch_alone_does_not_complete_the_audit() -> None:
    """Half the peer's material is not the peer's material."""
    audit = build.runtime()
    audit.accept_final_nonce_reveal(build.nonce_batch(), build.PEER_GROUP)

    assert audit.phase is AuditPhase.AWAITING_DISCLOSURE
    assert not audit.milestones.complete.is_set()


def test_the_state_is_installed_before_the_signal_is_set() -> None:
    """A waiter woken by the event can read everything it came for."""
    audit = build.runtime()
    audit.accept_final_nonce_reveal(build.nonce_batch(), build.PEER_GROUP)
    assert audit.disclosure is None

    audit.accept_audit_disclosure(build.document())

    assert audit.disclosure is not None
    assert audit.outcome is not None
    assert audit.phase is AuditPhase.COMPLETE
    assert audit.milestones.complete.is_set()


def test_a_disclosure_that_arrived_first_is_not_missed() -> None:
    """`asyncio.Event` latches, so waiting after the fact returns at once."""
    audit = build.runtime()
    audit.accept_final_nonce_reveal(build.nonce_batch(), build.PEER_GROUP)
    audit.accept_audit_disclosure(build.document())

    async def wait_after_the_fact() -> None:
        await asyncio.wait_for(audit.milestones.complete.wait(), 0.1)

    asyncio.run(wait_after_the_fact())


def test_a_refused_disclosure_leaves_the_signal_clear() -> None:
    """Only an accepted disclosure completes an audit; a rejected one changes nothing."""
    audit = build.runtime()
    audit.accept_final_nonce_reveal(build.nonce_batch(), build.PEER_GROUP)

    with pytest.raises(TranscriptMismatchError):
        audit.accept_audit_disclosure(build.document(steps=(1,)))

    assert audit.phase is AuditPhase.AWAITING_DISCLOSURE
    assert not audit.milestones.complete.is_set()
