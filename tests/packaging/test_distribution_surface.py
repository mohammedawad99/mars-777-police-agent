"""What the built distribution promises to anyone who installs it.

The package ships a public SDK and is checked with `mypy --strict`, so a
consumer that installs the wheel should get the types too - PEP 561 makes that
conditional on a `py.typed` marker being **packaged**, not merely present in the
source tree. And the documented commands should be real commands, not a module
path a reader has to reconstruct.

These assert the built artifact rather than the working directory, because the
working directory is not what a grader installs.
"""

import importlib
import tomllib
import zipfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "mars777_police"
CONSOLE = {
    "mars777-agent": "mars777_police.__main__:main",
    "mars777-backend": "mars777_police.kit_backend_main:main",
    "mars777-gateway": "mars777_police.kit_gateway_main:main",
    "mars777-gui": "mars777_police.gui_main:main",
    "mars777-replay": "mars777_police.replay_main:main",
    "mars777-report": "mars777_police.report_main:main",
    "mars777-preflight": "mars777_police.gmail_preflight:main",
}


def _pyproject() -> dict[str, Any]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        document: dict[str, Any] = tomllib.load(handle)
    return document


def _wheel() -> Path:
    built = sorted((ROOT / "dist").glob("*.whl"))
    if not built:
        pytest.skip("no wheel built in this working tree; run `uv build`")
    return built[-1]


def test_the_typing_marker_exists_in_the_source_package() -> None:
    """PEP 561: without this file an installed consumer is told we are untyped."""
    assert (PACKAGE / "py.typed").is_file()


def test_the_typing_marker_is_actually_packaged_into_the_wheel() -> None:
    """Present in the tree is not the same as shipped, which is the whole point."""
    with zipfile.ZipFile(_wheel()) as archive:
        names = archive.namelist()

    assert "mars777_police/py.typed" in names


def test_every_documented_command_has_a_console_script() -> None:
    assert dict(_pyproject()["project"]["scripts"]) == CONSOLE


def test_every_console_script_target_is_importable_and_callable() -> None:
    """A named entry point that does not resolve is worse than none at all."""
    for target in CONSOLE.values():
        module_name, attribute = target.split(":")
        entry = getattr(importlib.import_module(module_name), attribute)

        assert callable(entry)


def test_the_wheel_records_those_entry_points() -> None:
    with zipfile.ZipFile(_wheel()) as archive:
        name = next(one for one in archive.namelist() if one.endswith("entry_points.txt"))
        recorded = archive.read(name).decode("utf-8")

    for command, target in CONSOLE.items():
        assert f"{command} = {target}" in recorded


def test_the_research_commands_are_deliberately_not_shipped() -> None:
    """`research/` is development evidence and is outside the distributed package.

    Shipping a benchmark entry point in the tournament wheel would suggest the
    agent needs it at play time. It does not, and the directory is not part of
    the wheel at all.
    """
    with zipfile.ZipFile(_wheel()) as archive:
        names = archive.namelist()

    assert not any(one.startswith("research/") for one in names)
    assert not any("bench_main" in one or "final_main" in one for one in names)
