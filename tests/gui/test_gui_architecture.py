"""That the graphical package presents, and is structurally unable to decide.

The stage prohibition is absolute: the GUI must never decide a move, a barrier,
a capture, a scent, a commitment, a verdict, a transition, a score or a result
agreement. A promise in prose is not evidence, so these read the source.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"
GUI = sorted(path.name for path in (SRC / "gui").glob("*.py"))

DECIDING = (
    "..app.turn_service",
    "..app.capture_rules",
    "..app.strategy_api",
    "..app.baseline_strategy",
    "..app.peer_runner",
    "..app.state_machine",
    "..app.semantic_replay",
    "..protocol",
    "..transport",
    "..infra",
    "..domain.terminal",
)
"""Owners of a decision. A drawing module that imported one could contradict it."""

REACHING = ("subprocess", "socket", "urllib", "http", "httpx", "requests", "ssl", "pickle")
"""Every module a picture could use to run something or leave this machine.

Checked as *imports* rather than as text: `socket` is a perfectly good English
word, and a guard that fails on a docstring explaining why there is no socket
teaches the next author to delete the explanation.
"""

FORBIDDEN = ("hashlib.", "hexdigest(", "eval(", "exec(", "pickle.")
"""Computation and execution, in the only forms that are actually calls."""


def source(name: str) -> str:
    return (SRC / "gui" / name).read_text(encoding="utf-8")


def imports(name: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(source(name))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def test_the_gui_package_was_actually_found() -> None:
    assert "live_layout.py" in GUI
    assert "replay_layout.py" in GUI


def test_no_drawing_module_imports_an_owner_of_a_decision() -> None:
    for name in GUI:
        for module in imports(name):
            assert not any(module.startswith(one) for one in DECIDING), f"{name} imports {module}"


def test_no_drawing_module_computes_or_executes_anything() -> None:
    for name in GUI:
        body = source(name)
        for forbidden in FORBIDDEN:
            assert forbidden not in body, f"gui/{name} contains {forbidden}"


def test_no_drawing_module_can_reach_the_network_or_start_a_process() -> None:
    for name in GUI:
        for module in imports(name):
            root = module.lstrip(".").split(".")[0]
            assert root not in REACHING, f"gui/{name} imports {module}"


def test_the_toolkit_is_named_in_exactly_one_module() -> None:
    users = [name for name in GUI if any("tkinter" in one for one in imports(name))]
    assert users == ["window.py"], "only the window adapter may name the toolkit"


def test_no_module_imports_the_toolkit_at_import_time() -> None:
    """Debian and Ubuntu package `tkinter` separately, so it may simply be absent.

    A module-scope `import tkinter` would make the whole graphical package
    unimportable there - including the layouts and the offscreen renderer, which
    need no toolkit at all. `gui/toolkit.py` obtains it on demand instead.
    """
    for name in GUI:
        tree = ast.parse(source(name))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom) and _at_module_scope(tree, node):
                named = {alias.name for alias in getattr(node, "names", ())}
                named.add(getattr(node, "module", "") or "")
                assert "tkinter" not in named, f"gui/{name} imports the toolkit eagerly"


def _at_module_scope(tree: ast.Module, node: ast.stmt) -> bool:
    """Whether *node* is a top-level statement rather than one inside a guard."""
    return node in tree.body


def test_the_offscreen_renderer_is_the_only_module_that_knows_about_pixels() -> None:
    users = [name for name in GUI if any(one.startswith("PIL") for one in imports(name))]
    assert users == ["image_renderer.py"]


def test_importing_the_package_pulls_in_no_toolkit_and_needs_no_display() -> None:
    assert "tkinter" not in imports("__init__.py")
