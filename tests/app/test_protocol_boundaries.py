"""Ownership and scope boundaries of the Stage-4A phase machine.

The machine owns exactly one fact - the current phase (`STATE_OWNERSHIP.md`:
"State-machine current state | app.state_machine"). The step count belongs to
`domain.truth` and the sub-game index to `app.orchestrator`, so neither is
duplicated here, and no protocol body or crypto exists behind the
crypto-named phases.
"""

import dataclasses
import inspect

import pytest

from mars777_police.app import state_machine
from mars777_police.app.state_machine import (
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
)

SOURCE = inspect.getsource(state_machine)
FIELDS = {f.name for f in dataclasses.fields(ProtocolMachine)}

NO_CURSOR = ["sub_game", "sub_game_index", "completed_sub_games", "series", "cursor"]
NO_FLAGS = ["config_locked", "commit_sent", "ack_received", "reveal_received", "tampered", "failed"]
NO_COUNTER = ["step", "completed_steps", "turn_number", "move_number", "turn"]
NO_STATE = [
    "LocalTruth",
    "Board",
    "MoveAction",
    "BarrierAction",
    "ScentField",
    "ScoreLine",
    "Position",
]
NO_EFFECT = ["LocalTurnService", "apply_move", "place_barrier", "evaluate_terminal", "score_for"]
NO_CRYPTO = [
    "hashlib",
    "sha256",
    "H_commit",
    "hmac",
    "nonce",
    "sealed",
    "canonical",
    "json",
    "signature",
]
NO_BODY = ["intent", "hint", "payload"]
NO_TRANSPORT = [
    "socket",
    "http",
    "url",
    "fastmcp",
    "asyncio",
    "thread",
    "opponent",
    "enemy",
    "connection",
]
NO_IO = ["open(", "pathlib", "os.", "random", "uuid", "datetime", "time."]


def test_the_machine_owns_exactly_the_current_phase() -> None:
    assert tuple(f.name for f in dataclasses.fields(ProtocolMachine)) == ("phase",)
    assert ProtocolMachine.__slots__ == ("phase",)


def test_no_duplicated_step_or_turn_counter() -> None:
    for forbidden in NO_COUNTER:
        assert forbidden not in FIELDS
    for forbidden in ("completed_steps", "turn_number", "move_number"):
        assert forbidden not in SOURCE


def test_no_cursor_and_no_duplicate_boolean_phase_flags() -> None:
    for forbidden in NO_CURSOR + NO_FLAGS + ["technical_loss"]:
        assert forbidden not in FIELDS


def test_no_game_state_is_embedded() -> None:
    for forbidden in NO_STATE:
        assert forbidden not in SOURCE


def test_the_machine_never_applies_a_local_effect() -> None:
    for forbidden in NO_EFFECT:
        assert forbidden not in SOURCE


def test_the_crypto_named_phases_carry_no_crypto() -> None:
    for forbidden in NO_CRYPTO + NO_BODY:
        assert forbidden.lower() not in SOURCE.lower()
    assert ProtocolPhase.COMMIT_SENT.value == "COMMIT_SENT"
    assert ProtocolPhase.REVEAL.value == "REVEAL"


def test_no_transport_opponent_state_io_or_nondeterminism() -> None:
    for forbidden in NO_TRANSPORT:
        assert forbidden not in SOURCE.lower()
    for forbidden in NO_IO:
        assert forbidden not in SOURCE


def test_the_graph_has_one_authoritative_representation() -> None:
    assert SOURCE.count("_ALLOWED") >= 2
    assert SOURCE.count("elif") == 0


def test_the_machine_imports_nothing_outward() -> None:
    allowed = ("from dataclasses", "from enum", "from typing", "from collections")
    outward = [
        line
        for line in SOURCE.splitlines()
        if line.startswith(("from ", "import ")) and not line.startswith(allowed)
    ]
    assert outward == []


def test_the_machine_cannot_be_constructed_from_an_arbitrary_value() -> None:
    for value in ("BOOT", None, 0, ProtocolPhase):
        with pytest.raises(IllegalTransitionError):
            ProtocolMachine(value)  # type: ignore[arg-type]


def test_the_normal_bootstrap_starts_at_boot() -> None:
    assert ProtocolMachine.start().phase is ProtocolPhase.BOOT
    assert ProtocolMachine.start() == ProtocolMachine(ProtocolPhase.BOOT)


def test_the_constructor_is_documented_as_a_trusted_snapshot_primitive() -> None:
    doc = (ProtocolMachine.__doc__ or "") + (ProtocolMachine.start.__doc__ or "")
    assert "snapshot" in doc.lower()
    assert "start" in doc.lower()
