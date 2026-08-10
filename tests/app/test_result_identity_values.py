"""The declaration-sourced halves of the core: participants and the four links.

Separated from `test_result_core_values.py` by the same ownership line the
production modules follow - what the declaration supplies, against what the
played series produces.
"""

import pytest
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.result_identity_values import (
    GithubLinks,
    ResultParticipants,
    require_result_score,
    require_result_text,
)
from mars777_police.app.result_values import InvalidResultValueError


def test_the_two_participants_must_differ() -> None:
    """A result naming one participant twice describes no match that was played."""
    with pytest.raises(InvalidResultValueError):
        ResultParticipants(GROUP_A, GROUP_A)
    assert ResultParticipants(GROUP_A, GROUP_B).group_b == GROUP_B


def test_participant_slots_are_positions_not_an_ordering() -> None:
    assert ResultParticipants(GROUP_A, GROUP_B) != ResultParticipants(GROUP_B, GROUP_A)
    assert min(GROUP_A, GROUP_B) == GROUP_B


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_all_four_links_are_required(index: int) -> None:
    values = ["a", "b", "c", "d"]
    values[index] = ""
    with pytest.raises(InvalidResultValueError):
        GithubLinks(*values)
    assert GithubLinks("a", "b", "c", "d").group_b_thief == "d"


def test_a_link_must_be_an_exact_string() -> None:
    with pytest.raises(InvalidResultValueError):
        GithubLinks("a", "b", "c", 4)


def test_the_shared_validators_reject_bool_and_negative_values() -> None:
    for bad in (True, -1, 1.0):
        with pytest.raises(InvalidResultValueError):
            require_result_score(bad, "cop_score")
    assert require_result_score(0, "cop_score") == 0
    assert require_result_text("a", "x") == "a"
