"""The real defect, pinned: an alternating counted series must report itself.

A counted series against `s82kma9e` completed six sub-games, six mutual audits
and a genuine bidirectional settlement, wrote fourteen artifacts, and mailed
nobody. These are the blocking tests for the repair, and nothing more: each one
fails on the shipped defect and passes on the fix.

The order the finalisation must follow is the subject. A result becomes
reportable only after **both** participants' own contributions exist and both
independently computed digests match; before that every path must refuse, and
the refusal must not damage the series that was actually played.
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest
from counted_result_builders import DIGEST, STAMP, merged, parts, write_set
from r16_builders import COMMIT_A, GROUP_A, GROUP_B, contribution

from mars777_police import GROUP_CODE
from mars777_police.app.kit_contribution_entries import ContributionCollector, admit
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_result_agreement import GroupResultAgreement
from mars777_police.app.protocol_errors import (
    LocalDefectError,
    ReportDisagreeError,
    StaleMessageError,
)
from mars777_police.app.report_values import ReportIneligibleError
from mars777_police.compose_report import read_report
from mars777_police.compose_series_writer import reporting_fields_for


class Exchange:
    """The agreement authority's verdict, without a live peer or a transport."""

    def __init__(self, agreed: bool, digest: str = "d" * 64) -> None:
        self.is_agreed = agreed
        self.local_digest = _Digest(digest) if agreed else None

    def approval_core(self) -> Any:
        return _Core()


class _Digest:
    def __init__(self, value: str) -> None:
        self.value = value


class _Core:
    participants = type("P", (), {"group_a": GROUP_A, "group_b": GROUP_B})()
    total_tokens = type("T", (), {"group_a": 621, "group_b": 1221})()


def held(exchange: object | None) -> GroupResultAgreement:
    holder = GroupResultAgreement(build=lambda: None)
    holder.exchange = exchange  # type: ignore[assignment]
    return holder


def test_no_agreement_renders_no_reporting_members() -> None:
    """The shipped defect's artifact: fourteen files, and nothing to report."""
    assert reporting_fields_for(held(None))(merged(), (), STAMP) == {}  # type: ignore[misc]


def test_an_incomplete_agreement_renders_no_reporting_members() -> None:
    """Both directions must complete; one is not most of an agreement."""
    assert reporting_fields_for(held(Exchange(agreed=False)))(merged(), (), STAMP) == {}  # type: ignore[misc]


def test_a_completed_agreement_renders_exactly_the_gate_members() -> None:
    fields = reporting_fields_for(held(Exchange(agreed=True)))(merged(), (), STAMP)  # type: ignore[misc]

    assert fields["mutual_agreement"] is True
    assert fields["result_sha256"] == "d" * 64
    assert fields["reported_by"] == GROUP_CODE
    assert fields["total_tokens"] == {GROUP_A: 621, GROUP_B: 1221}


def test_total_tokens_come_from_the_participant_owned_contributions() -> None:
    """Derived from the core the exchange assembled, never from this module."""
    fields = reporting_fields_for(held(Exchange(agreed=True)))(merged(), (), STAMP)  # type: ignore[misc]

    assert sum(fields["total_tokens"].values()) == 621 + 1221  # type: ignore[union-attr]


def test_a_result_written_without_an_agreement_is_refused_by_the_normal_gate(
    tmp_path: Path,
) -> None:
    """No bypass: the operator's own reader refuses it, exactly as it must."""
    write_set(tmp_path, parts())
    with pytest.raises(ReportIneligibleError, match="mutual agreement"):
        read_report(tmp_path / f"result_{merged().game_id}.json", tmp_path)


def test_the_agreement_refuses_to_answer_a_group_that_never_assembles() -> None:
    """A partial series cannot answer a peer: the digest would cover nothing real.

    The refusal now comes after a bounded wait rather than immediately, because a
    valid request may legitimately arrive early - see
    `test_result_agreement_readiness.py`. What is pinned here is that a group
    which never assembles never answers and never becomes agreed.
    """
    holder = GroupResultAgreement(build=lambda: None)
    holder.poll = 0.01
    with pytest.raises(StaleMessageError, match="not ready"):
        asyncio.run(holder.accept(object(), GROUP_B, 0.05))  # type: ignore[arg-type]
    assert holder.is_agreed is False


def test_a_backend_may_not_contribute_a_sub_game_the_schedule_gave_the_other() -> None:
    """`require_ours` is the frozen schedule, applied when the entry arrives."""
    with pytest.raises(LocalDefectError, match="never the other"):
        admit(merged(), GROUP_A, KitRole.POLICE, KitRole.POLICE, 2, COMMIT_A.value)


def test_a_contributed_commit_must_be_the_one_declared_for_the_role_played() -> None:
    with pytest.raises(ReportDisagreeError, match="declared for that role"):
        admit(merged(), GROUP_A, KitRole.POLICE, KitRole.POLICE, 1, "f" * 40)


def test_an_entry_arriving_before_the_declaration_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="merged Step-0 declaration"):
        admit(None, GROUP_A, KitRole.POLICE, KitRole.POLICE, 1, COMMIT_A.value)


def test_the_group_contribution_needs_six_unique_entries_and_repairs_none() -> None:
    collector = ContributionCollector()
    for number in (1, 3, 5):
        collector.record(number, COMMIT_A.value, 0)
    with pytest.raises(StaleMessageError, match=r"\[2, 4, 6\]"):
        collector.contribution(GROUP_CODE)
    with pytest.raises(StaleMessageError, match="contributes once"):
        collector.record(1, COMMIT_A.value, 0)


def test_a_peer_contribution_is_six_entries_or_it_is_not_one() -> None:
    """Never sorted, deduplicated or padded - the authority already refuses."""
    from mars777_police.app.result_values import InvalidResultValueError, ResultContribution

    short = tuple(contribution(GROUP_B, COMMIT_A).entries[:5])
    with pytest.raises(InvalidResultValueError, match="exactly once each"):
        ResultContribution(GROUP_B, short)


def test_the_settlement_digest_and_the_result_digest_stay_distinct() -> None:
    """Two facts over two scopes; aliasing one to the other would lose both."""
    fields = reporting_fields_for(held(Exchange(agreed=True)))(merged(), (), STAMP)  # type: ignore[misc]

    assert fields["result_sha256"] != DIGEST
