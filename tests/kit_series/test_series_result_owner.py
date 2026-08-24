"""Where a group's series-wide artifacts are assembled, and what licenses them.

The backend that owns sub-game six is the one that reaches a matching consensus
digest with the peer, but it cannot render the result: that needs the merged
declaration, which only the gateway holds. So the digest travels and the result
is rendered once, by the process that has both.
"""

import pytest
from r16_builders import COMMIT_A, GROUP_A, GROUP_B, merged, partial

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.series_result_owner import SeriesResultOwner
from mars777_police.domain.terminal import Outcome

DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"
OTHER = "f" * 64


def rows(count: int = 6) -> list[dict[str, object]]:
    return [
        settled_row(
            sub_game=n,
            ours=GROUP_A,
            theirs=GROUP_B,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL,
        )
        for n in range(1, count + 1)
    ]


def rendered(owner: SeriesResultOwner, **changes: object) -> dict[str, object]:
    members: dict[str, object] = {
        "declaration": merged(),
        "rows": rows(),
        "total_tokens": {GROUP_A: 10, GROUP_B: 11},
        "timestamp": "2026-08-23T18:45:00Z",
        **changes,
    }
    return owner.result(**members)  # type: ignore[arg-type]


def settled() -> SeriesResultOwner:
    owner = SeriesResultOwner()
    owner.settle(DIGEST)
    return owner


def test_a_series_with_no_reported_agreement_renders_nothing() -> None:
    with pytest.raises(LocalDefectError, match="no backend has reported a matching consensus"):
        rendered(SeriesResultOwner())


def test_the_reported_digest_licenses_the_result() -> None:
    made = rendered(settled())
    assert made["series_consensus_sha256"] == DIGEST


def test_a_second_differing_digest_is_refused_and_the_first_survives() -> None:
    """One series settles once; a late report must not change an agreed result."""
    owner = settled()
    with pytest.raises(StaleMessageError, match="already settled"):
        owner.settle(OTHER)
    assert owner.agreed == DIGEST


def test_the_same_digest_reported_twice_is_accepted() -> None:
    """A retry is not a conflict: the g06 owner may report what it already did."""
    owner = settled()
    owner.settle(DIGEST)
    assert owner.agreed == DIGEST


def test_a_malformed_digest_is_refused() -> None:
    for bad in ("", "abc", "z" * 63):
        with pytest.raises(StaleMessageError, match="64 hex characters"):
            SeriesResultOwner().settle(bad)


def test_a_half_declaration_cannot_name_both_participants() -> None:
    with pytest.raises(LocalDefectError, match="names both participants"):
        rendered(settled(), declaration=partial(GROUP_A, COMMIT_A))


def test_both_repositories_appear_for_each_participant() -> None:
    """Role attribution needs the opponent's two repositories as much as ours."""
    links = rendered(settled())["github_links"]
    assert isinstance(links, dict)
    assert set(links) == {GROUP_A, GROUP_B}
    for one in links.values():
        assert set(one) == {"police", "thief"}


def test_the_result_is_rendered_once_by_the_side_that_holds_both_facts() -> None:
    """The digest comes from a backend; the declaration comes from Step-0."""
    owner = settled()
    first, second = rendered(owner), rendered(owner)
    assert first == second
