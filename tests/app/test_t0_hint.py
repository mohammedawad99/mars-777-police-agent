"""The temporary zero-token hint, and the one promise it is allowed to make.

Ch 6 §6.5.1 makes the template provider the book's own default - *"pre-written
sentences, selected in Python code - zero tokens, no network dependency"* - so a
truthful fixed sentence is a source-supported stopgap rather than a shortcut.
App E #26 requires free natural language and #27 forbids a numeric-position
protocol, which is why every template below is a sentence and none carries a
cell.

`hint_max_words` is NEGOTIABLE (App F T14 #2), so the producer adapts to the
value a series actually locked instead of refusing a legal config. This is
temporary: PRD-04 owns the real language policy.
"""

import pytest

from mars777_police.app.sealed_record_values import Intent
from mars777_police.app.t0_hint import t0_hint

LIMITS = (1, 2, 3, 4, 5, 15)


def _words(text: str) -> int:
    return len(text.split())


@pytest.mark.parametrize("limit", LIMITS)
def test_every_negotiable_limit_yields_a_usable_hint(limit: int) -> None:
    spoken = t0_hint(limit)
    assert isinstance(spoken.text, str)
    assert spoken.text.strip() != ""
    assert _words(spoken.text) <= limit
    assert spoken.intent is Intent.TRUTH


@pytest.mark.parametrize("limit", LIMITS)
def test_no_hint_ever_carries_a_coordinate(limit: int) -> None:
    assert not any(character.isdigit() for character in t0_hint(limit).text)
    assert "," not in t0_hint(limit).text


@pytest.mark.parametrize("limit", LIMITS)
def test_it_is_deterministic(limit: int) -> None:
    assert t0_hint(limit) == t0_hint(limit)


def test_a_generous_limit_gets_the_full_sentence() -> None:
    assert t0_hint(5).text == "I chose a legal action."
    assert t0_hint(15).text == "I chose a legal action."


def test_a_narrow_limit_gets_the_shorter_sentence() -> None:
    assert t0_hint(3).text == "Legal action chosen."
    assert t0_hint(4).text == "Legal action chosen."


def test_the_narrowest_legal_limit_still_gets_one_truthful_word() -> None:
    for limit in (1, 2):
        assert _words(t0_hint(limit).text) == 1
        assert t0_hint(limit).text == "Legal."


def test_the_config_contract_guarantees_at_least_one_word() -> None:
    from mars777_police.domain.config_sections import InvalidConfigSectionError, WorldTerms

    with pytest.raises(InvalidConfigSectionError):
        WorldTerms(map_area="", hint_max_words=0)


def test_it_refuses_a_limit_no_config_could_have_locked() -> None:
    with pytest.raises(ValueError, match="hint_max_words"):
        t0_hint(0)


def test_it_reaches_for_no_provider_and_no_network() -> None:
    import inspect

    from mars777_police.app import t0_hint as module

    source = inspect.getsource(module)
    for forbidden in ("http", "requests", "openai", "anthropic", "ollama", "random"):
        assert forbidden not in source.lower()
