"""What two real processes do when they cannot agree, or cannot meet.

A peer that never appears has to fail inside its budget rather than hang; one
that starts second has to be joined anyway; and two legal-but-different boot
configurations have to be refused by the config lock rather than resolved by
preference.
"""

from pathlib import Path

import executable_evidence as evidence
import executable_outcome as outcome
import executable_process as process
from boot_builders import SECRET, free_port
from test_two_process_series import _roots

from mars777_police.app.sealed_record_values import ActorRole

"""The negotiated response and watchdog bounds a normal series locks.

Read back from the artifact rather than trusted from the fixture: an agent that
shipped one deadline and locked another would still write a config file, and
this is the file both sides then hold each other to.
"""
REAL = "real CLI"
PEER = "synthetic opponent"
"""The two sides, named once so a diagnostic says which process it is quoting."""


def test_a_peer_that_never_appears_fails_inside_its_budget(tmp_path: Path) -> None:
    """Bounded, non-zero, clean - and nothing official is written."""
    ours_root, _ = _roots(tmp_path)
    port = free_port()
    launch = process.written_launch(tmp_path)
    environment = process.environment(
        port, root=ours_root, opponent=f"http://{process.HOST}:{free_port()}/mcp"
    )
    child = process.spawn("mars777_police", launch, environment)
    assert outcome.await_application(child, port) == process.NOT_ACCEPTABLE
    ours = outcome.finished(REAL, child, timeout=300)

    assert SECRET not in ours.out and SECRET not in ours.err
    report = evidence.two_process_report((ours,), ((REAL, ours_root),))
    assert ours.status == 4, report
    assert "never became reachable" in ours.err, report
    assert not outcome.crashed(ours.err), report
    assert evidence.official(ours_root) == [], report


def test_the_startup_retry_joins_an_opponent_that_starts_second(tmp_path: Path) -> None:
    """The race, deterministically: our process is answering before theirs exists.

    No sleep decides anything - the parent waits for the real `/mcp` response
    from the first child, which is only possible once its ASGI stack is up, and
    only then starts the peer. The first child must therefore have failed at
    least one connection attempt and retried.
    """
    ours_port, theirs_port = free_port(), free_port()
    ours_root, theirs_root = _roots(tmp_path)
    launch = process.written_launch(tmp_path)
    environment = process.environment(
        ours_port, root=ours_root, opponent=f"http://{process.HOST}:{theirs_port}/mcp"
    )
    child = process.spawn("mars777_police", launch, environment)
    opponent = None
    try:
        assert outcome.await_application(child, ours_port) == process.NOT_ACCEPTABLE
        assert child.poll() is None
        opponent = process.spawn_opponent(
            ActorRole.THIEF.value,
            theirs_port,
            f"http://{process.HOST}:{ours_port}/mcp",
            theirs_root,
        )
        assert outcome.await_application(opponent, theirs_port) == process.NOT_ACCEPTABLE
        assert child.poll() is None
    finally:
        for one in (child, opponent):
            if one is not None and one.poll() is None:
                one.kill()
                one.communicate(timeout=10)


def test_two_legal_but_different_boot_configs_are_refused_by_the_lock(tmp_path: Path) -> None:
    """A NEGOTIABLE difference is refused where it always was, across processes.

    Both sides boot with a fully legal config; only `hint_max_words` differs, so
    nothing FIXED is bent to manufacture the disagreement. Step-0 still
    succeeds and the proposal exchange still happens - convergence is decided one
    step later, when `ConfigLockRuntime` recomputes *our* digest of *our* config
    and refuses evidence naming a different one.
    """
    ours_port, theirs_port = free_port(), free_port()
    ours_root, theirs_root = _roots(tmp_path)
    launch = process.written_launch(tmp_path)
    environment = process.environment(
        ours_port, root=ours_root, opponent=f"http://{process.HOST}:{theirs_port}/mcp"
    )
    child = process.spawn("mars777_police", launch, environment)
    opponent = process.spawn_opponent(
        ActorRole.THIEF.value,
        theirs_port,
        f"http://{process.HOST}:{ours_port}/mcp",
        theirs_root,
        variant="other",
    )
    try:
        ours = outcome.finished(REAL, child, timeout=300)
        theirs = outcome.finished(PEER, opponent, timeout=120)
    finally:
        for one in (child, opponent):
            if one.poll() is None:
                one.kill()
                one.communicate(timeout=10)

    assert SECRET not in ours.out and SECRET not in ours.err
    assert SECRET not in theirs.out and SECRET not in theirs.err
    report = evidence.two_process_report((ours, theirs), ((REAL, ours_root), (PEER, theirs_root)))
    assert ours.status != 0, report
    assert theirs.status != 0, report
    assert "E-CONFIG-MISMATCH" in ours.err or "series stopped" in ours.err, report
    for root in (ours_root, theirs_root):
        names = evidence.official(root)
        assert [name for name in names if name.startswith("result_")] == [], report
        assert [name for name in names if name.startswith("config_")] == [], report
