"""Stage-4E-R16 non-scope guards: what implementing the runtime must not add.

The peer-family inventory is exactly **eight**. R16 made four of them
executable; it created no ninth, no acknowledgement family, no universal
`accepted` flag and no token-accounting evidence. Those absences are the half of
the stage a reader cannot see from the code that *is* there, so they are
asserted here.
"""

import pkgutil

import pytest
from r16_source import tokens_of

from mars777_police import app
from mars777_police.app import (
    config_lock_runtime,
    config_negotiation_runtime,
    peer_messages,
    ports,
    result_agreement_gates,
    result_agreement_runtime,
    result_core_runtime,
    step0_runtime,
)

RUNTIMES = (
    step0_runtime,
    config_negotiation_runtime,
    config_lock_runtime,
    result_core_runtime,
    result_agreement_runtime,
)


def test_the_facade_still_exposes_exactly_the_implemented_families() -> None:
    assert peer_messages.__all__ == [
        "Acknowledgement",
        "Commitment",
        "ConfigLockContext",
        "ConfigLockEvidence",
        "ConfigProposal",
        "FinalNonceReveal",
        "ResultAgreement",
        "Reveal",
        "Step0DeclarationExchange",
        "TurnCursor",
    ]


@pytest.mark.parametrize(
    "invented",
    [
        "Step0Ack",
        "ConfigAck",
        "ConfigProposalAck",
        "ConfigLockAck",
        "ResultAck",
        "ResultAgreementAck",
        "FinalAuditAck",
        "MoveValidation",
        "FinalAuditVerdictMessage",
    ],
)
def test_no_acknowledgement_family_was_invented(invented: str) -> None:
    assert not hasattr(peer_messages, invented)
    for module in RUNTIMES:
        assert not hasattr(module, invented)


def test_no_local_runtime_value_leaked_onto_the_peer_facade() -> None:
    for local in (
        "ResultApprovalCore",
        "SubGameOutcomeLine",
        "ConfigLockGate",
        "Step0Completion",
        "MutualAgreementGate",
        "ResultParticipants",
        "GithubLinks",
        "CumulativeResult",
    ):
        assert not hasattr(peer_messages, local)


def test_no_universal_accepted_flag_crosses_any_boundary() -> None:
    for module in (*RUNTIMES, ports):
        assert tokens_of(module).isdisjoint({"accepted", "is_valid", "ok"})


def test_the_app_package_export_list_gained_no_runtime_value() -> None:
    for absent in ("ResultApprovalCore", "PeerProtocolError", "Step0Runtime", "ports"):
        assert absent not in app.__all__


def test_no_token_accounting_evidence_was_introduced() -> None:
    """`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE` remains BLOCKED-BY-CONSTRUCTION."""
    for module in RUNTIMES:
        code = {token.lower() for token in tokens_of(module)}
        assert code.isdisjoint({"merkle", "receipt", "ledger", "meter", "attestation"})


def test_the_app_package_still_has_no_transport_submodule() -> None:
    found = {name for _, name, _ in pkgutil.iter_modules(app.__path__)}
    for forbidden in ("mcp_server", "mcp_client", "transport", "reporter", "gui", "settings"):
        assert forbidden not in found


def test_the_result_agreement_completes_on_a_digest_never_a_boolean_verdict() -> None:
    gates = tokens_of(result_agreement_gates)
    assert "Sha256Digest" in gates
    assert "mutual_agreement" not in gates
    assert "mutual_agreement" not in tokens_of(result_agreement_runtime)


def test_the_local_agreement_state_is_never_a_peer_field() -> None:
    from mars777_police.app.peer_final_messages import ResultAgreement

    for absent in ("mutual_agreement", "result_sha256", "accepted", "reported_by"):
        assert absent not in {field for field in ResultAgreement.__dataclass_fields__}
