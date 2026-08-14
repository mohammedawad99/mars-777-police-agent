"""The last refusals: wrong types, half-merged declarations, and a failed write."""

from pathlib import Path

import composed_builders as compose
import evidence_builders as ev
import pytest
import r7_builders as r7
import r7_fixtures as fixtures
from r16_builders import GROUP_A

from mars777_police.app.artifact_store import InvalidArtifactNameError, require_game_id
from mars777_police.app.log_events import verified_at
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_record import own_team
from mars777_police.app.token_accounting import InvalidTokenUsageError, SeriesTokenLedger
from mars777_police.app.turn_protocol_state import AckEvidence, TurnEvidence
from mars777_police.artifact_documents import result_document
from mars777_police.infra.artifacts import JsonArtifactStore


def test_a_game_id_that_is_not_a_string_is_refused() -> None:
    with pytest.raises(InvalidArtifactNameError, match="must be a str"):
        require_game_id(7)  # type: ignore[arg-type]


def test_a_sub_game_that_is_not_a_whole_number_is_refused() -> None:
    with pytest.raises(InvalidTokenUsageError, match="must be an int"):
        SeriesTokenLedger().usage("1")  # type: ignore[arg-type]


def test_evidence_cannot_be_observed_after_the_nonces_arrived() -> None:
    """Late turn material is a defect, not a silent addition to a closed audit."""
    producer = ev.producer()
    prepared = [ev.prepare(producer, 1)]
    receiver = ev.receiver(prepared, (1,))
    receiver.accept_final_nonce_reveal(producer.final_nonce_reveal(), ev.PEER_GROUP)
    with pytest.raises(StaleMessageError, match="cannot be observed"):
        receiver.observe((), ())


def test_a_step_after_the_tampered_one_was_never_checked() -> None:
    assert verified_at(1, None) is True
    assert verified_at(1, 2) is True
    assert verified_at(2, 2) is False
    assert verified_at(3, 2) is None


def test_a_group_that_never_declared_is_not_a_participant() -> None:
    declaration = compose.compose().identity.declaration
    with pytest.raises(LocalDefectError, match="has not declared"):
        own_team(declaration, "GROUP-ZZ")
    assert own_team(declaration, GROUP_A).group_id == GROUP_A


def test_a_result_document_needs_the_digest_the_agreement_produced() -> None:
    runtime = _series()
    exchange = fixtures.unagreed_result(runtime)
    with pytest.raises(LocalDefectError, match="local digest"):
        result_document(exchange, GROUP_A)


def _series() -> object:
    import boot_builders as build

    from mars777_police.agent_runtime import AgentRuntime
    from mars777_police.app.series_record import outcome_line
    from mars777_police.domain.terminal import Outcome

    composition = compose.after_step0(compose.compose())
    agent = AgentRuntime(composition, build.HOST, build.free_port())
    runtime = r7.series_for(agent, JsonArtifactStore(Path(".")))
    runtime.lines = tuple(outcome_line(n, Outcome.CAPTURE) for n in range(1, 7))
    return runtime


def test_a_write_that_fails_mid_file_removes_its_own_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The partial never becomes official, and it does not survive the failure."""
    store = JsonArtifactStore(tmp_path)
    original = JsonArtifactStore.__module__

    def refuse(_fd: int) -> None:
        raise OSError("the device rejected the flush")

    monkeypatch.setattr(f"{original}.os.fsync", refuse)
    with pytest.raises(OSError, match="flush"):
        store.store("log_x_g01.json", {"entries": []})
    assert list(tmp_path.iterdir()) == []


def test_an_ack_is_a_frozen_value_that_carries_only_its_three_facts() -> None:
    from dataclasses import FrozenInstanceError, fields

    ack = AckEvidence(ev.CURSOR if hasattr(ev, "CURSOR") else _cursor(), _digest(), ActorRole.THIEF)
    assert [field.name for field in fields(AckEvidence)] == ["cursor", "h_commit", "by_role"]
    with pytest.raises(FrozenInstanceError):
        ack.by_role = ActorRole.POLICE  # type: ignore[misc]
    assert [field.name for field in fields(TurnEvidence)] == [
        "cursor",
        "h_commit",
        "action",
        "hint",
        "legal",
        "scent",
    ]


def _cursor() -> object:
    from mars777_police.app.turn_cursor import TurnCursor

    return TurnCursor(1, 1)


def _digest() -> object:
    from mars777_police.app.protocol_values import Sha256Digest

    return Sha256Digest("a" * 64)


def test_the_approval_core_exists_only_once_the_result_is_agreed() -> None:
    """A report cannot present a core before the hash over it was agreed."""
    exchange = fixtures.unagreed_result(_series())
    with pytest.raises(StaleMessageError, match="once the result is agreed"):
        exchange.approval_core()
