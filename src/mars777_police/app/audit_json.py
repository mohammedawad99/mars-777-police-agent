"""The primitive reads every part of an untrusted audit document shares.

`audit_disclosure` reads the sealed entries and `audit_capture` reads the
capture transcript; both face the same hostile JSON and must refuse it the same
way, with the same message prefix and the same typed error. Keeping the
primitives in one place is what makes "an integer that is really a bool" or "a
position that is really a string" impossible to get right in one reader and
wrong in the other.

Every function here is fail-closed and total: it returns the exact type it
promises or raises `MalformedMessageError`. Nothing coerces, nothing defaults,
and nothing retains the caller's object - a `Position` is built fresh, so a
later mutation of the document cannot reach a value already read out of it.
"""

from ..domain.board import Position
from .protocol_errors import MalformedMessageError


def refuse(what: str) -> MalformedMessageError:
    """The one refusal shape every reader of this document raises."""
    return MalformedMessageError(f"audit disclosure {what}")


def mapping(value: object, what: str) -> dict[str, object]:
    """*value* as a JSON object, or a refusal."""
    if not isinstance(value, dict):
        raise refuse(f"{what} is not an object")
    return value


def text(source: dict[str, object], key: str) -> str:
    """A non-empty string member, refusing an absent or empty one."""
    value = source.get(key)
    if type(value) is not str or not value:
        raise refuse(f"has no usable {key!r}")
    return value


def whole(source: dict[str, object], key: str) -> int:
    """An integer member. `type(...) is not int` also refuses `True`, which
    JSON cannot tell apart from `1` but a step number must never be."""
    value = source.get(key)
    if type(value) is not int:
        raise refuse(f"has no integer {key!r}")
    return value


def point(value: object, what: str) -> Position:
    """A `[row, col]` pair as a domain `Position`, validated by the domain."""
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise refuse(f"{what} is not a two-member position")
    row, col = value
    if type(row) is not int or type(col) is not int:
        raise refuse(f"{what} is not an integer position")
    return Position(row, col)
