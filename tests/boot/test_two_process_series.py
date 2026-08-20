"""The shipped CLI playing a whole series, as two real OS processes.

This is the proof no in-process harness can give: each side's own command line
boots, exchanges Step-0 over real HTTP, plays `g01`...`g06`, writes its fourteen
official artifacts and exits 0. Three defects the in-process proof had hidden
were found exactly here.
"""

import json
from pathlib import Path

import executable_evidence as evidence
import executable_outcome as outcome
import executable_process as process
import pytest
from boot_builders import SECRET, free_port

from mars777_police.app.sealed_record_values import ActorRole

GAMES = 6
FILES = 14
DEADLINE = (30, 60)
"""The negotiated response and watchdog bounds a normal series locks.

Read back from the artifact rather than trusted from the fixture: an agent that
shipped one deadline and locked another would still write a config file, and
this is the file both sides then hold each other to.
"""
REAL = "real CLI"
PEER = "synthetic opponent"
"""The two sides, named once so a diagnostic says which process it is quoting."""


def locked_deadline(root: Path) -> tuple[int, int]:
    """What the official g01 config says the two sides actually locked.

    Read from the artifact rather than from the fixture that proposed it: the
    assertion is only meaningful if the negotiated value survived convergence
    and the mutual lock, and the artifact is the record of that.
    """
    name = next(one for one in evidence.official(root) if one.startswith("config_"))
    document = json.loads((root / name).read_text(encoding="utf-8"))
    terms = document["config"]["network_and_league"]
    return terms["response_timeout_sec"], terms["watchdog_timeout_sec"]


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    ours, theirs = tmp_path / "mars777", tmp_path / "opponent"
    ours.mkdir()
    theirs.mkdir()
    return ours, theirs


@pytest.mark.windows_known_limitation
def test_the_real_cli_plays_a_whole_series_against_a_non_counted_opponent(tmp_path: Path) -> None:
    """One full exact-six autonomous series, both sides real OS processes.

    **Both sides are collected before anything is asserted.** A stall here is a
    statement about a pair, and judging the first process while the second was
    still undescribed reported one stack and discarded the peer holding the
    other end of it - which is exactly what a reproducible Windows stall needed.

    Marked because this pair reproducibly stalls on native Windows and nowhere
    else; see `docs/architecture/CONCURRENCY_MODEL.md`. The mark selects the
    test out of the *gating* Windows suite and into a visible non-gating job -
    it is fully gating on Linux, where it passes, and it is not an `xfail`,
    because a failure here must stay a failure that someone reads.
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
    )
    try:
        assert outcome.await_application(child, ours_port) == process.NOT_ACCEPTABLE
        ours = outcome.finished(REAL, child, timeout=600)
        theirs = outcome.finished(PEER, opponent, timeout=120)
    finally:
        for one in (child, opponent):
            if one.poll() is None:
                one.kill()
                one.communicate(timeout=10)

    assert SECRET not in ours.out and SECRET not in ours.err
    assert SECRET not in theirs.out and SECRET not in theirs.err
    report = evidence.two_process_report((ours, theirs), ((REAL, ours_root), (PEER, theirs_root)))

    assert ours.status == 0, report
    assert theirs.status == 0, report
    assert child.pid != opponent.pid
    assert not outcome.crashed(ours.err), report
    assert f"{FILES} artifacts" in ours.out, report

    for root in (ours_root, theirs_root):
        names = evidence.official(root)
        assert locked_deadline(root) == DEADLINE, report
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
    result = json.loads((ours_root / evidence.official(ours_root)[-1]).read_text(encoding="utf-8"))
    assert result["mutual_agreement"]
