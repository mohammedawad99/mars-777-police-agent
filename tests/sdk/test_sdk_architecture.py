"""Dependency direction around the facade, checked structurally.

Two rules, both stated as directions rather than as a list of forbidden files.
Operator entrypoints may reach the standard library and the SDK; the SDK may
reach composition, but never a business authority or a framework. The point is
to stop logic drifting back into the CLIs once the facade exists.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"

ENTRYPOINTS = ("__main__.py", "kit_backend_main.py", "kit_gateway_main.py")

STDLIB = {"argparse", "asyncio", "sys", "pathlib", "os"}

BUSINESS = (
    "strategy",
    "commitment",
    "scent",
    "adjudicat",
    "scoring",
    "capture",
    "audit",
    "terminal",
)

FRAMEWORK = ("fastmcp", "pydantic", "httpx", "ngrok")


def imported_modules(path: Path) -> set[str]:
    """Every module name a file imports, absolute or relative."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("." * node.level + (node.module or ""))
    return names


def test_every_operator_entrypoint_reaches_only_the_standard_library_and_the_sdk() -> None:
    for name in ENTRYPOINTS:
        for module in imported_modules(SRC / name):
            assert module in STDLIB or module == ".sdk", f"{name} imports {module}"


def test_the_sdk_names_no_business_authority() -> None:
    for path in (SRC / "sdk").rglob("*.py"):
        for module in imported_modules(path):
            assert not any(word in module for word in BUSINESS), f"{path.name}: {module}"


def test_the_sdk_names_no_framework() -> None:
    for path in (SRC / "sdk").rglob("*.py"):
        for module in imported_modules(path):
            assert not any(word in module for word in FRAMEWORK), f"{path.name}: {module}"


def test_the_sdk_does_not_reach_into_the_domain() -> None:
    """Domain is pure game truth; a facade that touched it would own rules."""
    for path in (SRC / "sdk").rglob("*.py"):
        for module in imported_modules(path):
            assert "domain" not in module, f"{path.name}: {module}"


def test_the_version_authority_depends_on_nothing_of_ours() -> None:
    """It must be importable from anywhere, so it may import nothing inward."""
    for module in imported_modules(SRC / "shared" / "version.py"):
        assert not module.startswith("."), module
