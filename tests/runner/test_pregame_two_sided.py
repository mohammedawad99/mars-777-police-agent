"""Both directions of one config round, with the round state owned in one place.

Before Stage 5-R4 only an inbound proposal moved `opening` and `seen`, so a side
that opened the exchange still believed the round was unopened. These tests hold
both sides' pregame runtimes and check each one's view of its own round.
"""

import pytest
import runner_builders as build
from r16_builders import GROUP_A, GROUP_B, config

from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.scent_model_default import default_scent_model


def sides() -> tuple[object, object]:
    """The opener and the responder, by the frozen initial-proposer rule."""
    opener = build.side(GROUP_B, ActorRole.THIEF)
    other = build.side(GROUP_A, ActorRole.POLICE)
    return opener, other


def test_our_own_opening_proposal_closes_the_opening_window() -> None:
    opener, _ = sides()
    assert opener.pregame.opening
    opener.pregame.prepare_proposal(config())
    assert not opener.pregame.opening
    assert opener.pregame.seen == frozenset({GROUP_B})


def test_the_receiving_side_records_the_peer_not_itself() -> None:
    opener, other = sides()
    proposal = opener.pregame.prepare_proposal(config())
    other.pregame.accept_proposal(proposal, GROUP_B)
    assert other.pregame.seen == frozenset({GROUP_B})
    assert not other.pregame.opening


def test_the_counterproposal_path_remains_legal() -> None:
    """After the opener has spoken, the other side may still propose once."""
    opener, other = sides()
    other.pregame.accept_proposal(opener.pregame.prepare_proposal(config()), GROUP_B)
    counter = other.pregame.prepare_proposal(config())
    assert counter.sub_game == build.SUB_GAME
    assert other.pregame.seen == frozenset({GROUP_B, GROUP_A})


def test_neither_side_may_propose_twice_in_one_round() -> None:
    opener, other = sides()
    opener.pregame.prepare_proposal(config())
    with pytest.raises(StaleMessageError, match="already proposed"):
        opener.pregame.prepare_proposal(config())
    other.pregame.accept_proposal(
        opener.pregame.negotiation.propose(config(), opening=True), GROUP_B
    )
    other.pregame.prepare_proposal(config())
    with pytest.raises(StaleMessageError, match="already proposed"):
        other.pregame.prepare_proposal(config())


def test_the_wrong_side_still_cannot_open_the_exchange() -> None:
    """The frozen initial-proposer rule is untouched by the local seam."""
    _, other = sides()
    with pytest.raises(LocalDefectError, match="byte-wise lower"):
        other.pregame.prepare_proposal(config())


def test_local_lock_evidence_needs_the_config_this_side_adopted() -> None:
    opener, _ = sides()
    with pytest.raises(StaleMessageError, match="a config this side agreed"):
        opener.pregame.prepare_lock()
    opener.pregame.adopt_config(config())
    assert opener.pregame.prepare_lock().context.sub_game == build.SUB_GAME


def test_opening_the_next_round_resets_what_our_own_proposal_advanced() -> None:
    """The R4G-frozen reset covers locally-sent proposals too."""
    opener, _ = sides()
    opener.pregame.prepare_proposal(config())
    opener.pregame.adopt_config(config())
    budget = config().network_and_league.token_budget_per_series
    from peer_ops import authenticator

    from mars777_police.app.interop_profiles import InteropProfileSet
    from mars777_police.protocol.config_lock import ConfigLockAuthenticator

    shared = ConfigLockAuthenticator(authenticator())
    profiles: InteropProfileSet = opener.pregame.negotiation.profiles
    opener.pregame.open_round(
        ConfigNegotiationRuntime(GROUP_B, 2, budget, profiles, shared, default_scent_model()),
        ConfigLockRuntime("g", "u", 2, profiles, shared, shared, default_scent_model()),
    )
    assert opener.pregame.opening and opener.pregame.seen == frozenset()
    assert opener.pregame.config is None


def alternate_model() -> object:
    """A valid, still-radial model that is not the one either side agreed."""
    import dataclasses

    from mars777_police.domain.scent_kernel import ScentKernel
    from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS

    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = "0.03"
    return dataclasses.replace(default_scent_model(), kernel=ScentKernel.from_rows(rows))


def test_a_real_round_agrees_on_the_scent_model_both_sides_carry() -> None:
    """The opener's real proposal carries its model and the peer accepts it."""
    opener, other = sides()
    proposal = opener.pregame.prepare_proposal(config())
    assert proposal.scent_model == default_scent_model()
    assert other.pregame.accept_proposal(proposal, GROUP_B)


def test_a_real_round_refuses_a_valid_but_different_scent_model() -> None:
    from r16_builders import PROFILES

    from mars777_police.app.peer_pregame_messages import ConfigProposal
    from mars777_police.app.protocol_errors import ConfigMismatchError

    _, other = sides()
    proposal = ConfigProposal(build.SUB_GAME, config(), PROFILES, alternate_model())
    with pytest.raises(ConfigMismatchError, match="not the one this side agreed"):
        other.pregame.accept_proposal(proposal, GROUP_B)
    assert other.pregame.config is None


def test_a_real_round_refuses_a_proposal_with_no_scent_model() -> None:
    from r16_builders import PROFILES

    from mars777_police.app.peer_pregame_messages import ConfigProposal
    from mars777_police.app.protocol_errors import ConfigMismatchError

    _, other = sides()
    proposal = ConfigProposal(build.SUB_GAME, config(), PROFILES)
    with pytest.raises(ConfigMismatchError, match="required pre-game term"):
        other.pregame.accept_proposal(proposal, GROUP_B)
    assert other.pregame.config is None
