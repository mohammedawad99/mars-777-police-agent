"""Development evidence for a KIT friendly, and every claim it refuses to make.

A friendly establishes real facts - six settled sub-games, six chains that
reproduce in both directions, one series identity - and it establishes two
**absences** just as firmly: keyed Step-0 authentication never happened, and the
pinned four-tool wire has no mutual result-agreement operation to perform.

So this evidence is written under its own names, into its own root, and it says
what is missing out loud. The official counted writers are untouched: they still
refuse to produce a declaration without an authenticated peer, a config without
a verified lock, or a result without an agreement, and nothing here relaxes any
of that to reach a file count. Truth outranks the number fourteen.
"""

import pytest
from r16_builders import GAME_ID, GAME_UID, GROUP_A, GROUP_B

from mars777_police.app.artifact_store import (
    config_name,
    declaration_name,
    log_name,
    result_name,
)
from mars777_police.app.friendly_evidence import (
    DevelopmentEvidenceStore,
    friendly_series_name,
    friendly_sub_game_name,
    persist_friendly_evidence,
    series_document,
    sub_game_document,
)
from mars777_police.app.friendly_evidence_values import (
    FriendlySeriesEvidence,
    FriendlySubGameEvidence,
)
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.terminal import Outcome

SCHEDULE = (
    KitRole.POLICE,
    KitRole.THIEF,
    KitRole.POLICE,
    KitRole.THIEF,
    KitRole.POLICE,
    KitRole.THIEF,
)


def row(number: int) -> FriendlySubGameEvidence:
    return FriendlySubGameEvidence(
        sub_game=number,
        role=SCHEDULE[number - 1],
        outcome=Outcome.SURVIVAL,
        steps=34 + number % 2,
        our_commits=tuple(f"{number:02d}{index:062d}" for index in range(2)),
        peer_chain_verified=True,
        peer_result_claim="survival",
        peer_records=35,
        semantic_statuses=(("scent_truthfulness", "NOT_CHECKABLE"),),
    )


def evidence(rows: int = 6) -> FriendlySeriesEvidence:
    return FriendlySeriesEvidence(
        classification=RunClassification.friendly(kit_terms_agreement=True),
        game_id=GAME_ID,
        game_uid=GAME_UID,
        our_group=GROUP_A,
        peer_group=GROUP_B,
        schedule=SCHEDULE,
        rows=tuple(row(number) for number in range(1, rows + 1)),
    )


class _Store:
    def __init__(self) -> None:
        self.written: dict[str, object] = {}

    def store(self, name: str, document: object) -> object:
        self.written[name] = document
        return name


def test_the_series_document_says_which_two_things_are_absent() -> None:
    """The two facts a KIT friendly can never establish, named rather than omitted."""
    document = series_document(evidence())

    assert document["keyed_step0_authentication"] == "ABSENT"
    assert document["mutual_result_agreement"] == "ABSENT"
    assert document["evidence_class"] == "DEVELOPMENT_EVIDENCE"
    assert document["counted_eligible"] is False


def test_no_agreement_is_fabricated_anywhere_in_the_evidence() -> None:
    """`mutual_agreement` and `result_sha256` are the counted result's, not ours."""
    rendered = repr(series_document(evidence())) + repr(sub_game_document(row(1)))

    assert "mutual_agreement" not in rendered
    assert "result_sha256" not in rendered
    assert "peer_approved" not in rendered


def test_no_authentication_is_fabricated_anywhere_in_the_evidence() -> None:
    rendered = repr(series_document(evidence()))

    assert "step0_authenticated" not in rendered
    assert "auth_proof" not in rendered


def test_one_series_identity_across_all_six_rows() -> None:
    document = series_document(evidence())

    assert document["game_id"] == GAME_ID
    assert document["game_uid"] == GAME_UID
    assert document["group_id"] == GROUP_A
    assert document["opponent_group_id"] == GROUP_B
    assert len(document["sub_games"]) == 6


def test_the_six_role_contributions_merge_into_one_series_not_two() -> None:
    """Police and Thief are role contributors to one group series."""
    document = series_document(evidence())
    rows = document["sub_games"]

    assert [one["role"] for one in rows] == [one.value for one in SCHEDULE]
    assert sorted(one["sub_game"] for one in rows) == [1, 2, 3, 4, 5, 6]
    assert document["series_convention"] == "REFERENCE_ODD_EVEN_ALTERNATION"


def test_a_series_that_did_not_play_six_is_refused_rather_than_padded() -> None:
    with pytest.raises(LocalDefectError):
        series_document(evidence(rows=5))


def test_the_scores_come_from_the_one_existing_scoring_authority() -> None:
    """No second result engine: `outcome_line` and `cumulative_of`, unchanged."""
    document = series_document(evidence())

    assert document["sub_games"][0]["cop_score"] == 5
    assert document["sub_games"][0]["thief_score"] == 10
    assert document["role_totals"] == {"cop": 30, "thief": 60}


def test_no_group_total_or_winner_is_invented_for_an_alternating_series() -> None:
    """The counted result defines role totals; a group total under alternation is
    a number no contract fixes, so none is published."""
    document = series_document(evidence())

    assert "winner_group" not in document
    assert "group_total" not in document
    assert "diversity_reward" not in document


def test_a_not_checkable_status_is_carried_through_unchanged() -> None:
    document = sub_game_document(row(1))

    assert document["semantic_statuses"] == {"scent_truthfulness": "NOT_CHECKABLE"}


def test_development_names_never_collide_with_the_official_contract() -> None:
    official = {
        declaration_name(GAME_ID),
        result_name(GAME_ID),
        *(config_name(GAME_ID, n) for n in range(1, 7)),
        *(log_name(GAME_ID, n) for n in range(1, 7)),
    }
    ours = {
        friendly_series_name(GAME_ID),
        *(friendly_sub_game_name(GAME_ID, n) for n in range(1, 7)),
    }

    assert official.isdisjoint(ours)


def test_the_development_store_refuses_an_official_filename() -> None:
    """Structural, not remembered: the wrapper cannot write a counted name."""
    store = DevelopmentEvidenceStore(_Store())

    with pytest.raises(LocalDefectError):
        store.store(result_name(GAME_ID), {})


def test_persisting_writes_one_series_document_and_six_sub_game_documents() -> None:
    inner = _Store()

    persist_friendly_evidence(DevelopmentEvidenceStore(inner), evidence())

    assert sorted(inner.written) == sorted(
        [friendly_series_name(GAME_ID), *(friendly_sub_game_name(GAME_ID, n) for n in range(1, 7))]
    )


def test_persisted_evidence_cannot_make_a_run_counted() -> None:
    inner = _Store()
    held = evidence()

    persist_friendly_evidence(DevelopmentEvidenceStore(inner), held)

    assert held.classification.counted_capable is False
    assert held.classification.step0_authenticated is False


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
    from kit_backend_builders import backend

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


def test_each_role_contribution_has_its_own_development_filename() -> None:
    """Two backends write two files, and neither is a counted name."""
    from mars777_police.app.friendly_merge import friendly_contribution_name

    police = friendly_contribution_name(GAME_ID, KitRole.POLICE)
    thief = friendly_contribution_name(GAME_ID, KitRole.THIEF)

    assert police != thief
    assert police.startswith("friendly_") and thief.startswith("friendly_")
    assert police.endswith("_police.json") and thief.endswith("_thief.json")


def test_the_development_bundle_shares_the_one_identifier_validator() -> None:
    """One semantic `game_id`, one lexical rule.

    Stage 8A-2F needed a separate development check because the counted namer
    was lowercase-only and could not express a kit-derived id containing our own
    `MaRs-777`. Stage 8A-2G amended that format - it is PROJECT-CONTRACT, not
    source-fixed - so the second validator has no reason to exist and is gone.
    The development *filenames* stay separate; only the id rule is shared.
    """
    from mars777_police.app.artifact_store import require_game_id
    from mars777_police.app.friendly_evidence import friendly_series_name

    kit_game_id = "MaRs-777-vs-sparring-local"

    assert require_game_id(kit_game_id) == kit_game_id
    assert friendly_series_name(kit_game_id) == f"friendly_{kit_game_id}.json"


def test_a_development_name_still_refuses_anything_a_path_could_escape_through() -> None:
    from mars777_police.app.artifact_store import InvalidArtifactNameError
    from mars777_police.app.friendly_evidence import friendly_series_name

    for unsafe in ("../escape", "with/slash", "with space", ""):
        with pytest.raises(InvalidArtifactNameError):
            friendly_series_name(unsafe)
