"""What an alternating counted series may and may not report, and why not yet.

A real counted series against `s82kma9e` played six sub-games, completed six
mutual audits, settled bidirectionally and wrote exactly fourteen official files
- and the lecturer was never mailed. `SeriesDriver._report` is unreachable in an
alternating series: one process never sees the whole thing.

The gateway now hands the written result to the same reporter an operator would
invoke. It is refused, and these pin **why**: a result becomes eligible only
once both participants' own `ResultContribution`s exist, and the pinned KIT
external `receive_control` is a status signal that returns `{"ok": true}` and
carries no contribution and no digest. An absent peer contribution is never
replaced by a manufactured one, so the agreement stays incomplete and the normal
gate refuses - which is the honest state of a result nobody agreed.
"""

from pathlib import Path

import pytest
from counted_result_builders import (
    COMMIT_A,
    DIGEST,
    GROUP_A,
    STAMP,
    both_contributions,
    contribution,
    document,
    merged,
    parts,
    rows,
    stamp,
    write_set,
    written,
)

from mars777_police.app.protocol_errors import LocalDefectError, ReportDisagreeError
from mars777_police.app.report_values import ReportIneligibleError
from mars777_police.app.result_core_runtime import slot_of
from mars777_police.app.result_values import InvalidResultValueError, ResultContribution
from mars777_police.compose_report import read_report
from mars777_police.counted_result_core import approval_core
from mars777_police.protocol.result_core import ResultDigester, result_core


def core(**changes: object) -> object:
    given = {
        "declaration": merged(),
        "rows": rows(),
        "timestamp": stamp(),
        "contributions": both_contributions(),
        "group_id": GROUP_A,
        **changes,
    }
    return approval_core(**given)  # type: ignore[arg-type]


def test_without_the_peer_contribution_no_result_sha256_exists(tmp_path: Path) -> None:
    """The gateway writes fourteen files and the result carries no agreement."""
    made = document(tmp_path)
    assert made["series_consensus_sha256"] == DIGEST
    for absent in ("result_sha256", "mutual_agreement", "reported_by"):
        assert absent not in made


def test_a_result_with_no_agreement_is_refused_by_the_normal_gate(tmp_path: Path) -> None:
    """No bypass exists: the operator's own reader refuses it, as it must."""
    with pytest.raises(ReportIneligibleError, match="mutual agreement"):
        read_report(written(tmp_path), tmp_path)


def test_an_unagreed_series_writes_nothing_at_all(tmp_path: Path) -> None:
    assert not parts(agreed=None).ready
    write_set(tmp_path, parts(agreed=None))
    assert list(tmp_path.iterdir()) == []


def test_the_core_needs_both_participants_and_invents_neither() -> None:
    """One contribution is not a core; nothing stands in for the missing side."""
    ours, _ = both_contributions()
    with pytest.raises((ReportDisagreeError, LocalDefectError, IndexError, KeyError)):
        core(contributions=(ours, ours))


def test_a_contribution_missing_a_sub_game_is_refused_not_repaired() -> None:
    """Five entries are not six, and they are never sorted, padded or defaulted."""
    short = tuple(contribution(GROUP_A, COMMIT_A).entries[:5])
    with pytest.raises(InvalidResultValueError, match="exactly once each"):
        ResultContribution(GROUP_A, short)


def test_total_tokens_is_the_sum_of_each_participants_own_six_values() -> None:
    """Derived, never transmitted: one fact has exactly one representation.

    Read through `slot_of`: a contribution's `group_id` selects a slot and never
    defines one, so a test that assumed the seating would encode one pairing's
    layout as if it were a rule.
    """
    built = core()
    for given in both_contributions():
        slot = slot_of(merged(), given.group_id)
        assert getattr(built.total_tokens, slot) == sum(e.tokens for e in given.entries)  # type: ignore[attr-defined]


def test_each_sub_game_carries_the_contributed_token_count_verbatim() -> None:
    built = core()
    for given in both_contributions():
        slot = slot_of(merged(), given.group_id)
        for entry, mine in zip(built.sub_games, given.entries, strict=True):  # type: ignore[attr-defined]
            assert getattr(entry.tokens, slot) == mine.tokens


def test_result_sha256_recomputes_from_the_core_and_is_not_the_consensus_digest() -> None:
    """Two facts over two scopes; aliasing them would destroy the distinction."""
    digest = ResultDigester().digest(core()).value  # type: ignore[arg-type]
    assert len(digest) == 64
    assert digest != DIGEST
    assert ResultDigester().digest(core()).value == digest  # type: ignore[arg-type]


def test_the_core_excludes_every_member_that_describes_reporting() -> None:
    """`result_sha256` may never sit inside the bytes it covers."""
    projected = result_core(core())  # type: ignore[arg-type]
    for excluded in ("result_sha256", "mutual_agreement", "reported_by"):
        assert excluded not in projected


def test_the_timestamp_is_carried_verbatim_into_the_core() -> None:
    assert core().timestamp.value == STAMP  # type: ignore[attr-defined]
