"""The language policy: what this side says, and how honestly it means it.

Ch 6 §6.5.1 makes the template provider the book's own default - *"pre-written
sentences, selected in Python code - zero tokens, no network dependency"* - so
this path is the reference one, not a placeholder for a model.

Two properties carry the whole stage. **Nothing leaves without passing the
validator**, so a candidate that broke App E #27 could not reach `Reveal.hint`
even if a future author wrote one. And **`intent` is honest**: every sentence
here asserts only what `LocalTurnService.apply` has already established, so
`Intent.TRUTH` is a fact about the text rather than a default.
"""

import pytest
from r16_builders import config as locked_config

from mars777_police.app.config_rules import hints_of
from mars777_police.app.hint_policy import HintPort, TemplateHintPolicy
from mars777_police.app.hint_validator import counted_words, normalised, validate_hint
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move

CAPS = (1, 2, 3, 4, 5, 8, 15, 40)
"""Every cap a series may lock, including the App F floor of 1."""

MOVE = MoveAction(Move.N)
BARRIER = BarrierAction(Position(2, 2))
ACTIONS = (MOVE, BARRIER)


def policy(cap: int, role: ActorRole = ActorRole.POLICE) -> TemplateHintPolicy:
    return TemplateHintPolicy(role=role, hint_max_words=cap)


@pytest.mark.parametrize("cap", CAPS)
@pytest.mark.parametrize("step", [1, 2, 3, 7, 20])
def test_every_cap_and_step_yields_a_legal_hint(cap: int, step: int) -> None:
    """The floor of 1 is a legal locked value, so it must have an answer."""
    spoken = policy(cap).choose(TurnCursor(1, step), MOVE)

    assert spoken.text.strip() != ""
    assert counted_words(spoken.text) <= cap
    assert validate_hint(spoken.text, cap).accepted
    assert spoken.intent is Intent.TRUTH


@pytest.mark.parametrize("cap", CAPS)
@pytest.mark.parametrize("action", ACTIONS)
def test_both_action_classes_are_spoken_for(action: object, cap: int) -> None:
    spoken = policy(cap).choose(TurnCursor(1, 1), action)  # type: ignore[arg-type]

    assert validate_hint(spoken.text, cap).accepted


def test_the_catalogue_has_real_variety() -> None:
    """LLM-002 is not honoured by one hardwired sentence repeated forever."""
    said = {policy(15).choose(TurnCursor(1, step), MOVE).text for step in range(1, 12)}

    assert len(said) >= 3


def test_selection_is_deterministic_and_carries_no_position() -> None:
    """Same semantic inputs, same sentence - and the cell never enters the choice."""
    first = policy(15).choose(TurnCursor(2, 5), MOVE)
    again = policy(15).choose(TurnCursor(2, 5), MOVE)

    assert first == again
    assert not any(character.isdigit() for character in first.text)


def test_a_narrow_cap_shortens_rather_than_refusing() -> None:
    """A locked cap of 1 must not let language veto lawful counted play."""
    spoken = policy(1).choose(TurnCursor(1, 1), MOVE)

    assert counted_words(spoken.text) == 1


class Coordinates:
    """A catalogue that breaks App E #27, to prove the policy still cannot."""

    def texts(self, action: object) -> tuple[str, ...]:
        return ("x=3 y=4",)


def test_a_candidate_that_breaks_the_prohibition_never_escapes() -> None:
    """The validator owns the outgoing hint, not the catalogue that proposed it."""
    unsafe = TemplateHintPolicy(role=ActorRole.POLICE, hint_max_words=15, catalogue=Coordinates())

    spoken = unsafe.choose(TurnCursor(1, 1), MOVE)

    assert spoken.text != "x=3 y=4"
    assert validate_hint(spoken.text, 15).accepted
    assert spoken.intent is Intent.TRUTH


class TooLong:
    def texts(self, action: object) -> tuple[str, ...]:
        return ("one two three four five six",)


def test_an_over_length_candidate_is_replaced_not_truncated_into_nonsense() -> None:
    spoken = TemplateHintPolicy(
        role=ActorRole.POLICE, hint_max_words=3, catalogue=TooLong()
    ).choose(TurnCursor(1, 1), MOVE)

    assert counted_words(spoken.text) <= 3
    assert validate_hint(spoken.text, 3).accepted


def test_the_policy_satisfies_the_port() -> None:
    assert isinstance(policy(15), HintPort)


@pytest.mark.parametrize("cap", CAPS)
@pytest.mark.parametrize("action", ACTIONS)
def test_what_is_spoken_is_already_its_own_normal_form(action: object, cap: int) -> None:
    """One authoritative text: what is validated is what is sealed.

    `hint` is one of the eight `H_commit` members and the final audit compares
    the disclosed string against the one we witnessed, so a hint that were
    normalised *after* validation would seal bytes nobody checked. Returning
    text that is already NFC and already stripped removes the second form
    entirely - there is nothing left for a later stage to quietly rewrite.
    """
    spoken = policy(cap).choose(TurnCursor(1, 1), action)  # type: ignore[arg-type]

    assert normalised(spoken.text) == spoken.text


def test_the_locked_config_owns_the_cap() -> None:
    """`hints_of` reads the negotiated word budget; nothing hard-codes 15."""
    narrow = hints_of(_with_cap(2), ActorRole.POLICE)
    wide = hints_of(_with_cap(12), ActorRole.POLICE)

    assert counted_words(narrow.choose(TurnCursor(1, 1), MOVE).text) <= 2
    assert counted_words(wide.choose(TurnCursor(1, 1), MOVE).text) <= 12


def _with_cap(cap: int):
    import dataclasses

    from mars777_police.domain.config_sections import WorldTerms

    base = locked_config()
    return dataclasses.replace(base, world=WorldTerms(base.world.map_area, cap))
