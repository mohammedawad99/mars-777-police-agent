"""`TransitionEvidence` is valid by construction: legal edges only.

R7 evidence records a **successful** transition, so a value whose pair is not in
the frozen `STATE_MACHINE.md` §2 graph cannot truthfully be one. R1 ("no
skipping") makes that concrete: a record claiming COMMIT_SENT -> REVEAL asserts
something the machine forbids, so it must be impossible to build, not merely
detected downstream.

Validity is structural only. It is **not** authenticity: a hand-built value is a
well-formed edge, never proof that the edge actually occurred. Authenticity
needs the hashes, nonces and signatures of PRD-06 / replay, which Stage 4B does
not provide.
"""

import itertools

import pytest

from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
)

P = ProtocolPhase


def _legal() -> list[tuple[ProtocolPhase, ProtocolPhase]]:
    return [(s, t) for s in ProtocolPhase for t in ProtocolMachine(s).allowed_next()]


def _illegal() -> list[tuple[ProtocolPhase, ProtocolPhase]]:
    legal = set(_legal())
    return [p for p in itertools.product(ProtocolPhase, repeat=2) if p not in legal]


def test_boot_cannot_claim_a_jump_into_reveal() -> None:
    with pytest.raises(IllegalTransitionError, match="illegal transition BOOT -> REVEAL"):
        TransitionEvidence(P.BOOT, P.REVEAL)


def test_commit_sent_cannot_skip_acknowledged() -> None:
    # R1 - no skipping.
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.COMMIT_SENT, P.REVEAL)


def test_tampered_cannot_claim_a_return_to_play() -> None:
    # R5 - terminal is terminal.
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.TAMPERED, P.SUBGAME_COMPLETE)
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.FAILED, P.READY)


def test_technical_loss_has_exactly_one_legal_successor() -> None:
    assert TransitionEvidence(P.TECHNICAL_LOSS, P.SUBGAME_COMPLETE).target_phase is (
        P.SUBGAME_COMPLETE
    )
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.TECHNICAL_LOSS, P.READY)
    with pytest.raises(IllegalTransitionError):
        TransitionEvidence(P.TECHNICAL_LOSS, P.TURN_DECISION)


def test_every_legal_edge_is_constructible() -> None:
    edges = _legal()
    assert len(edges) == 31
    for source, target in edges:
        evidence = TransitionEvidence(source, target)
        assert evidence.source_phase is source
        assert evidence.target_phase is target


def test_every_illegal_ordered_pair_is_refused() -> None:
    pairs = _illegal()
    assert len(pairs) == 293
    for source, target in pairs:
        with pytest.raises(IllegalTransitionError):
            TransitionEvidence(source, target)


def test_no_phase_may_claim_a_transition_to_itself() -> None:
    for phase in ProtocolPhase:
        with pytest.raises(IllegalTransitionError):
            TransitionEvidence(phase, phase)


def test_an_absorbing_source_admits_no_evidence_at_all() -> None:
    for phase in (P.REPORT_READY, P.FAILED, P.TAMPERED):
        assert ProtocolMachine(phase).is_absorbing
        for target in ProtocolPhase:
            with pytest.raises(IllegalTransitionError):
                TransitionEvidence(phase, target)


def test_validity_is_derived_from_the_single_frozen_graph() -> None:
    """No second adjacency table: the accepted set equals ``allowed_next()``."""
    for source in ProtocolPhase:
        accepted = {t for t in ProtocolPhase if _accepts(source, t)}
        assert accepted == set(ProtocolMachine(source).allowed_next())


def _accepts(source: ProtocolPhase, target: ProtocolPhase) -> bool:
    try:
        TransitionEvidence(source, target)
    except IllegalTransitionError:
        return False
    return True


def test_a_hand_built_value_is_valid_but_not_proof_that_it_happened() -> None:
    """Valid by construction is a structural guarantee, never authenticity."""
    hand_built = TransitionEvidence(P.VALIDATING, P.TURN_COMPLETE)
    emitted = ProtocolMachine(P.VALIDATING).advance(P.TURN_COMPLETE).evidence
    assert hand_built == emitted
    for name in ("hash", "digest", "signature", "nonce", "mac", "sealed"):
        assert not hasattr(hand_built, name)


def test_type_checking_still_precedes_the_edge_check() -> None:
    with pytest.raises(IllegalTransitionError, match="source_phase must be a ProtocolPhase"):
        TransitionEvidence("BOOT", P.REVEAL)  # type: ignore[arg-type]
    with pytest.raises(IllegalTransitionError, match="target_phase must be a ProtocolPhase"):
        TransitionEvidence(P.BOOT, "REVEAL")  # type: ignore[arg-type]
