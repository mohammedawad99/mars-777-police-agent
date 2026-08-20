"""What the checker scans, what it ignores, and what it reports.

The gate has to be reproducible: the same tree must give the same answer for a
contributor and for CI, in the same order, or a failing build is a coin toss.
"""

from pathlib import Path

from check_python_loc import LIMIT, main, over_limit


def tree(root: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


def big(lines: int) -> str:
    return "x = 1\n" * lines


def test_a_clean_tree_reports_nothing(tmp_path: Path) -> None:
    tree(tmp_path, {"src/a.py": big(LIMIT), "tests/b.py": big(1)})

    assert over_limit(tmp_path) == []


def test_production_python_is_scanned(tmp_path: Path) -> None:
    tree(tmp_path, {"src/pkg/a.py": big(LIMIT + 1)})

    assert [path for path, _ in over_limit(tmp_path)] == ["src/pkg/a.py"]


def test_test_python_is_scanned_too(tmp_path: Path) -> None:
    """§6.1 rule 6: test files obey the same cap."""
    tree(tmp_path, {"tests/unit/test_a.py": big(LIMIT + 1)})

    assert [path for path, _ in over_limit(tmp_path)] == ["tests/unit/test_a.py"]


def test_the_reported_count_is_the_effective_one(tmp_path: Path) -> None:
    tree(tmp_path, {"src/a.py": "# note\n\n" + big(LIMIT + 3)})

    assert over_limit(tmp_path) == [("src/a.py", LIMIT + 3)]


def test_files_outside_the_two_trees_are_ignored(tmp_path: Path) -> None:
    tree(tmp_path, {"tools/t.py": big(LIMIT + 1), "docs/d.py": big(LIMIT + 1)})

    assert over_limit(tmp_path) == []


def test_non_python_files_are_ignored(tmp_path: Path) -> None:
    tree(tmp_path, {"src/a.md": big(LIMIT + 1), "tests/b.txt": big(LIMIT + 1)})

    assert over_limit(tmp_path) == []


def test_findings_are_sorted_so_the_output_is_deterministic(tmp_path: Path) -> None:
    tree(
        tmp_path,
        {
            "tests/z.py": big(LIMIT + 1),
            "src/m.py": big(LIMIT + 2),
            "src/a.py": big(LIMIT + 3),
        },
    )

    assert [path for path, _ in over_limit(tmp_path)] == [
        "src/a.py",
        "src/m.py",
        "tests/z.py",
    ]


def test_a_missing_tree_is_not_an_error(tmp_path: Path) -> None:
    """A repository without a `tests/` directory is unusual, not broken."""
    tree(tmp_path, {"src/a.py": big(1)})

    assert over_limit(tmp_path) == []


def test_the_command_succeeds_on_a_clean_tree(tmp_path: Path, capsys: object) -> None:
    tree(tmp_path, {"src/a.py": big(LIMIT)})

    assert main([str(tmp_path)]) == 0


def test_the_command_fails_and_names_every_offender(tmp_path: Path, capsys: object) -> None:
    tree(tmp_path, {"src/a.py": big(LIMIT + 1), "tests/b.py": big(LIMIT + 9)})

    status = main([str(tmp_path)])
    printed = capsys.readouterr().out  # type: ignore[attr-defined]

    assert status == 1
    assert "src/a.py" in printed and "tests/b.py" in printed
    assert str(LIMIT + 9) in printed


def test_the_command_defaults_to_this_repository() -> None:
    """Run with no argument, the checker measures the tree it ships in."""
    assert main([]) == 0
