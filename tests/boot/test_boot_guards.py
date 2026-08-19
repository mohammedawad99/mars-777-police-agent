"""What BOOT must not do, and what composition must still not do."""

import dataclasses

import boot_builders as build
import composed_builders as compose
from r16_source import code_of, imports_of, tokens_of

from mars777_police import __main__ as entry
from mars777_police import (
    agent_runtime,
    compose_series,
    composition,
    composition_values,
    identity,
    launch_input,
)
from mars777_police.agent_runtime import AgentRuntime, RuntimeState

OUTER = (agent_runtime, launch_input, entry)


def test_the_runtime_holds_only_lifecycle_state() -> None:
    """No sub-game, turn, role, config, verdict, result or score."""
    assert {f.name for f in dataclasses.fields(AgentRuntime)} == {
        "composition",
        "host",
        "port",
        "path",
        "state",
        "server_task",
        "listener",
    }
    assert {member.value for member in RuntimeState} == {"NEW", "SERVING", "RUNNING", "CLOSED"}


def test_boot_runs_no_game_logic() -> None:
    for module in OUTER:
        tokens = tokens_of(module)
        for forbidden in ("send_step0", "open_turn", "reveal_turn", "acknowledge_peer_turn"):
            assert forbidden not in tokens
        for forbidden in ("strategy", "scent", "belief", "llm", "sub_game", "score"):
            assert forbidden not in tokens


def test_boot_opens_no_tunnel_and_writes_no_artifact() -> None:
    for module in OUTER:
        tokens = tokens_of(module)
        for forbidden in ("ngrok", "NgrokPublicIngress", "write_text", "write_bytes", "mkdir"):
            assert forbidden not in tokens


def test_boot_uses_no_sleep_or_poll_as_readiness() -> None:
    """Readiness is the bind; nothing here waits a guessed interval."""
    for module in (agent_runtime, entry):
        tokens = tokens_of(module)
        for forbidden in ("sleep", "poll", "retry", "monotonic", "perf_counter"):
            assert forbidden not in tokens


def test_only_the_composition_boundary_reads_the_environment() -> None:
    """Settings stay the configuration boundary.

    Stage 9A-1B1 moved the read from the command line into the composition
    module the facade delegates to; the property this guards - exactly one
    place - is unchanged, so the assertion follows it rather than being dropped.
    """
    for forbidden in ("environ", "getenv"):
        assert forbidden not in tokens_of(agent_runtime)
        assert forbidden not in tokens_of(launch_input)
        assert forbidden not in tokens_of(entry)
    assert "environ" in tokens_of(compose_series)


def test_the_launch_adapter_invents_no_schema() -> None:
    """It decodes the frozen wire models; it defines no declaration of its own."""
    body = code_of(launch_input)
    assert "decode_declaration" in body and "decode_profiles" in body
    for invented in ("game_id =", "game_uid =", "TeamDeclaration (", "HardwareDeclaration ("):
        assert invented not in body


def test_composition_still_starts_nothing() -> None:
    """R6 did not move BOOT into R5."""
    for module in (composition, composition_values):
        tokens = tokens_of(module)
        for forbidden in ("run_http_async", "create_task", "aenter", "listen", "bind"):
            assert forbidden not in tokens
    composed = compose.compose()
    assert composed.peer_client._session is None


def test_the_runtime_reaches_no_inward_layer_it_should_not() -> None:
    imported = imports_of(agent_runtime)
    assert all("domain" not in name and "protocol." not in name for name in imported)
    assert "composition_values" in "".join(imported)


def test_no_outer_module_carries_a_role_branch() -> None:
    """Only the entrypoint names a role, and it declares one rather than branching."""
    for module in (agent_runtime, launch_input, composition, composition_values):
        body = code_of(module)
        for branch in ("police", "thief", "POLICE", "THIEF"):
            assert branch not in body


def test_the_package_declares_its_role_without_branching_on_it() -> None:
    """This repository *is* one role; settings are checked against it, not asked.

    The declaration moved to `identity` at Stage 9A-1B1 so that the facade and
    every composition module agree by construction rather than by importing the
    command line. It is still exactly one constant, still with no branch.
    """
    body = code_of(identity)
    roles = [name for name in ("POLICE", "THIEF") if name in body]
    assert len(roles) == 1
    assert f"ROLE : Final [ ActorRole ] = ActorRole . {roles[0]}" in body
    assert "if" not in body
    assert entry.ROLE.value in {"police", "thief"}


def test_the_secret_is_never_printed() -> None:
    body = code_of(entry)
    for leak in ("reveal", "settings)", "print(settings"):
        assert leak not in body
    assert build.SECRET not in body
