"""What the graphical command line is allowed to reach, and why it differs.

The counted operator entrypoints are held to "standard library and the facade"
so game logic cannot drift back into them. A viewer is a different kind of
program: it composes presentation. So it gets its own rule rather than an
unexamined exemption - it may reach the facade, the identity it prints, the
drawing package and the sink a live window attaches to, and nothing else.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"

STDLIB = {"argparse", "asyncio", "sys", "threading", "pathlib"}
PRESENTATION = {".sdk", ".identity", ".replay_main", ".app.live_view_sink"}
DRAWING = ".gui"


def imported(name: str) -> set[str]:
    """Every module name the file imports, absolute or relative, at any depth."""
    tree = ast.parse((SRC / name).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def test_the_graphical_command_reaches_only_the_facade_and_the_drawing_package() -> None:
    for module in imported("gui_main.py"):
        allowed = module in STDLIB or module in PRESENTATION or module.startswith(DRAWING)
        assert allowed, f"gui_main imports {module}"


def test_it_opens_a_replay_through_the_facade_rather_than_the_composition() -> None:
    reached = imported("gui_main.py")
    assert ".sdk" in reached
    assert ".compose_replay" not in reached


def test_it_reuses_the_replay_command_s_exit_semantics_rather_than_inventing_them() -> None:
    assert ".replay_main" in imported("gui_main.py")
