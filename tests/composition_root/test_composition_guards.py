"""What composition must not be, and what it must not do."""

import dataclasses

import composed_builders as build
from r16_source import imports_of, tokens_of

from mars777_police import composition, composition_values
from mars777_police.app import active_runtime_context as context
from mars777_police.app import peer_runner
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.result_core_runtime import SubGameOutcomeLine
from mars777_police.app.result_core_values import CumulativeResult, ResultApprovalCore
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.transport import peer_operations


def names(value: type) -> set[str]:
    return {field.name for field in dataclasses.fields(value)}


def test_the_runtime_context_is_not_a_registry() -> None:
    """Typed slots only - no string key can name anything here."""
    body = tokens_of(context)
    for generic in ("dict", "Mapping", "getattr", "setattr", "register", "lookup"):
        assert generic not in body


def test_the_runtime_context_stays_inside_the_application() -> None:
    imported = imports_of(context)
    assert all("transport" not in name and "infra" not in name for name in imported)
    for forbidden in ("fastmcp", "httpx", "ngrok", "environ", "getenv", "socket", "open"):
        assert forbidden not in tokens_of(context)


def test_composition_never_runs_anything() -> None:
    """Construction only: the words that would start something are absent."""
    body = tokens_of(composition) | tokens_of(composition_values)
    for forbidden in ("run", "serve", "sleep", "aenter", "__aenter__", "start", "listen"):
        assert forbidden not in body


def test_composition_reads_no_environment_of_its_own() -> None:
    """Settings is the only configuration boundary."""
    body = tokens_of(composition) | tokens_of(composition_values)
    for forbidden in ("environ", "getenv", "load_dotenv", "ngrok", "open", "Path"):
        assert forbidden not in body


def test_composition_implements_no_cryptography() -> None:
    body = tokens_of(composition) | tokens_of(composition_values)
    for forbidden in ("hashlib", "sha256", "hmac", "secrets", "dumps", "canonical"):
        assert forbidden not in body


def test_composition_contains_no_result_placeholder() -> None:
    """No fabricated score, commit, token count or outcome at startup."""
    from r16_source import code_of

    body = code_of(composition) + code_of(composition_values)
    for fabrication in ("placeholder", "dummy", "TODO", "unplayed", "pending"):
        assert fabrication.lower() not in body.lower()
    assert "SubGameOutcomeLine (" not in body
    assert "ResultContribution (" not in body


def test_the_two_adapters_resolve_the_result_lazily() -> None:
    """Both are `Callable[[], ResultExchange]`, not a held instance."""
    for module, holder in ((peer_runner, "PeerRunner"), (peer_operations, "InboundPeerOperations")):
        annotations = dataclasses.fields(getattr(module, holder))
        results = next(f for f in annotations if f.name == "results")
        assert "Callable" in str(results.type)


def test_no_result_value_gained_a_lifecycle_marker() -> None:
    """Late binding is local wiring; the hashed values are untouched."""
    assert names(ResultAgreement) == {
        "game_id",
        "game_uid",
        "declaration_ref",
        "timestamp",
        "contribution",
    }
    assert names(ResultContribution) == {"group_id", "entries"}
    assert names(ResultContributionEntry) == {"sub_game", "github_commit", "tokens"}
    assert names(SubGameOutcomeLine) == {"sub_game", "cop_score", "thief_score", "outcome"}
    assert names(CumulativeResult) == {"cop_total", "thief_total", "series_outcome"}
    for invented in ("pending", "unplayed", "placeholder", "bound", "late"):
        assert invented not in names(ResultApprovalCore)


def test_the_composition_carries_no_role_branch() -> None:
    from r16_source import code_of

    body = code_of(composition) + code_of(composition_values)
    for branch in ("POLICE", "THIEF", "police", "thief"):
        assert branch not in body


def test_the_secret_never_reaches_the_composition_value() -> None:
    """`AuthSecret.reveal` is used once, and the result is not stored here."""
    composed = build.compose()
    assert "secret" not in {f.name for f in dataclasses.fields(composed)}
    assert build.SHARED.decode() not in repr(composed.identity)
