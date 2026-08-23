"""One group, one opponent, one series - across two role backends.

A role switch is **not** a new series. `MaRs-777` is one group identity with two
role backends behind one endpoint, and the identity every artifact is written
under must not move when the backend does: same `game_id`, same `game_uid`, same
opponent, one convention, six sub-games.

The two ids are pure functions of shared inputs, which is exactly why they
survive the switch: neither backend has to be told them, and neither can drift.
"""

import pytest
from kit_backend_builders import backend
from r16_builders import config  # noqa: F401 - repo-normalized fixture import

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_schedule import SUB_GAMES, require_ours, schedule_for
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.protocol.kit_identity import kit_game_id, kit_game_uid

TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}
OURS = "MaRs-777"
PEER = "sparring-local"


def context(role: KitRole, sub_game: int) -> KitSessionContext:
    held = KitSessionContext(OURS, role, PeerPayload(TERMS), sub_game)
    held.peer_group = PEER
    return held


def test_the_two_ids_are_the_same_for_every_sub_game_and_every_backend() -> None:
    ids = {
        (
            kit_game_id(OURS, PEER),
            kit_game_uid(TERMS, OURS, PEER),
        )
        for number, role in enumerate(schedule_for(KitRole.POLICE), start=1)
        for _ in (context(role, number),)
    }

    assert len(ids) == 1
    assert ids.pop() == ("MaRs-777-vs-sparring-local", kit_game_uid(TERMS, OURS, PEER))


def test_the_ids_do_not_depend_on_which_side_derives_them() -> None:
    assert kit_game_id(OURS, PEER) == kit_game_id(PEER, OURS)
    assert kit_game_uid(TERMS, OURS, PEER) == kit_game_uid(TERMS, PEER, OURS)


def test_every_greeting_of_the_series_names_the_one_group() -> None:
    groups = {
        context(role, number).our_greeting("a" * 32, number).group_id
        for number, role in enumerate(schedule_for(KitRole.POLICE), start=1)
    }

    assert groups == {OURS}


def test_only_the_role_and_the_sub_game_vary_across_the_schedule() -> None:
    greetings = [
        context(role, number).our_greeting("a" * 32, number)
        for number, role in enumerate(schedule_for(KitRole.POLICE), start=1)
    ]

    assert [one.sub_game_number for one in greetings] == [1, 2, 3, 4, 5, 6]
    assert [one.role for one in greetings] == list(schedule_for(KitRole.POLICE))
    assert len({one.terms.value["board_size"] for one in greetings}) == 1
    assert len({one.game_uid for one in greetings}) == 1


def test_a_series_is_six_sub_games_and_the_schedule_says_so_once() -> None:
    assert SUB_GAMES == 6
    assert len(schedule_for(KitRole.THIEF)) == 6


def test_a_backend_refuses_a_sub_game_the_schedule_did_not_give_it() -> None:
    """This repository's role never plays the other side, and the refusal is structural."""

    from mars777_police.__main__ import ROLE

    held = backend(KitRole.POLICE)
    mine = (1, 3, 5) if ROLE.value == "police" else (2, 4, 6)
    theirs = (2, 4, 6) if ROLE.value == "police" else (1, 3, 5)

    assert held.ours == mine
    require_ours(mine[1], held.ours, held.kit_role)
    with pytest.raises(LocalDefectError):
        require_ours(theirs[0], held.ours, held.kit_role)
