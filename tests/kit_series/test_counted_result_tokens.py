"""Where a token count in a counted result may come from, and where it may not.

`result_core_runtime` is explicit that contributed counts are what a participant
**reported**, and that nothing downstream treats them as verified provider usage.
Stage 9C briefly mapped an absent peer contribution to a reported `0`; that was
wrong and is gone. A count exists only because its owner contributed it.

Our own count comes from the local accounting authority — `TokenAccountingPort`,
production implementation `SeriesTokenLedger`. If it answers zero, zero is
legitimate **because the authority answered**, not because a field was absent.
"""

import pytest
from counted_result_builders import (
    COMMIT_A,
    COMMIT_B,
    GROUP_A,
    GROUP_B,
    both_contributions,
    merged,
    rows,
    stamp,
)
from r16_builders import merged_with_distinct_role_commits

import mars777_police.counted_result_core as core_module
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError, ReportDisagreeError
from mars777_police.app.result_core_runtime import slot_of
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.app.run_class import RunClass, RunClassification
from mars777_police.app.token_accounting import SeriesTokenLedger
from mars777_police.counted_result_core import approval_core, outcome_of
from mars777_police.domain.terminal import Outcome


def test_no_zero_substitution_constant_exists_anywhere() -> None:
    """The rejected mapping is gone, by name and by behaviour."""
    assert not hasattr(core_module, "REPORTED_WHEN_UNREPORTED")
    source = core_module.__doc__ or ""
    assert "reported zero" not in source.lower()


def test_our_own_count_comes_from_the_accounting_authority() -> None:
    """Zero is what the ledger answered, not a placeholder for a missing field."""
    ledger = SeriesTokenLedger()
    assert ledger.usage(1) == 0
    ledger.charge(1, 7)
    assert ledger.usage(1) == 7
    assert ledger.total() == 7


def test_a_peer_count_is_accepted_only_from_its_own_contribution() -> None:
    """Whatever the peer contributed is carried verbatim, high or zero."""
    ours, _ = both_contributions()
    quiet = ResultContribution(
        GROUP_B, tuple(ResultContributionEntry(n, COMMIT_B, 0) for n in range(1, 7))
    )
    built = approval_core(merged(), rows(), stamp(), (ours, quiet), GROUP_A)
    slot = slot_of(merged(), GROUP_B)
    assert getattr(built.total_tokens, slot) == 0
    assert all(getattr(entry.tokens, slot) == 0 for entry in built.sub_games)


def test_a_contribution_may_not_be_authored_for_another_participant() -> None:
    """A slot is selected by the contributor's own id, never assigned to it."""
    ours, _ = both_contributions()
    impostor = ResultContribution(
        "not-a-participant", tuple(ResultContributionEntry(n, COMMIT_B, 1) for n in range(1, 7))
    )
    with pytest.raises(ReportDisagreeError):
        approval_core(merged(), rows(), stamp(), (ours, impostor), GROUP_A)


def test_each_sub_game_must_carry_the_commit_declared_for_the_role_played() -> None:
    """Commits follow the role played, which alternates; participants do not."""
    declaration = merged_with_distinct_role_commits()
    wrong = ResultContribution(
        GROUP_A, tuple(ResultContributionEntry(n, COMMIT_A, 1) for n in range(1, 7))
    )
    _, theirs = both_contributions()
    with pytest.raises(ReportDisagreeError, match="did not declare"):
        approval_core(declaration, rows(), stamp(), (wrong, theirs), GROUP_A)


def test_an_unknown_outcome_word_is_refused_rather_than_guessed() -> None:
    for token in ("survival", "capture", "technical_loss"):
        assert outcome_of(token) in Outcome
    with pytest.raises(LocalDefectError):
        outcome_of("tie")


def test_a_counted_run_class_can_never_start_a_kit_role_backend() -> None:
    """`kit_backend_main` is development play and refuses to be anything else.

    Counted-ness lives in the gateway, the only process holding the whole series.
    A backend handed a counted classification is refused at construction.
    """
    import dataclasses

    from kit_backend_builders import backend

    from mars777_police.app.kit_friendly import KitFriendlySession

    friendly = backend(KitRole.POLICE)
    assert friendly.friendly.classification.run_class is RunClass.KIT_FRIENDLY_ONLY

    counted_session = KitFriendlySession(RunClassification.counted(keyed_auth_satisfied=True))
    with pytest.raises(LocalDefectError, match="development friendlies"):
        dataclasses.replace(friendly, friendly=counted_session)
