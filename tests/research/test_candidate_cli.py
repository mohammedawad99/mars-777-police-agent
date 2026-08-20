"""The candidate command line, and the doors it must not have.

Every action here reads development rows and nothing else. The tests that matter
most are the negative ones: there is no flag, and no code path, that reaches
validation, stress, or the sealed final holdout.
"""

import ast
from pathlib import Path

import pytest
from research.candidate_main import development, parse_args, screen
from research.records import write_csv
from test_research_records import record

from research import candidate_main

SOURCE = Path(candidate_main.__file__)


def _docstrings(tree: ast.AST) -> set[str]:
    """Every module, class and function docstring in a parsed source file."""
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, holders):
            text = ast.get_docstring(node, clean=False)
            if text is not None:
                found.add(text)
    return found


def _screening() -> dict[str, object]:
    """The smallest screening document the figure stage will accept."""
    cell = {
        "revision": "r1",
        "summary": "s",
        "overall": {"n": 9, "baseline_wins": 1, "candidate_wins": 2, "gains": 1, "losses": 0},
        "paired_ci": {"mean": 0.1, "ci_low": 0.0, "ci_high": 0.2},
    }
    return {"screening": {"n": 9}, "C1": cell, "C2": cell, "C3": cell, "C4": cell}


def _development(root: Path, count: int = 6) -> None:
    rows = tuple(
        record(
            scenario_id=f"{index:064d}", seed=index, outcome="CAPTURE" if index % 2 else "SURVIVAL"
        )
        for index in range(count)
    )
    write_csv(rows, root / "baseline" / "games_development.csv")


def test_the_command_line_offers_no_way_to_ask_for_a_held_out_set() -> None:
    parser_actions = parse_args(["screen"])

    assert parser_actions.action == "screen"
    for forbidden in ("--validation", "--stress", "--final-holdout", "--holdout"):
        with pytest.raises(SystemExit):
            parse_args(["screen", forbidden])


def test_no_action_can_reach_a_held_out_file() -> None:
    """Asserted on the code, not on the prose.

    The module docstring says in words that nothing here reaches validation,
    stress or the final holdout, and a guard that failed on that sentence would
    teach the next author to delete the documentation rather than keep the
    property. So docstrings are dropped and the remaining literals are checked.
    """
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    named = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    } - _docstrings(tree)

    assert not any(
        "final_holdout" in one or "validation" in one or "stress" in one for one in named
    )


def test_the_development_loader_reads_only_the_development_file(tmp_path: Path) -> None:
    _development(tmp_path)

    rows = development(tmp_path)

    assert len(rows) == 6
    assert {one.seed_set for one in rows} == {"development"}


def test_screening_records_every_candidate_including_the_ones_that_lose(
    tmp_path: Path,
) -> None:
    _development(tmp_path, 40)

    found = screen(tmp_path)

    for key in ("C1", "C2", "C3", "C4"):
        assert key in found
        assert (tmp_path / "candidates" / f"screen_{key}.csv").exists()
    assert "not final holdout" in str(found["label"])


def test_an_unknown_candidate_is_refused_rather_than_guessed(tmp_path: Path) -> None:
    _development(tmp_path)

    with pytest.raises(SystemExit, match="unknown candidate"):
        candidate_main.full(tmp_path, "C99")
