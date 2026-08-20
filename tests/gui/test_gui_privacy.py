"""The line between what a live window may show and what a replay may.

`GUI-002` forbids the objective board state while a match is being played;
`PRD07-FR-023` permits it only after the audit point, and says so in the same
breath as "this is not permission for the live GUI to do so". These tests hold
that line in the source, so the two modes cannot quietly converge.
"""

import ast
from pathlib import Path

from test_gui_architecture import GUI, imports, source

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"

OPPONENT = ("police_cell", "thief_cell", "opponent", "peer_position", "true_path")
"""Names that mean the objective board state. Lawful in replay, never in live."""

LIVE_SIDE = ("live_layout.py", "live_app.py")
REPLAY_SIDE = ("replay_layout.py", "replay_app.py")


def live_source(name: str) -> str:
    """One of the live-view application modules, as text."""
    return (SRC / "app" / name).read_text(encoding="utf-8")


def symbols(body: str) -> set[str]:
    """Every name, attribute and argument the module actually reads or writes.

    Identifiers rather than text: the live panel *prints* the words "opponent
    position: never shown", which is the guarantee itself, and a guard that
    failed on that label would teach the next author to delete the guarantee.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.FunctionDef | ast.ClassDef):
            found.add(node.name)
    return found


def names_anything(found: set[str], forbidden: str) -> bool:
    """Whether any symbol in *found* contains *forbidden*."""
    return any(forbidden in one for one in found)


def test_no_live_module_so_much_as_names_the_objective_board_state() -> None:
    for name in LIVE_SIDE:
        found = symbols(source(name))
        for forbidden in OPPONENT:
            assert not names_anything(found, forbidden), f"gui/{name} names {forbidden}"


def test_the_live_projection_itself_names_no_opponent_either() -> None:
    for name in ("live_view_values.py", "live_view_sink.py", "live_view_feed.py"):
        found = symbols(live_source(name))
        for forbidden in OPPONENT:
            assert not names_anything(found, forbidden), f"app/{name} names {forbidden}"


def test_the_replay_side_is_where_both_agents_are_allowed_to_appear() -> None:
    found = symbols(source("replay_layout.py"))
    assert "police_cell" in found
    assert "thief_cell" in found


def test_a_live_module_never_imports_a_replay_module_or_the_other_way_round() -> None:
    for name in LIVE_SIDE:
        assert not any("replay" in one for one in imports(name)), name
    for name in REPLAY_SIDE:
        assert not any(".live" in one for one in imports(name)), name


def test_the_live_window_reads_a_snapshot_and_never_the_running_game() -> None:
    reached = imports("live_app.py")
    assert reached == {
        "..app.live_view_sink",
        "..app.live_view_values",
        ".geometry",
        ".live_layout",
        ".window",
    }


def test_every_module_in_the_package_was_covered_by_one_of_these_rules() -> None:
    known = {
        *LIVE_SIDE,
        *REPLAY_SIDE,
        "__init__.py",
        "geometry.py",
        "image_renderer.py",
        "palette.py",
        "primitives.py",
        "window.py",
    }
    assert set(GUI) == known
