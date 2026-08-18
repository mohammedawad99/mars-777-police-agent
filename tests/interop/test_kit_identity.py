"""Match identity both peers reach alone, and the agreement digest over the terms.

Two peers that name a match differently produce two sets of artifact filenames
and two reports nobody can join. The kit's fix is to derive both ids from
`sorted([group_a, group_b])`, so neither side has to be told the order and
there is no convention left for a pairing to settle - which is why the swapped
case below matters more than the canonical one.

`terms_signature` is a **content agreement digest**, not authentication: it is
unkeyed, and anyone holding the terms and the nonce can recompute it. Our
`HMAC_SHA256` Step-0 proof is what authenticates a peer, and no successful
comparison here may ever stand in for it.
"""

from kit_vectors import GAME_ID, GAME_UID, GROUPS, TERMS, TERMS_NONCE, TERMS_SIGNATURE

from mars777_police.protocol.kit_identity import kit_game_id, kit_game_uid, kit_terms_digest


def test_the_pinned_game_uid_reproduces_exactly() -> None:
    assert kit_game_uid(TERMS, *GROUPS) == GAME_UID


def test_the_pinned_game_id_reproduces_exactly() -> None:
    assert kit_game_id(*GROUPS) == GAME_ID


def test_swapping_the_pair_changes_neither_id() -> None:
    """The property the pairing depends on: no peer has to be told the order."""
    forward, reverse = GROUPS, (GROUPS[1], GROUPS[0])

    assert kit_game_uid(TERMS, *reverse) == kit_game_uid(TERMS, *forward)
    assert kit_game_id(*reverse) == kit_game_id(*forward)


def test_the_game_id_never_names_us_first() -> None:
    """`<us>-vs-<them>` is the failure the sort exists to prevent."""
    assert kit_game_id("zeta", "alpha") == "alpha-vs-zeta"


def test_different_terms_give_a_different_uid() -> None:
    """The uid names *this* agreement, not merely this pair."""
    other = {**TERMS, "max_steps": TERMS["max_steps"] + 1}

    assert kit_game_uid(other, *GROUPS) != GAME_UID


def test_the_pinned_terms_digest_reproduces_exactly() -> None:
    assert kit_terms_digest(TERMS, TERMS_NONCE) == TERMS_SIGNATURE


def test_the_terms_digest_is_unkeyed_and_therefore_not_authentication() -> None:
    """Anyone with the terms and nonce recomputes it - it proves agreement, not identity."""
    assert kit_terms_digest(TERMS, TERMS_NONCE) == kit_terms_digest(dict(TERMS), TERMS_NONCE)


def test_an_empty_group_id_is_refused_rather_than_sorted() -> None:
    """A blank id would sort first and silently name every match the same way."""
    import pytest

    for pair in (("", "team-bet"), ("team-aleph", "")):
        with pytest.raises(ValueError, match="two non-empty group ids"):
            kit_game_id(*pair)


def test_the_terms_digest_refuses_a_missing_nonce() -> None:
    import pytest

    with pytest.raises(ValueError, match="non-empty nonce"):
        kit_terms_digest(TERMS, "")
