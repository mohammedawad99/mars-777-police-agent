"""MODEL A: the series outlives the round, and the round leaves nothing behind.

Stage 5-R3R's pre-commit gate found that `opening`, `seen` and the adopted config
survived into the next sub-game, which would have refused the opponent's
legitimate `g02` opening proposal as a duplicate. `open_round` is the fix, and
these tests are the proof that nothing round-scoped crosses the boundary.
"""

import pytest
import session_builders as build
from peer_ops import step0_exchange
from r16_builders import GROUP_B

from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError

ROUNDS = (1, 2, 3, 4, 5, 6)
"""The six sub-games the series plays. A test-only sequence: production never
iterates rounds, it is told which one to open."""


def authenticated() -> object:
    """A series that has completed Step-0 and worked through its first round."""
    runtime = build.pregame()
    runtime.accept_step0(step0_exchange())
    runtime.adopt_config(build.agreed())
    runtime.accept_proposal(build.proposal_for(1), GROUP_B)
    return runtime


def test_the_first_round_leaves_exactly_the_state_that_must_not_carry() -> None:
    runtime = authenticated()
    assert runtime.opening is False
    assert GROUP_B in runtime.seen
    assert runtime.config is not None


def test_opening_a_round_replaces_both_round_runtimes() -> None:
    runtime = authenticated()
    negotiation, lock = build.round_of(2)
    runtime.open_round(negotiation, lock)
    assert runtime.negotiation is negotiation and runtime.lock is lock
    assert runtime.negotiation.sub_game == 2 and runtime.lock.sub_game == 2


def test_opening_a_round_resets_opening_seen_and_config() -> None:
    runtime = authenticated()
    runtime.open_round(*build.round_of(2))
    assert runtime.opening is True
    assert runtime.seen == frozenset()
    assert runtime.config is None


def test_the_declaration_and_peer_survive_every_round() -> None:
    """Step-0 is a series fact; a new config round must never re-open it."""
    runtime = authenticated()
    declaration, peer = runtime.declaration, runtime.peer
    for sub_game in ROUNDS[1:]:
        runtime.open_round(*build.round_of(sub_game))
        assert runtime.declaration is declaration
        assert runtime.peer == peer == GROUP_B


def test_the_first_round_sender_is_not_still_seen_in_the_second() -> None:
    """The defect the gate caught: `g01` seen refusing a legitimate `g02` open."""
    runtime = authenticated()
    with pytest.raises(StaleMessageError, match="already proposed"):
        runtime.accept_proposal(build.proposal_for(1), GROUP_B)
    runtime.open_round(*build.round_of(2))
    assert runtime.accept_proposal(build.proposal_for(2), GROUP_B) is True


def test_the_previous_config_cannot_satisfy_the_new_round() -> None:
    runtime = authenticated()
    runtime.open_round(*build.round_of(2))
    with pytest.raises(StaleMessageError, match="before this side agreed"):
        runtime.accept_lock(build.lock_evidence_for(2))


def test_a_stale_previous_round_proposal_is_refused_after_opening() -> None:
    runtime = authenticated()
    runtime.open_round(*build.round_of(2))
    with pytest.raises(StaleMessageError, match="sub-game"):
        runtime.accept_proposal(build.proposal_for(1), GROUP_B)


def test_a_stale_previous_round_lock_is_refused_after_opening() -> None:
    runtime = authenticated()
    runtime.open_round(*build.round_of(2))
    runtime.adopt_config(build.agreed())
    with pytest.raises(StaleMessageError, match="sub-game"):
        runtime.accept_lock(build.lock_evidence_for(1))


def test_the_new_rounds_lock_verifies_against_the_new_rounds_config() -> None:
    """The digest comes from the config adopted for *this* round, via the port."""
    runtime = authenticated()
    runtime.open_round(*build.round_of(2))
    runtime.adopt_config(build.agreed())
    runtime.accept_lock(build.lock_evidence_for(2))


def test_a_round_whose_runtimes_disagree_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="one sub-game"):
        build.pregame().open_round(build.negotiation_for(2), build.lock_for(3))


def test_a_refused_round_open_changes_nothing_at_all() -> None:
    """Atomic: validation runs before the first assignment."""
    runtime = authenticated()
    before = (runtime.negotiation, runtime.lock, runtime.opening, runtime.seen, runtime.config)
    with pytest.raises(LocalDefectError):
        runtime.open_round(build.negotiation_for(2), build.lock_for(3))
    after = (runtime.negotiation, runtime.lock, runtime.opening, runtime.seen, runtime.config)
    assert before == after


@pytest.mark.parametrize("sub_game", ROUNDS)
def test_all_six_rounds_open_consecutively_and_reset_every_time(sub_game: int) -> None:
    """Driven to `sub_game` one explicit round at a time; state resets each hop."""
    runtime = build.pregame()
    runtime.accept_step0(step0_exchange())
    for target in ROUNDS[1:sub_game]:
        runtime.accept_proposal(build.proposal_for(target - 1), GROUP_B)
        runtime.adopt_config(build.agreed())
        runtime.open_round(*build.round_of(target))
        assert runtime.opening is True and runtime.seen == frozenset()
        assert runtime.config is None
    assert runtime.negotiation.sub_game == sub_game == runtime.lock.sub_game
    assert runtime.peer == GROUP_B
