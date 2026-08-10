"""The declaration-sourced halves of the result core: who played, and where.

`ResultParticipants` and `GithubLinks` are the two members of
`RESULT_APPROVAL_CORE` that are **joined from the declaration** rather than
produced by play - Ch 9 p.79 keeps the four links a mandatory *report* field even
though repository metadata is otherwise declaration-owned (SUB-004, INV-04).
They are separated from the played-series values in `app.result_core_values` by
that ownership, and by measured line budget.

The two shared validators live here because both modules need them and neither
may grow a private copy: one representation rule, one implementation.
"""

from dataclasses import dataclass

from .result_values import InvalidResultValueError


def require_result_text(value: object, name: str) -> str:
    """Return *value* when it is a non-empty exact `str`, else refuse it."""
    if type(value) is not str:
        raise InvalidResultValueError(f"{name} must be a str, got {type(value).__name__}")
    if not value:
        raise InvalidResultValueError(f"{name} must be non-empty")
    return value


def require_result_score(value: object, name: str) -> int:
    """Return *value* when it is an exact non-negative `int`, else refuse it.

    `bool` is rejected by exact type, as everywhere else in this repository: a
    score of `True` is a coercion defect, not a score of 1.
    """
    if type(value) is not int:
        raise InvalidResultValueError(f"{name} must be an int, got {type(value).__name__}")
    if value < 0:
        raise InvalidResultValueError(f"{name} must be >= 0, got {value}")
    return value


@dataclass(frozen=True, slots=True)
class ResultParticipants:
    """The two participant `group_id`s in their canonical slots.

    Slots, never an ordering: neither `group_a` nor `group_b` implies the
    byte-wise lower id, which is what the deterministic proposer rules - the
    config initial proposal and the result timestamp - are stated on. The two
    ids must differ, because a result naming one participant twice describes no
    match that was played.
    """

    group_a: str
    group_b: str

    def __post_init__(self) -> None:
        require_result_text(self.group_a, "group_a")
        require_result_text(self.group_b, "group_b")
        if self.group_a == self.group_b:
            raise InvalidResultValueError("the two participants must have distinct group_ids")


@dataclass(frozen=True, slots=True)
class GithubLinks:
    """The four mandatory report links: both teams' police and thief repos.

    A fixed four-member object rather than a list, so a missing or duplicated
    link is unrepresentable instead of merely unlikely (JDEC-009). Reachability,
    ownership and whether a URL resolves are runtime duties elsewhere - this
    value proves only that four non-empty links were declared.
    """

    group_a_police: str
    group_a_thief: str
    group_b_police: str
    group_b_thief: str

    def __post_init__(self) -> None:
        for name in ("group_a_police", "group_a_thief", "group_b_police", "group_b_thief"):
            require_result_text(getattr(self, name), name)
