"""Where the secret may live, and where it may not.

`r16_source` reads real code tokens with docstrings stripped, so a module that
merely promises these properties in prose cannot satisfy them.
"""

from r16_source import code_of, imports_of, tokens_of

from mars777_police.app import audit_disclosure_writer as writer
from mars777_police.app import nonce_source as port
from mars777_police.app import outbound_evidence_runtime as runtime
from mars777_police.app import outbound_evidence_values as values
from mars777_police.protocol import secure_nonce as provider

PRODUCERS = (runtime, values, writer, port)


def test_only_the_provider_may_reach_the_cryptographic_source() -> None:
    """One capability, one place: `app` never imports `secrets`."""
    assert "secrets" in tokens_of(provider)
    for module in PRODUCERS:
        assert "secrets" not in tokens_of(module)


def test_no_weak_randomness_is_used_anywhere() -> None:
    for module in (provider, *PRODUCERS):
        for weak in ("random", "uuid", "time", "monotonic", "counter"):
            assert weak not in tokens_of(module)


def test_the_producer_computes_no_digest_of_its_own() -> None:
    for module in PRODUCERS:
        for forbidden in ("hashlib", "sha256", "compute_commitment", "dumps", "canonical"):
            assert forbidden not in tokens_of(module)


def test_the_producer_reaches_crypto_only_through_the_registered_ports() -> None:
    tokens = tokens_of(runtime)
    assert "CommitmentPort" in tokens and "NonceSourcePort" in tokens
    assert all("protocol." not in name for name in imports_of(runtime))


def test_the_producer_touches_no_transport_infra_or_environment() -> None:
    for module in PRODUCERS:
        imported = imports_of(module)
        assert all("transport" not in name and "infra" not in name for name in imported)
        for forbidden in ("fastmcp", "httpx", "ngrok", "environ", "getenv", "socket"):
            assert forbidden not in tokens_of(module)


def test_the_producer_writes_no_file() -> None:
    """R4P is an in-memory evidence source; artifacts are later work."""
    for module in (provider, *PRODUCERS):
        for forbidden in ("open", "Path", "write_text", "write_bytes", "mkdir", "json"):
            assert forbidden not in tokens_of(module)


def test_the_prepared_turn_value_names_no_secret_member() -> None:
    body = code_of(values)
    assert "class PreparedTurn" in body.replace(" :", ":")
    prepared = body[body.index("class PreparedTurn") :]
    for secret in ("nonce", "intent", "state"):
        assert secret not in prepared


def test_the_runtime_carries_no_role_branch() -> None:
    for module in PRODUCERS:
        body = code_of(module)
        for branch in ("POLICE", "THIEF"):
            assert branch not in body
