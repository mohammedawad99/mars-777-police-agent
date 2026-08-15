"""Opening a round that is already open must not throw the peer's work away.

Two independent processes have no way to agree who opens `g01` first. Whichever
finishes Step-0 first opens its round and proposes immediately, so the other
side can receive an authenticated proposal *before* its own `SeriesDriver.open()`
runs. That open used to call `open_round` unconditionally, and `open_round`
resets `opening`, `seen`, the config, the verified evidence and the milestones -
so the proposal, and the signal that it arrived, vanished. The peer sends
exactly one proposal per round, so the local side then waited forever.

Stage 6C-C1 never saw it: its in-process harness called `driver.open()` on both
sides before either could send anything, which is an ordering two OS processes
cannot provide.

The fix belongs to the caller that opened twice, not to `open_round`: opening
the round a side is *already* on is a no-op, and advancing to the next sub-game
still opens a genuinely fresh one. These tests pin both halves, plus the local
ownership invariant that keeps `open` from silently swapping our own candidate.
"""

import dataclasses

import autonomous_series_builders as auto
import pytest
import r7_builders as r7
from r16_builders import GROUP_B

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.state_machine import ProtocolPhase
from mars777_police.domain.config_sections import WorldTerms

OTHER = dataclasses.replace(
    r7.CONFIG, world=WorldTerms(map_area=r7.CONFIG.world.map_area, hint_max_words=12)
)
"""A different but entirely legal local candidate, for the ownership guard."""

TO_NEXT_SUB_GAME = (
    ProtocolPhase.STEP0_NEGOTIATION,
    ProtocolPhase.CONFIG_NEGOTIATION,
    ProtocolPhase.CONFIG_LOCKED,
    ProtocolPhase.READY,
    ProtocolPhase.SUBGAME_COMPLETE,
    ProtocolPhase.READY,
)
"""The phases a finished sub-game walks, so the cursor reaches the next one."""


def _sides(tmp_path: object) -> tuple[object, object, object]:
    """A real police series with its driver, and the peer's real pregame."""
    a, b = auto.pair_for(tmp_path)  # type: ignore[arg-type]
    driver = auto.driver_for(a, ActorRole.POLICE)
    return a, b, driver


def _peer_proposal_arrives(a: object, b: object) -> None:
    """The peer proposes for the current round and we authenticate it."""
    proposal = b.composition.pregame.prepare_proposal(r7.CONFIG)  # type: ignore[attr-defined]
    a.composition.pregame.accept_proposal(proposal, GROUP_B)  # type: ignore[attr-defined]


def test_an_early_peer_proposal_survives_our_own_open(tmp_path: object) -> None:
    """The race, reproduced through the production `SeriesDriver.open()`."""
    a, b, driver = _sides(tmp_path)
    pregame = a.composition.pregame  # type: ignore[attr-defined]
    assert pregame.negotiation.sub_game == a.sub_game == 1  # type: ignore[attr-defined]

    _peer_proposal_arrives(a, b)
    assert GROUP_B in pregame.seen
    assert pregame.milestones.proposal_seen.is_set()
    opening_after_accept = pregame.opening

    driver.open()  # type: ignore[attr-defined]

    assert GROUP_B in pregame.seen
    assert pregame.milestones.proposal_seen.is_set()
    assert pregame.opening is opening_after_accept
    assert pregame.config == r7.CONFIG


def test_opening_the_same_round_twice_changes_nothing(tmp_path: object) -> None:
    """Idempotent: no reset, no protocol send, no cursor move, no artifact."""
    a, b, driver = _sides(tmp_path)
    pregame = a.composition.pregame  # type: ignore[attr-defined]

    driver.open()  # type: ignore[attr-defined]
    _peer_proposal_arrives(a, b)
    milestones, negotiation = pregame.milestones, pregame.negotiation
    driver.open()  # type: ignore[attr-defined]

    assert pregame.milestones is milestones
    assert pregame.negotiation is negotiation
    assert GROUP_B in pregame.seen
    assert pregame.locked_evidence is None
    assert a.orchestrator.machine.phase is ProtocolPhase.BOOT  # type: ignore[attr-defined]
    assert a.lines == ()  # type: ignore[attr-defined]
    written = tmp_path / "police"  # type: ignore[operator]
    assert not written.exists() or list(written.iterdir()) == []


def test_a_different_local_candidate_for_the_same_round_is_refused(tmp_path: object) -> None:
    """Our own candidate is ours: `open` never silently swaps it."""
    _, _, driver = _sides(tmp_path)
    driver.open()  # type: ignore[attr-defined]
    other = dataclasses.replace(driver, config=OTHER)  # type: ignore[type-var]

    with pytest.raises(LocalDefectError, match="already opened"):
        other.open()


def test_the_next_sub_game_still_opens_a_genuinely_fresh_round(tmp_path: object) -> None:
    """Idempotence must not become "never open again"."""
    a, b, driver = _sides(tmp_path)
    pregame = a.composition.pregame  # type: ignore[attr-defined]
    driver.open()  # type: ignore[attr-defined]
    _peer_proposal_arrives(a, b)
    frozen = pregame.scent_freeze

    for target in TO_NEXT_SUB_GAME:
        a.orchestrator = a.orchestrator.advance(target).orchestrator  # type: ignore[attr-defined]
    assert a.sub_game == 2  # type: ignore[attr-defined]
    driver.open()  # type: ignore[attr-defined]

    assert pregame.negotiation.sub_game == 2
    assert pregame.lock.sub_game == 2
    assert pregame.seen == frozenset()
    assert not pregame.milestones.proposal_seen.is_set()
    assert pregame.locked_evidence is None
    assert pregame.opening is True
    assert pregame.config == r7.CONFIG
    assert pregame.scent_freeze is frozen
    assert pregame.peer == GROUP_B or pregame.peer is None


def test_a_split_round_identity_is_a_local_defect(tmp_path: object) -> None:
    """Never guess which half of a half-opened round is authoritative."""
    a, _, driver = _sides(tmp_path)
    pregame = a.composition.pregame  # type: ignore[attr-defined]
    pregame.lock = dataclasses.replace(pregame.lock, sub_game=2)

    with pytest.raises(LocalDefectError, match="one sub-game"):
        driver.open()  # type: ignore[attr-defined]
