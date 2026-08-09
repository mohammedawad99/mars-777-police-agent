"""The sealed snapshot's barrier ordering and uniqueness contract (Stage 4E-R9-R2).

Barriers are logically a *set* — publicly declared cells (BAR-001), where order
carries no meaning. Serializing a set is where two honest peers most easily
diverge, so Stage 4E-R9-R1 pushed the ordering decision down into the semantic
value: `barriers` must arrive **already lexicographically sorted by `(row, col)`
and duplicate-free**. The canonical mapper therefore never sorts, deduplicates
or repairs, canonical bytes cannot depend on producer iteration order, and value
equality does not quietly become order-sensitive for a set-like collection.

The rule only bites if the value refuses rather than fixes, which is what this
file is for. Bounds, board legality and quotas stay LIVE.
"""

import pytest

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, SealedState
from mars777_police.domain.board import Position

SORTED = (Position(0, 4), Position(1, 1), Position(1, 5), Position(4, 0))


def with_barriers(barriers: object) -> SealedState:
    return SealedState(
        config_sha256=Sha256Digest("0" * 64),
        self_pos=Position(2, 3),
        barriers=barriers,  # type: ignore[arg-type]
        step=1,
        role=ActorRole.POLICE,
    )


@pytest.mark.parametrize(
    "good",
    [
        (),
        (Position(1, 1),),
        SORTED,
        (Position(1, 1), Position(1, 5)),
        (Position(0, 9), Position(1, 0)),
        (Position(0, 0), Position(0, 1), Position(0, 2)),
        (Position(0, 7), Position(3, 7), Position(9, 7)),
    ],
)
def test_an_already_ordered_unique_tuple_is_accepted(good: tuple[Position, ...]) -> None:
    """Empty, single, same-row-ascending-column and same-column-ascending-row all pass."""
    assert with_barriers(good).barriers == good


def test_the_stored_tuple_is_the_exact_object_supplied() -> None:
    """Proof there is no silent sort, copy-and-fix or rebuild behind the field."""
    assert with_barriers(SORTED).barriers is SORTED


@pytest.mark.parametrize(
    "unordered",
    [
        (Position(1, 1), Position(0, 4)),
        (Position(1, 5), Position(1, 1)),
        (Position(4, 0), Position(1, 1), Position(1, 5)),
        (Position(0, 4), Position(4, 0), Position(1, 1)),
        tuple(reversed(SORTED)),
        (Position(1, 0), Position(0, 9)),
    ],
)
def test_an_unsorted_tuple_is_refused_never_sorted(unordered: tuple[Position, ...]) -> None:
    """Row dominates column: `(1,0)` sorts after `(0,9)`, not before it."""
    with pytest.raises(ValueError):
        with_barriers(unordered)


@pytest.mark.parametrize(
    "dupes",
    [
        (Position(1, 1), Position(1, 1)),
        (Position(0, 4), Position(1, 1), Position(1, 1)),
        (*SORTED, Position(4, 0)),
        (Position(0, 0), Position(0, 0), Position(0, 1)),
    ],
)
def test_a_duplicate_is_refused_never_deduplicated(dupes: tuple[Position, ...]) -> None:
    with pytest.raises(ValueError):
        with_barriers(dupes)


@pytest.mark.parametrize(
    "bad",
    [
        [Position(1, 1)],
        {Position(1, 1)},
        frozenset({Position(1, 1)}),
        iter((Position(1, 1),)),
        (p for p in (Position(1, 1),)),
        None,
        True,
        0,
        Position(1, 1),
        "barriers",
    ],
)
def test_a_container_that_is_not_an_exact_tuple_is_refused(bad: object) -> None:
    """No list, set, iterator or generator is consumed, converted or counted."""
    with pytest.raises(ValueError):
        with_barriers(bad)


@pytest.mark.parametrize(
    "bad", [((1, 1),), ("1,1",), (None,), (Sha256Digest("0" * 64),), (Position(0, 0), (1, 1))]
)
def test_a_member_that_is_not_a_position_is_refused(bad: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        with_barriers(bad)


def test_a_position_subclass_member_is_refused() -> None:
    class LoosePosition(Position): ...

    with pytest.raises(ValueError):
        with_barriers((LoosePosition(1, 1),))


def test_ordering_uses_the_locked_coordinate_key_not_object_identity() -> None:
    """`(row, col)` is JDEC-012's key; nothing here may fall back on `repr` or `id`."""
    ascending = (Position(0, 10), Position(2, 1))
    assert with_barriers(ascending).barriers == ascending
    with pytest.raises(ValueError):
        with_barriers((Position(2, 1), Position(0, 10)))


def test_a_tuple_subclass_is_refused() -> None:
    """`type(...) is tuple`, so even a `NamedTuple`-style container cannot slip through."""

    class LooseTuple(tuple[Position, ...]): ...

    with pytest.raises(ValueError):
        with_barriers(LooseTuple((Position(1, 1),)))
