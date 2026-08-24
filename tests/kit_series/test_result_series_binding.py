"""Which identity a verified result agreement is answered as.

The proof half is `test_series_result_authority.py`. This is the binding half:
once a request has proved itself, the sender is resolved from the Step-0 that
established the series - and never from `contribution.group_id`, because letting
a request name its own author turns the downstream ownership check into `x != x`.
"""

import pytest
from counted_result_builders import merged
from result_auth_builders import authority, payload, proof_over, sides

from mars777_police.app.declaration_values import Declaration, DeclarationTeams
from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.app.series_result_authority import (
    authenticated_sender,
    opponent_of,
    raw_payload,
)


def test_a_fresh_session_with_a_valid_proof_is_named_by_the_series_binding() -> None:
    declaration = merged()
    ours, theirs = sides(declaration)
    body = payload(theirs)

    found = authenticated_sender(None, body, proof_over(body), declaration, ours, authority())

    assert found == theirs


def test_the_identity_never_comes_from_the_payload() -> None:
    """A request claiming to be us is still named by the binding, then refused later."""
    declaration = merged()
    ours, theirs = sides(declaration)
    body = payload(ours)

    found = authenticated_sender(None, body, proof_over(body), declaration, ours, authority())

    assert found == theirs
    assert found != body["contribution"]["group_id"]  # type: ignore[index]


def test_a_valid_proof_without_an_established_series_is_refused() -> None:
    """A stored Step-0 authenticates the series; absent one, nothing is authenticated."""
    body = payload()
    with pytest.raises(AuthFailureError) as failure:
        authenticated_sender(None, body, proof_over(body), None, "MaRs-777", authority())
    assert "no authenticated Step-0" in str(failure.value)


def test_a_half_exchanged_series_is_not_an_established_one() -> None:
    """Our own subtree is not the peer's proof."""
    whole = merged()
    ours, _ = sides(whole)
    partial = Declaration(
        whole.game_id,
        whole.game_uid,
        whole.token_budget_per_series,
        whole.times,
        DeclarationTeams(whole.teams.group_a, None),
    )
    assert partial.teams.is_merged is False
    body = payload()

    with pytest.raises(AuthFailureError):
        authenticated_sender(None, body, proof_over(body), partial, ours, authority())


def test_an_unconfigured_group_cannot_name_the_opponent() -> None:
    with pytest.raises(AuthFailureError) as failure:
        opponent_of(merged(), "")
    assert "no configured identity" in str(failure.value)


def test_a_series_that_does_not_name_us_authenticates_nobody_to_us() -> None:
    """ "Whichever participant is not us" would answer a stranger's series."""
    with pytest.raises(AuthFailureError) as failure:
        opponent_of(merged(), "somebody-else")
    assert "does not name" in str(failure.value)


def test_the_proof_is_taken_over_the_payload_exactly_as_it_arrived() -> None:
    body = payload()
    assert raw_payload({"kind": "result_agreement", "payload": body}) is body


def test_a_message_with_no_payload_carries_no_provable_subject() -> None:
    for message in ({"kind": "result_agreement"}, "not a mapping", None):
        with pytest.raises(AuthFailureError):
            raw_payload(message)
