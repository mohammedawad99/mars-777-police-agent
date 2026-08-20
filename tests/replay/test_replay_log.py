"""Reading a persisted official log back, and what it refuses to read.

The viewer is an attack surface: it reads files a grader may have been handed by
anybody. So parsing is strict and every refusal is a viewer-level error naming
what failed - never a traceback offered as the user interface.
"""

import pytest

from mars777_police.app.replay_log import read_log
from mars777_police.app.replay_values import ReplayError


def minimal() -> dict[str, object]:
    return {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [],
        "audit": {
            "final_reveal": [],
            "result": "Verified OK",
            "tampered_step": None,
            "semantic": {
                "verdict": "CONSISTENT",
                "step": None,
                "at_fault": None,
                "also_at_fault": None,
            },
        },
    }


def test_a_minimal_log_reads_its_identity() -> None:
    log = read_log(minimal())

    assert log.game_id == "A-vs-B"
    assert log.sub_game == 1
    assert log.config_sha256 == "a" * 64
    assert log.result == "Verified OK"


def test_a_document_that_is_not_a_mapping_is_refused() -> None:
    with pytest.raises(ReplayError, match="not a log"):
        read_log([])  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["game_id", "game_uid", "sub_game", "config_sha256", "entries"])
def test_a_missing_top_level_field_is_refused(field: str) -> None:
    document = minimal()
    del document[field]

    with pytest.raises(ReplayError, match=field):
        read_log(document)


def test_a_missing_audit_block_is_refused() -> None:
    document = minimal()
    del document["audit"]

    with pytest.raises(ReplayError, match="audit"):
        read_log(document)


def test_a_sub_game_that_is_not_a_number_is_refused() -> None:
    with pytest.raises(ReplayError, match="sub_game"):
        read_log({**minimal(), "sub_game": "one"})


def test_entries_that_are_not_a_list_are_refused() -> None:
    with pytest.raises(ReplayError, match="entries"):
        read_log({**minimal(), "entries": {}})


def test_an_entry_without_a_phase_is_refused() -> None:
    with pytest.raises(ReplayError, match="phase"):
        read_log({**minimal(), "entries": [{"step": 1}]})


def test_an_unknown_phase_is_refused_rather_than_ignored() -> None:
    with pytest.raises(ReplayError, match="wander"):
        read_log({**minimal(), "entries": [{"phase": "wander", "step": 1}]})


def test_a_commit_without_its_sealed_state_is_refused() -> None:
    entry = {
        "phase": "commit",
        "step": 1,
        "role": "police",
        "commit": "b" * 64,
        "move": {"kind": "MOVE", "value": "S"},
        "hint": "x",
        "intent": "truth",
    }

    with pytest.raises(ReplayError, match="state"):
        read_log({**minimal(), "entries": [entry]})
