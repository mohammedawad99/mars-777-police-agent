"""That the viewer reads, delegates, projects and formats - and does nothing else.

`REPLAY-001` asks for a viewer, not a second implementation of the game. A
replay that decided legality for itself could disagree with the audit, and the
disagreement would be indistinguishable from a real finding.
"""

import ast
import inspect
from pathlib import Path

from mars777_police import sdk

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"

VIEWER = (
    "app/replay_values.py",
    "app/replay_log.py",
    "app/replay_crypto.py",
    "app/replay_board.py",
    "app/replay_session.py",
    "replay_main.py",
)

FORBIDDEN = (
    "hashlib",
    "hexdigest",
    "sha256(",
    "import random",
    "import secrets",
    "pickle",
    "eval(",
    "exec(",
)
"""Computation and unsafe evaluation. `config_sha256` is a field name, not a hash."""


def source(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8")


def imports(name: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(source(name))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def test_no_viewer_module_computes_a_digest_itself() -> None:
    for name in VIEWER:
        body = source(name)
        for forbidden in FORBIDDEN:
            assert forbidden not in body, f"{name} contains {forbidden}"


def test_the_viewer_delegates_legality_to_the_existing_replay_engine() -> None:
    assert ".semantic_replay" in imports("app/replay_session.py")


def test_the_viewer_delegates_the_digest_to_the_commitment_port() -> None:
    assert ".ports" in imports("app/replay_crypto.py")


def test_the_viewer_reimplements_no_rule_module() -> None:
    """It may hold positions; it may not hold movement, barrier or scent rules."""
    for name in VIEWER:
        for module in imports(name):
            for rule in ("domain.rules", "domain.barriers", "domain.scent", "domain.terminal"):
                assert rule not in module, f"{name} imports {module}"


def test_the_command_reaches_only_the_standard_library_and_the_sdk() -> None:
    for module in imports("replay_main.py"):
        assert module in {"argparse", "sys", "pathlib"} or module == ".sdk", module


def test_the_replay_surface_is_public_and_framework_neutral() -> None:
    for name in ("ReplaySession", "ReplaySummary", "ReplayStep", "ReplayTurn", "ReplayCheck"):
        assert name in sdk.__all__
    hints = inspect.signature(sdk.AgentSdk.verify_replay).return_annotation

    assert hints is sdk.ReplaySummary


def test_no_transport_or_framework_type_reaches_the_public_replay_values() -> None:
    for name in ("app/replay_values.py",):
        for module in imports(name):
            assert "transport" not in module and "pydantic" not in module
