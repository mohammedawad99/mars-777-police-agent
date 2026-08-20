"""Success must mean *complete enough*, not "everything present happened to pass".

An official log exists so that **every** step's commitment can be recomputed:
`LOG_CONTRACT.md` marks the nonce `Required`, `CRYPTO-008` releases it at the
end-of-game audit, and `REPLAY-002` asks for a recomputation *for each log step*.
So a replay that verified only the steps whose evidence happened to be present
has not performed the audit the source asks for, and must not report success.

**Absence is still not an accusation.** Missing evidence stays `NOT_CHECKABLE`
and gets its own exit status; it is never promoted to `TAMPERED` to make
automation fail, and never demoted to `Verified OK` to make it pass.
"""

from pathlib import Path

import pytest
import replay_fixtures as fixtures

from mars777_police import replay_main
from mars777_police.app.replay_status import audit_complete
from mars777_police.app.replay_values import ReplayCheck
from mars777_police.sdk import AgentSdk, ReplayError

OTHER = "f" * 64


def edited(tmp_path: Path, edit: object) -> tuple[Path, Path]:
    log, config = fixtures.played(tmp_path)
    document = fixtures.document(log)
    edit(document)  # type: ignore[operator]
    fixtures.rewritten(log, document)
    return log, config


def status(log: Path, config: Path) -> int:
    return replay_main.main(["--log", str(log), "--config", str(config), "--summary"])


def drop_every_nonce(document: dict[str, object]) -> None:
    document["audit"]["final_reveal"] = []  # type: ignore[index]


def drop_one_nonce(document: dict[str, object]) -> None:
    document["audit"]["final_reveal"] = document["audit"]["final_reveal"][:-1]  # type: ignore[index]


def test_a_complete_official_log_is_verified_and_successful(tmp_path: Path) -> None:
    log, config = fixtures.played(tmp_path)

    found = AgentSdk().verify_replay(log, config)

    assert found.crypto is ReplayCheck.VERIFIED_OK
    assert audit_complete(found) is True
    assert status(log, config) == 0


def test_a_missing_nonce_is_not_checkable_rather_than_tampered(tmp_path: Path) -> None:
    log, config = edited(tmp_path, drop_one_nonce)

    found = AgentSdk().verify_replay(log, config)

    assert found.crypto is ReplayCheck.NOT_CHECKABLE
    assert found.crypto is not ReplayCheck.TAMPERED


def test_a_missing_nonce_can_never_return_success(tmp_path: Path) -> None:
    log, config = edited(tmp_path, drop_one_nonce)

    assert status(log, config) != 0


def test_every_nonce_missing_can_never_return_success(tmp_path: Path) -> None:
    log, config = edited(tmp_path, drop_every_nonce)

    assert status(log, config) != 0


def test_incomplete_evidence_has_its_own_exit_status(tmp_path: Path) -> None:
    """Four, not three: a grader must tell absence from an accusation."""
    incomplete, config = edited(tmp_path, drop_one_nonce)

    assert status(incomplete, config) == 4


def test_a_real_mismatch_keeps_exit_three(tmp_path: Path) -> None:
    def tamper(document: dict[str, object]) -> None:
        for entry in document["entries"]:  # type: ignore[union-attr]
            if entry["phase"] == "commit":
                entry["commit"] = OTHER
                return

    log, config = edited(tmp_path, tamper)

    assert status(log, config) == 3


def test_the_summary_cannot_be_upgraded_by_a_later_verified_step(tmp_path: Path) -> None:
    """One unverifiable step decides the whole audit, whatever follows it."""
    log, config = edited(tmp_path, drop_one_nonce)

    found = AgentSdk().verify_replay(log, config)
    replay = AgentSdk().open_replay(log, config)
    seen = [turn.check for step in replay.steps for turn in step.turns]

    assert ReplayCheck.VERIFIED_OK in seen
    assert found.crypto is ReplayCheck.NOT_CHECKABLE
    assert audit_complete(found) is False


def test_an_official_commit_without_its_digest_is_malformed(tmp_path: Path) -> None:
    """`LOG_CONTRACT.md` marks the commitment Required; absence is corruption."""

    def strip(document: dict[str, object]) -> None:
        for entry in document["entries"]:  # type: ignore[union-attr]
            if entry["phase"] == "commit":
                del entry["commit"]
                return

    log, config = edited(tmp_path, strip)

    with pytest.raises(ReplayError, match="commit"):
        AgentSdk().open_replay(log, config)
    assert status(log, config) == 2


def test_a_not_applicable_record_does_not_make_an_audit_incomplete() -> None:
    """The completeness rule keys on unavailable evidence, not on inapplicable."""
    from mars777_police.app.replay_status import worst_check

    assert worst_check([ReplayCheck.VERIFIED_OK, ReplayCheck.NOT_APPLICABLE]) is (
        ReplayCheck.VERIFIED_OK
    )


def test_an_unavailable_record_outranks_every_verified_one() -> None:
    from mars777_police.app.replay_status import worst_check

    checks = [ReplayCheck.VERIFIED_OK, ReplayCheck.NOT_CHECKABLE, ReplayCheck.VERIFIED_OK]

    assert worst_check(checks) is ReplayCheck.NOT_CHECKABLE


def test_a_mismatch_outranks_an_unavailable_record() -> None:
    """A real accusation is not softened by evidence that was merely absent."""
    from mars777_police.app.replay_status import worst_check

    checks = [ReplayCheck.NOT_CHECKABLE, ReplayCheck.TAMPERED]

    assert worst_check(checks) is ReplayCheck.TAMPERED
