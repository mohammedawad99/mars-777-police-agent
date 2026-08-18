"""What a perfect friendly is still not, and why nothing can turn it into one.

Six sub-games, every chain reproducing, both sides agreeing every row - and the
run is still **not counted**, for two independent reasons that this stage does
not weaken: the source requires keyed producer authentication at Step-0 and the
pinned peer offers only an unkeyed content agreement, and the sparring group is
synthetic rather than an enrolled opponent.

None of this depends on an operator remembering it. `counted_capable` is derived
from the run class, the readiness gate reads `step0_authenticated` from the same
fact, and there is no counted mail path in this build at all.
"""

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.kit_friendly_result import KitFriendlyResult
from mars777_police.app.run_class import RunClass, RunClassification
from mars777_police.domain.terminal import Outcome

SIX = (Outcome.SURVIVAL,) * 6


def perfect_friendly() -> KitFriendlyResult:
    """Everything a friendly can possibly achieve, all at once."""
    return KitFriendlyResult(
        RunClassification.friendly(kit_terms_agreement=True),
        SIX,
        crypto_audit_passed=True,
        semantic_audit_clean=True,
        peer_audit_received=True,
        result_agreed=True,
    )


def test_a_perfect_six_game_friendly_is_still_not_counted_eligible() -> None:
    result = perfect_friendly()

    assert result.exact_six is True
    assert result.complete is True
    assert result.counted_eligible is False
    assert result.keyed_auth is False


def test_counted_readiness_refuses_a_friendly_on_the_step_zero_check() -> None:
    """The gate reads the same fact the run class already reported."""
    from test_readiness_gate import facts

    from mars777_police.app.public_readiness_gate import ReadinessCheck, evaluate

    friendly = RunClassification.friendly(kit_terms_agreement=True)
    verdict = evaluate(facts(step0_authenticated=friendly.step0_authenticated))

    assert verdict.is_ready is False
    assert ReadinessCheck.STEP0_AUTHENTICATED in {one.check for one in verdict.failures}


def test_the_counted_auth_profile_is_untouched() -> None:
    assert AuthProfile.HMAC_SHA256.value == "HMAC_SHA256"
    assert "KIT_SIGNATURE" not in {one.value for one in AuthProfile}
    assert "NONE" not in {one.value for one in AuthProfile}


def test_there_is_no_counted_mail_path_for_a_friendly_to_enter() -> None:
    """No reporting owner exists in this build, so none can be reached by accident."""
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "src"
    senders = [
        path.name
        for path in src.rglob("*.py")
        if "smtplib" in path.read_text(encoding="utf-8")
        or "gmail" in path.read_text(encoding="utf-8").lower()
    ]

    assert senders == []


def test_a_friendly_carries_no_counted_metadata() -> None:
    """No diversity reward, no counted-game count, no league ledger state."""
    result = perfect_friendly()

    assert result.classification.run_class is RunClass.KIT_FRIENDLY_ONLY
    assert result.classification.wire_view() == {}


def test_no_run_class_token_ever_reaches_the_peer() -> None:
    assert "KIT_FRIENDLY_ONLY" not in repr(perfect_friendly().classification.wire_view())


def test_a_counted_run_needs_the_key_to_have_spoken() -> None:
    assert RunClassification.counted(keyed_auth_satisfied=True).counted_capable is True
    assert RunClassification.counted(keyed_auth_satisfied=False).counted_capable is False
