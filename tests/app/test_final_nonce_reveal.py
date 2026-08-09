"""The batched final nonce reveal and its association entry.

Ch 5 §5.4 (p.55) has each agent submit his full log *including the nonce reveals
of all his steps*, and Figure 6 (p.52) draws *Final Reveal: all Nonces* both
ways - **one batched message per side over its own steps**, never one per turn,
scoped per sub-game by Stage 4E-R6. Association is `TurnCursor` alone: no `role`
(a side reveals only its own nonces and the receiver knows the direction - the R3
`by_role` result) and no repeated `h_commit`, action or hint. Context-dependent
rules stay LIVE, so this file asserts that completeness, uniqueness, ordering and
same-sub-game agreement are *accepted* structurally.
"""

import dataclasses

import pytest

from mars777_police.app.peer_final_messages import FinalNonceReveal, NonceRevealEntry
from mars777_police.app.peer_messages import TurnCursor
from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.domain.config_model import FIRST_SUB_GAME

NONCE = NonceValue("0123456789abcdef0123456789abcdef")
OTHER = NonceValue("f" * 32)
CURSOR = TurnCursor(FIRST_SUB_GAME, 1)
ENTRY = NonceRevealEntry(CURSOR, NONCE)


def test_the_entry_carries_exactly_the_cursor_and_the_nonce() -> None:
    assert tuple(f.name for f in dataclasses.fields(NonceRevealEntry)) == ("cursor", "nonce")


ABSENT = ["role", "by_role", "sender", "h_commit", "action", "move", "hint", "state", "intent"]
ABSENT += ["phase", "game_id", "game_uid", "verdict", "accepted", "reason", "timestamp"]


@pytest.mark.parametrize("absent", ABSENT)
def test_the_entry_carries_no_further_field(absent: str) -> None:
    """Role is local attribution; the digest, action and hint are already held."""
    assert not hasattr(ENTRY, absent)


@pytest.mark.parametrize("value", [(1, 1), {"sub_game": 1, "step": 1}, [1, 1], None, True, 1])
def test_an_entry_cursor_of_the_wrong_type_is_refused(value: object) -> None:
    with pytest.raises(ValueError):
        NonceRevealEntry(value, NONCE)  # type: ignore[arg-type]


WRONG_NONCES = ["0" * 32, b"0" * 32, None, True, 0, Sha256Digest("0" * 64), ("0" * 32,)]


@pytest.mark.parametrize("value", WRONG_NONCES)
def test_an_entry_nonce_of_the_wrong_type_is_refused_never_wrapped(value: object) -> None:
    """A raw 32-hex string raises: `NonceValue` has one authoritative constructor."""
    with pytest.raises(ValueError):
        NonceRevealEntry(CURSOR, value)  # type: ignore[arg-type]


def test_entry_subclasses_of_the_composed_values_are_refused() -> None:
    class LooseCursor(TurnCursor): ...

    class LooseNonce(NonceValue): ...

    with pytest.raises(ValueError):
        NonceRevealEntry(LooseCursor(FIRST_SUB_GAME, 1), NONCE)
    with pytest.raises(ValueError):
        NonceRevealEntry(CURSOR, LooseNonce("0" * 32))


@pytest.mark.parametrize("absent", ["sub_game", "role", "by_role", "game_id", "h_commit", "hint"])
def test_the_reveal_carries_exactly_its_entries_and_nothing_else(absent: str) -> None:
    """Sub-game comes from each entry's cursor; the batch names none itself."""
    assert tuple(f.name for f in dataclasses.fields(FinalNonceReveal)) == ("entries",)
    assert not hasattr(FinalNonceReveal((ENTRY,)), absent)


def test_an_empty_batch_is_structurally_valid() -> None:
    """Completeness depends on the steps actually played, so it is LIVE."""
    assert FinalNonceReveal(()).entries == ()


NOT_TUPLES = [[ENTRY], {ENTRY}, iter((ENTRY,)), (e for e in (ENTRY,)), None, True, 0, ENTRY]


@pytest.mark.parametrize("value", NOT_TUPLES)
def test_entries_that_are_not_an_exact_tuple_are_refused(value: object) -> None:
    """No list, set, generator or iterable is consumed or converted."""
    with pytest.raises(ValueError):
        FinalNonceReveal(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("member", [CURSOR, NONCE, "entry", None, (CURSOR, NONCE)])
def test_a_member_that_is_not_an_entry_is_refused(member: object) -> None:
    with pytest.raises(ValueError):
        FinalNonceReveal((ENTRY, member))  # type: ignore[arg-type]


def test_an_entry_subclass_member_is_refused() -> None:
    class LooseEntry(NonceRevealEntry): ...

    with pytest.raises(ValueError):
        FinalNonceReveal((LooseEntry(CURSOR, NONCE),))


def test_duplicates_out_of_order_and_mixed_sub_games_are_structurally_accepted() -> None:
    """These are LIVE rules; a value must never query played game state."""
    assert len(FinalNonceReveal((ENTRY, ENTRY)).entries) == 2
    late, early = (
        NonceRevealEntry(TurnCursor(1, 9), NONCE),
        NonceRevealEntry(TurnCursor(1, 2), OTHER),
    )
    assert [e.cursor.step for e in FinalNonceReveal((late, early)).entries] == [9, 2]
    other_game = NonceRevealEntry(TurnCursor(4, 1), OTHER)
    assert {e.cursor.sub_game for e in FinalNonceReveal((ENTRY, other_game)).entries} == {1, 4}


def test_both_values_are_frozen_slotted_and_value_equal() -> None:
    reveal = FinalNonceReveal((ENTRY,))
    with pytest.raises(dataclasses.FrozenInstanceError):
        reveal.entries = ()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        ENTRY.nonce = OTHER  # type: ignore[misc]
    assert not hasattr(reveal, "__dict__") and not hasattr(ENTRY, "__dict__")
    assert (NonceRevealEntry.__slots__, FinalNonceReveal.__slots__) == (
        ("cursor", "nonce"),
        ("entries",),
    )
    assert reveal == FinalNonceReveal((ENTRY,))
    assert reveal != FinalNonceReveal(())
    assert NonceRevealEntry(CURSOR, OTHER) != ENTRY
    assert NonceRevealEntry(TurnCursor(2, 1), NONCE) != ENTRY


def test_the_module_neither_hashes_nor_verifies_nor_generates() -> None:
    from mars777_police.app import peer_final_messages

    for forbidden in ("hashlib", "json", "secrets", "random", "sha256", "canonical"):
        assert not hasattr(peer_final_messages, forbidden)
    for method in ("verify", "recompute", "to_json", "serialize", "matches"):
        assert not hasattr(FinalNonceReveal, method) and not hasattr(NonceRevealEntry, method)


def test_the_reveal_is_on_the_stable_facade_and_app_surface() -> None:
    from mars777_police import app
    from mars777_police.app import peer_final_messages, peer_messages

    assert peer_messages.FinalNonceReveal is peer_final_messages.FinalNonceReveal
    assert app.FinalNonceReveal is peer_final_messages.FinalNonceReveal
    assert app.NonceRevealEntry is peer_final_messages.NonceRevealEntry
    assert {"FinalNonceReveal", "NonceRevealEntry"} <= set(app.__all__)
    assert not hasattr(peer_messages, "NonceRevealEntry")
