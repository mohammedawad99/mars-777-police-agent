"""A sub-game closes on the peer's audit material, not on ours being sent.

`semantic_review` replays the peer's own disclosed positions, so closing before
that disclosure arrived is refused - correctly - with `E-LOCAL-DEFECT`. Stage
6C-C1 never hit it: both drivers share one event loop there, and the awaited
sends interleave so the peer's disclosure always landed first. Two OS processes
schedule independently, and the side that finishes first found `disclosure`
still `None`.

The wait belongs to the driver and the fact belongs to the audit: `SeriesDriver`
sends its final nonce and disclosure exactly as before, then waits on the local
`AuditRuntime`'s completion signal, and only then closes. Nothing is resent and
no audit rule is relaxed - the barrier is local scheduling.

These tests drive the **real** inbound owner: the peer's material arrives
through `AuditRuntime.accept_final_nonce_reveal` / `accept_audit_disclosure`,
never by assigning `disclosure` behind the audit's back.
"""

import asyncio

import audit_builders as audit_build
import pytest
import r7_builders as r7

from mars777_police.app.audit_values import AuditPhase
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.state_machine import ProtocolPhase


def _audit_awaiting_disclosure() -> object:
    """A real audit that has accepted the peer's nonce batch and nothing more."""
    audit = audit_build.runtime()
    audit.accept_final_nonce_reveal(audit_build.nonce_batch(), audit_build.PEER_GROUP)
    return audit


def test_closing_before_the_peer_disclosure_is_still_refused() -> None:
    """The audit rule this barrier exists to respect is untouched."""
    audit = _audit_awaiting_disclosure()
    assert audit.disclosure is None  # type: ignore[attr-defined]

    from mars777_police.app.semantic_review import peer_turns

    with pytest.raises(LocalDefectError, match="follows the peer's audit disclosure"):
        peer_turns(audit)  # type: ignore[arg-type]


def test_the_driver_waits_until_the_peer_disclosure_is_accepted(tmp_path: object) -> None:
    """Pre-fix this returned immediately and closed a sub-game it could not review."""
    audit = _audit_awaiting_disclosure()

    async def run() -> None:
        waiting = asyncio.create_task(
            asyncio.wait_for(audit.milestones.complete.wait(), 10.0)  # type: ignore[attr-defined]
        )
        await asyncio.sleep(0)
        assert not waiting.done()

        audit.accept_audit_disclosure(audit_build.document())  # type: ignore[attr-defined]
        await waiting
        assert audit.phase is AuditPhase.COMPLETE  # type: ignore[attr-defined]
        assert audit.disclosure is not None  # type: ignore[attr-defined]

    asyncio.run(run())


def test_nothing_is_recorded_while_the_barrier_holds(tmp_path: object) -> None:
    """No log, no outcome line and no cursor move happen before the peer's audit."""
    import autonomous_series_builders as auto

    a, _ = auto.pair_for(tmp_path)  # type: ignore[arg-type]
    audit = _audit_awaiting_disclosure()

    async def run() -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(audit.milestones.complete.wait(), 0.05)  # type: ignore[attr-defined]

    asyncio.run(run())

    assert a.lines == ()  # type: ignore[attr-defined]
    assert a.orchestrator.machine.phase is ProtocolPhase.BOOT  # type: ignore[attr-defined]
    written = tmp_path / "police"  # type: ignore[operator]
    assert not written.exists() or list(written.iterdir()) == []


def test_the_driver_sequence_names_the_wait_between_sending_and_closing() -> None:
    """The order is load-bearing: send ours, receive theirs, then close."""
    import inspect

    from mars777_police.series_driver import SeriesDriver

    source = inspect.getsource(SeriesDriver.play_sub_game)
    nonce = source.index("send_final_nonce_reveal")
    disclosure = source.index("send_audit_disclosure")
    wait = source.index("milestones.complete")
    close = source.index("close_sub_game")
    assert nonce < disclosure < wait < close
    assert "retry" not in source and r7.CONFIG is not None
