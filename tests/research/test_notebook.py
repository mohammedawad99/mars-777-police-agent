"""The notebook explains; it must never be where a number is decided.

Two properties matter. It has to actually run against the committed evidence -
a notebook whose cells raise is worse than no notebook - and it must contain no
statistic of its own, because a cell is not covered by this suite and a number
that exists only there is a number nobody checks.

Executed with plain Python rather than Jupyter: the point is that every cell's
logic works and reads only committed files, which needs no notebook stack.
"""

import json
import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks" / "competitive_research.ipynb"
FORBIDDEN = (
    r"\bbootstrap\b",
    r"\bpaired_by_scenario\b",
    r"\bSubGame\b",
    r"\.play\(",
    r"\bchoose_action\b",
)
"""Matched as whole words: a bare `play(` also matches `display(`, which is how
the first version of this guard failed on the figure cell."""


def _cells(kind: str) -> list[str]:
    document = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return ["".join(one["source"]) for one in document["cells"] if one["cell_type"] == kind]


def test_the_notebook_is_mostly_explanation() -> None:
    """An explanatory surface, so prose must outweigh code.

    Asserted as a ratio rather than a cell count: the point is that this file
    explains evidence computed elsewhere, and a notebook that drifted into
    doing the work would fail here before anyone noticed by reading it.
    """
    assert NOTEBOOK.is_file()
    prose, code = _cells("markdown"), _cells("code")

    assert len(prose) > len(code)
    assert len(code) >= 4


def test_no_statistic_is_computed_only_in_a_cell() -> None:
    """The calculation authority is `research/`, which the suite covers."""
    body = "\n".join(_cells("code"))

    for pattern in FORBIDDEN:
        found = re.search(pattern, body)
        assert found is None, f"{pattern} belongs in research/, not in a cell"


def test_the_notebook_reaches_no_network_credential_or_sealed_scenario() -> None:
    body = "\n".join(_cells("code"))

    for reckless in ("requests", "urllib", "http", "token", "secret", "smtp", "gmail"):
        assert reckless not in body.lower()
    assert "sealed_set" not in body
    assert "run_once" not in body


def test_the_notebook_says_plainly_that_nothing_is_trained() -> None:
    """The one claim this project may never get wrong."""
    prose = "\n".join(_cells("markdown")).lower()

    assert "nothing in this project is trained" in prose
    assert "no learning curve" not in prose or "learning curve" in prose
    assert "strategy research progression" in prose


def test_every_code_cell_runs_against_the_committed_evidence() -> None:
    """The proof that it reproduces: run it, with no Jupyter involved."""
    if not (ROOT / "results" / "candidates" / "final_holdout_result.json").exists():
        pytest.skip("no committed research evidence in this working tree")

    class _Image:
        def __init__(self, filename: str = "") -> None:
            assert Path(filename).is_file(), filename

    display = types.ModuleType("IPython.display")
    display.Image = _Image  # type: ignore[attr-defined]
    display.display = lambda one: None  # type: ignore[attr-defined]
    parent = types.ModuleType("IPython")
    parent.display = display  # type: ignore[attr-defined]
    sys.modules["IPython"], sys.modules["IPython.display"] = parent, display

    scope: dict[str, object] = {"__name__": "__notebook__"}
    original = Path.cwd()
    try:
        for index, code in enumerate(_cells("code")):
            exec(compile(code, f"<cell {index}>", "exec"), scope)
    finally:
        sys.modules.pop("IPython", None)
        sys.modules.pop("IPython.display", None)
        assert Path.cwd() == original


def test_the_notebook_documents_how_to_reproduce_it_without_jupyter() -> None:
    prose = "\n".join(_cells("markdown"))

    assert "research.candidate_main figures" in prose
    assert "not in the committed lockfile" in prose
