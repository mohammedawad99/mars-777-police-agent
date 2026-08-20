"""Each role's own rows, and the one series they merge into.

Alternation means each backend plays half the sub-games, so neither side holds a
whole series. What is pinned here is that a backend contributes **only** what it
played, that two contributions become one series rather than two, and that a
disagreement or a gap is refused rather than padded.
"""

import pytest
from kit_backend_builders import backend
from r16_builders import GAME_ID, GAME_UID, GROUP_A, GROUP_B
from test_friendly_evidence import row

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.terminal import Outcome


def contribution(role: KitRole) -> object:
    from mars777_police.app.friendly_merge import contribution_document

    ours = tuple(r for r in (row(n) for n in range(1, 7)) if r.role is role)
    return contribution_document(
        role=role,
        game_id=GAME_ID,
        game_uid=GAME_UID,
        our_group=GROUP_A,
        peer_group=GROUP_B,
        rows=ours,
    )


def test_each_role_backend_contributes_only_its_own_rows() -> None:
    from mars777_police.app.friendly_merge import contribution_document  # noqa: F401

    police, thief = contribution(KitRole.POLICE), contribution(KitRole.THIEF)

    assert [one["sub_game"] for one in police["sub_games"]] == [1, 3, 5]
    assert [one["sub_game"] for one in thief["sub_games"]] == [2, 4, 6]
    assert police["role"] == "police"


def test_two_contributions_merge_into_one_series_and_not_two() -> None:
    from mars777_police.app.friendly_merge import merge_contributions

    merged = merge_contributions(
        (contribution(KitRole.POLICE), contribution(KitRole.THIEF)),
        RunClassification.friendly(kit_terms_agreement=True),
    )

    assert merged["game_id"] == GAME_ID
    assert merged["game_uid"] == GAME_UID
    assert [one["sub_game"] for one in merged["sub_games"]] == [1, 2, 3, 4, 5, 6]
    assert merged["keyed_step0_authentication"] == "ABSENT"


def test_contributions_that_disagree_on_the_series_are_refused() -> None:
    """One group series has one identity; two would be two series."""
    from mars777_police.app.friendly_merge import merge_contributions

    police = dict(contribution(KitRole.POLICE))
    police["game_uid"] = "0" * 8

    with pytest.raises(LocalDefectError):
        merge_contributions(
            (police, contribution(KitRole.THIEF)),
            RunClassification.friendly(kit_terms_agreement=True),
        )


def test_a_merge_missing_a_sub_game_is_refused_rather_than_padded() -> None:
    from mars777_police.app.friendly_merge import merge_contributions

    with pytest.raises(LocalDefectError):
        merge_contributions(
            (contribution(KitRole.POLICE),),
            RunClassification.friendly(kit_terms_agreement=True),
        )


def test_a_contribution_carries_no_mutable_game_state() -> None:
    """References and settled facts only - never a board, a position or a nonce."""
    rendered = repr(contribution(KitRole.POLICE))

    for forbidden in ("board", "own_position", "nonce", "barriers", "smell_grid"):
        assert forbidden not in rendered


def test_a_backend_projects_only_the_sub_games_it_actually_played() -> None:
    """The projection invents nothing: a fact the backend does not hold is absent."""

    from mars777_police.app.commitment_codecs import CommitmentCodec
    from mars777_police.app.friendly_backend_evidence import BackendWitness, backend_rows
    from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim
    from mars777_police.app.kit_records import KitRecordChain
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    held = backend(KitRole.POLICE)
    role = held.kit_role
    witness = BackendWitness()
    outcomes = {}
    chains = {}
    verified = {}
    for number in held.ours:
        outcomes[number] = Outcome.SURVIVAL
        chains[number] = KitRecordChain(
            CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource()
        )
        verified[number] = True
        witness.steps[number] = 34
        witness.record(number, KitAuditReveal(role, (), KitResultClaim.SURVIVAL))

    rows = backend_rows(
        role=role, outcomes=outcomes, chains=chains, verified=verified, witnessed=witness
    )

    assert [one.sub_game for one in rows] == list(held.ours)
    assert all(one.role is role for one in rows)
    assert all(one.peer_result_claim == "survival" for one in rows)
    assert all(one.semantic_statuses == (("scent_truthfulness", "NOT_CHECKABLE"),) for one in rows)


def test_a_sub_game_the_backend_never_played_has_no_row() -> None:
    from mars777_police.app.friendly_backend_evidence import BackendWitness, backend_rows

    rows = backend_rows(
        role=KitRole.POLICE, outcomes={}, chains={}, verified={}, witnessed=BackendWitness()
    )

    assert rows == ()
