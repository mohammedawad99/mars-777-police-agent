"""The shipped CLI, as a real OS process, booting itself against a real peer.

**What this proves.** `python -m mars777_police --launch …` serves, reaches an
opponent that may not be up yet, exchanges Step-0, runs one production
`SeriesDriver` to the end of a six-sub-game series, writes its own fourteen
official files and exits 0 - with no fixture supplying an action, an outcome or
a lifecycle call, and no shared object between the two processes.

**What this deliberately does not prove.** The counterparty is a *synthetic,
non-counted integration opponent* (`opponent_entrypoint`), not another team.
The shipped CLI is `MaRs-777` and Step-0 refuses a peer authoring our own
subtree, so a lawful counterparty must carry a different group id - supplied by
test construction, never by the shipped entrypoint. **This is not a league
match and its result is not tournament evidence.** A counted proof needs an
externally supplied different-group agent.

The parent here only writes boot inputs, starts processes, observes readiness,
waits, and reads artifacts afterwards. It sends no protocol message.
"""

import json
from pathlib import Path

import executable_process as process
from boot_builders import SECRET, free_port

from mars777_police.app.sealed_record_values import ActorRole

GAMES = 6
FILES = 14

REAL = "real CLI"
PEER = "synthetic opponent"
"""The two sides, named once so a diagnostic says which process it is quoting."""


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    ours, theirs = tmp_path / "mars777", tmp_path / "opponent"
    ours.mkdir()
    theirs.mkdir()
    return ours, theirs


def test_the_real_cli_plays_a_whole_series_against_a_non_counted_opponent(tmp_path: Path) -> None:
    """One full exact-six autonomous series, both sides real OS processes.

    **Both sides are collected before anything is asserted.** A stall here is a
    statement about a pair, and judging the first process while the second was
    still undescribed reported one stack and discarded the peer holding the
    other end of it - which is exactly what a reproducible Windows stall needed.
    """
    ours_port, theirs_port = free_port(), free_port()
    ours_root, theirs_root = _roots(tmp_path)
    launch = process.written_launch(tmp_path)
    environment = process.environment(
        ours_port, root=ours_root, opponent=f"http://{process.HOST}:{theirs_port}/mcp"
    )
    child = process.spawn("mars777_police", launch, environment)
    opponent = process.spawn_opponent(
        ActorRole.THIEF.value, theirs_port, f"http://{process.HOST}:{ours_port}/mcp", theirs_root
    )
    try:
        assert process.await_application(child, ours_port) == process.NOT_ACCEPTABLE
        ours = process.finished(REAL, child, timeout=600)
        theirs = process.finished(PEER, opponent, timeout=120)
    finally:
        for one in (child, opponent):
            if one.poll() is None:
                one.kill()
                one.communicate(timeout=10)

    assert SECRET not in ours.out and SECRET not in ours.err
    assert SECRET not in theirs.out and SECRET not in theirs.err
    report = process.two_process_report((ours, theirs), ((REAL, ours_root), (PEER, theirs_root)))

    assert ours.status == 0, report
    assert theirs.status == 0, report
    assert child.pid != opponent.pid
    assert not process.crashed(ours.err), report
    assert f"{FILES} artifacts" in ours.out, report

    for root in (ours_root, theirs_root):
        names = process.official(root)
        assert len(names) == FILES == len(set(names)), report
        assert sum(name.startswith("declaration_") for name in names) == 1, report
        assert sum(name.startswith("result_") for name in names) == 1, report
        for family in ("config_", "log_"):
            got = sorted(name for name in names if name.startswith(family))
            assert len(got) == GAMES, report
            assert all(f"_g0{index}." in name for index, name in enumerate(got, start=1)), report

    for log in sorted(path for path in ours_root.iterdir() if path.name.startswith("log_")):
        document = json.loads(log.read_text(encoding="utf-8"))
        assert document["audit"]["semantic"]["verdict"] == "CONSISTENT"
    result = json.loads((ours_root / process.official(ours_root)[-1]).read_text(encoding="utf-8"))
    assert result["mutual_agreement"]


def test_a_peer_that_never_appears_fails_inside_its_budget(tmp_path: Path) -> None:
    """Bounded, non-zero, clean - and nothing official is written."""
    ours_root, _ = _roots(tmp_path)
    port = free_port()
    launch = process.written_launch(tmp_path)
    environment = process.environment(
        port, root=ours_root, opponent=f"http://{process.HOST}:{free_port()}/mcp"
    )
    child = process.spawn("mars777_police", launch, environment)
    assert process.await_application(child, port) == process.NOT_ACCEPTABLE
    ours = process.finished(REAL, child, timeout=300)

    assert SECRET not in ours.out and SECRET not in ours.err
    report = process.two_process_report((ours,), ((REAL, ours_root),))
    assert ours.status == 4, report
    assert "never became reachable" in ours.err, report
    assert not process.crashed(ours.err), report
    assert process.official(ours_root) == [], report


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
        assert process.await_application(child, ours_port) == process.NOT_ACCEPTABLE
        assert child.poll() is None
        opponent = process.spawn_opponent(
            ActorRole.THIEF.value,
            theirs_port,
            f"http://{process.HOST}:{ours_port}/mcp",
            theirs_root,
        )
        assert process.await_application(opponent, theirs_port) == process.NOT_ACCEPTABLE
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
        ours = process.finished(REAL, child, timeout=300)
        theirs = process.finished(PEER, opponent, timeout=120)
    finally:
        for one in (child, opponent):
            if one.poll() is None:
                one.kill()
                one.communicate(timeout=10)

    assert SECRET not in ours.out and SECRET not in ours.err
    assert SECRET not in theirs.out and SECRET not in theirs.err
    report = process.two_process_report((ours, theirs), ((REAL, ours_root), (PEER, theirs_root)))
    assert ours.status != 0, report
    assert theirs.status != 0, report
    assert "E-CONFIG-MISMATCH" in ours.err or "series stopped" in ours.err, report
    for root in (ours_root, theirs_root):
        names = process.official(root)
        assert [name for name in names if name.startswith("result_")] == [], report
        assert [name for name in names if name.startswith("config_")] == [], report
