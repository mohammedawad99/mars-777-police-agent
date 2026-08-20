"""The small refusals and branches the end-to-end path does not reach.

Each of these is a way evidence can be malformed that a real played sub-game
never produces, which is exactly why they are exercised directly.
"""

import pytest

from mars777_police.app.replay_board import board_lines, symbol_at
from mars777_police.app.replay_crypto import barriers_of, check_commit, sealed_state
from mars777_police.app.replay_log import read_log
from mars777_police.app.replay_values import ReplayCheck, ReplayError, ReplayStep

STEP = ReplayStep(
    number=1,
    turns=(),
    police_cell=(0, 0),
    thief_cell=(1, 1),
    barriers=((2, 2),),
    grid_size=3,
    semantic="CONSISTENT",
)


def test_a_barrier_cell_is_drawn_as_a_barrier() -> None:
    assert symbol_at(STEP, 2, 2) == "#"


def test_an_empty_cell_is_drawn_as_empty() -> None:
    assert symbol_at(STEP, 0, 2) == "."


def test_two_agents_on_one_cell_are_drawn_as_one_symbol() -> None:
    together = ReplayStep(1, (), (1, 1), (1, 1), (), 3, "CONSISTENT")

    assert symbol_at(together, 1, 1) == "!"
    assert "!" in "".join(board_lines(together))


def test_a_barrier_set_that_is_not_a_list_is_refused() -> None:
    with pytest.raises(ReplayError, match="barrier set"):
        barriers_of({"barriers": 7})


def test_a_cell_that_is_not_a_pair_is_refused() -> None:
    with pytest.raises(ReplayError, match="two-member position"):
        barriers_of({"barriers": [[1]]})


def test_a_cell_that_is_not_whole_numbers_is_refused() -> None:
    with pytest.raises(ReplayError, match="whole numbers"):
        barriers_of({"barriers": [["a", "b"]]})


def test_a_sealed_state_missing_a_member_is_refused() -> None:
    with pytest.raises(ReplayError, match="could not be rebuilt"):
        sealed_state({"state": {"role": "police"}}, 1)


def test_a_commit_entry_without_a_digest_is_not_applicable() -> None:
    assert check_commit({}, None, {}, None, 1) is ReplayCheck.NOT_APPLICABLE  # type: ignore[arg-type]


def test_a_commit_entry_without_a_step_is_not_checkable() -> None:
    entry = {"commit": "a" * 64}

    assert check_commit(entry, None, {}, None, 1) is ReplayCheck.NOT_CHECKABLE  # type: ignore[arg-type]


def test_a_log_whose_final_reveal_is_not_a_list_is_refused() -> None:
    document = {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {"final_reveal": 5, "semantic": {"verdict": "CONSISTENT"}},
    }

    with pytest.raises(ReplayError, match="final_reveal"):
        read_log(document)


def test_a_tampered_step_that_is_not_a_step_is_refused() -> None:
    document = {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {
            "final_reveal": [],
            "tampered_step": "two",
            "semantic": {"verdict": "CONSISTENT"},
        },
    }

    with pytest.raises(ReplayError, match="tampered_step"):
        read_log(document)


def test_a_nonce_entry_without_a_step_is_ignored_rather_than_fatal() -> None:
    document = {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {"final_reveal": [{"role": "police"}, 7], "semantic": {"verdict": "CONSISTENT"}},
    }

    assert read_log(document).nonces == {}


def test_an_empty_game_id_is_refused() -> None:
    document = {
        "game_id": "",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {"final_reveal": [], "semantic": {"verdict": "CONSISTENT"}},
    }

    with pytest.raises(ReplayError, match="game_id"):
        read_log(document)


def test_a_sealed_state_that_is_not_an_object_is_refused() -> None:
    with pytest.raises(ReplayError, match="no sealed state"):
        sealed_state({"state": 7}, 1)


def test_a_commit_without_an_intent_is_refused() -> None:
    entry = {
        "commit": "a" * 64,
        "step": 1,
        "move": {"kind": "MOVE", "value": "S"},
        "state": {
            "config_sha256": "b" * 64,
            "self_pos": [0, 0],
            "barriers": [],
            "step": 1,
            "role": "police",
        },
    }

    with pytest.raises(ReplayError, match="could not be rebuilt"):
        check_commit(entry, None, {(1, "police"): "c" * 64}, None, 1)  # type: ignore[arg-type]


def test_an_audit_block_without_a_semantic_finding_is_refused() -> None:
    document = {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {"final_reveal": []},
    }

    with pytest.raises(ReplayError, match="semantic"):
        read_log(document)


def test_a_nonce_that_is_not_text_is_ignored() -> None:
    document = {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {"final_reveal": [{"step": 1, "nonce": 7}], "semantic": {"verdict": "CONSISTENT"}},
    }

    assert read_log(document).nonces == {}


def test_a_logged_action_that_is_not_an_action_is_refused() -> None:
    from mars777_police.app.protocol_errors import MalformedMessageError
    from mars777_police.transport.codec_replay import replay_action

    with pytest.raises(MalformedMessageError, match="not an action"):
        replay_action({"kind": "TELEPORT", "value": "Z"})


def test_a_logged_move_decodes_to_its_domain_action() -> None:
    from mars777_police.domain.actions import MoveAction
    from mars777_police.transport.codec_replay import replay_action

    assert isinstance(replay_action({"kind": "MOVE", "value": "S"}), MoveAction)
