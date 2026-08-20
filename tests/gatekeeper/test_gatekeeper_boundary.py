"""Which calls go through the gate, and which must never be dragged into it.

This is a structural guard, not a comment. The excellence guideline §5.1 wants
every **provider** call centralised; the project's own delivery contract wants
peer gameplay left exactly where it is, because a generic resend of a turn the
opponent already applied is a protocol violation and a generic queue would break
lockstep. Both halves are asserted from the source tree.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"

GATE = ("gatekeeper", "rate_limit")

PEER_PATH = (
    "transport/client.py",
    "transport/peer_transport.py",
    "transport/peer_operations.py",
    "transport/router.py",
    "transport/kit_router.py",
    "transport/kit_server.py",
    "transport/handlers.py",
    "transport/inbound_session.py",
    "transport/kit_admin_client.py",
    "app/kit_delivery.py",
    "app/kit_play.py",
    "app/kit_half_turn.py",
    "app/kit_sub_game.py",
    "app/turn_service.py",
)


def imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("." * node.level + (node.module or ""))
    return names


def test_no_peer_gameplay_module_reaches_the_generic_gatekeeper() -> None:
    for name in PEER_PATH:
        path = SRC / name
        assert path.is_file(), name
        for module in imports(path):
            assert not any(word in module for word in GATE), f"{name} imports {module}"


def test_no_peer_transport_module_anywhere_reaches_it() -> None:
    """The list above is explicit; this is the sweep that keeps it honest."""
    for path in (SRC / "transport").rglob("*.py"):
        for module in imports(path):
            assert not any(word in module for word in GATE), f"{path.name}: {module}"


def test_the_gate_knows_nothing_about_the_game() -> None:
    """A gate that could see a turn could be tempted to resend one."""
    forbidden = ("domain", "kit_", "peer_", "turn", "commitment", "scent", "strategy", "audit")
    for name in (
        "gatekeeper.py",
        "gatekeeper_queue.py",
        "gatekeeper_retry.py",
        "gatekeeper_windows.py",
        "gatekeeper_events.py",
    ):
        for module in imports(SRC / "app" / name):
            assert not any(word in module for word in forbidden), f"{name}: {module}"


def test_the_gate_names_no_framework() -> None:
    for name in (
        "gatekeeper.py",
        "gatekeeper_queue.py",
        "gatekeeper_retry.py",
        "gatekeeper_windows.py",
        "gatekeeper_events.py",
    ):
        for module in imports(SRC / "app" / name):
            assert not any(word in module for word in ("fastmcp", "pydantic", "httpx", "ngrok"))


def test_the_provider_adapter_is_composed_with_a_gated_fetcher() -> None:
    """The converse: the one provider surface really does route through it."""
    source = (SRC / "compose_gateway.py").read_text(encoding="utf-8")

    assert "gated_fetcher(gate)" in source
    assert "Gatekeeper(load_rate_limits())" in source
