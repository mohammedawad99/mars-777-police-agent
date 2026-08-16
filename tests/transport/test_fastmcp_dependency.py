"""The dependency is pinned, importable, and the API R17 needs is present.

Stage 4E-R17 stopped because FastMCP was neither declared nor locked. This file
keeps that from silently regressing, and pins the exact version: an unpinned or
drifting transport is precisely what makes two peers disagree.
"""

import inspect
import tomllib
from importlib.metadata import version
from pathlib import Path

import fastmcp
import pydantic
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError

COMPOSITION_ROOT = frozenset({"composition.py", "composition_values.py", "launch_input.py"})
"""The outer files allowed to name the framework: composition (5-R5) and the
launch-input adapter (5-R6), which validates the already-frozen wire models."""

DIRECT_DEPENDENCIES = ["fastmcp==3.4.6", "pydantic==2.13.4"]
"""The project's exact direct runtime dependencies.

`pydantic` is **direct**, not merely inherited through FastMCP: R17 production
DTOs import `BaseModel`, `ConfigDict(extra="forbid")` and the string constraints
themselves, and a package a project imports directly is a package the project
owns. Relying on a transitive edge would let a FastMCP release quietly change an
API this project calls.
"""


def test_both_direct_dependencies_are_declared_with_exact_pins() -> None:
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == DIRECT_DEPENDENCIES


def test_nothing_else_was_promoted_to_direct_ownership() -> None:
    """`mcp`, `pydantic-core` and `pydantic-settings` stay transitive."""
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    names = {pin.split("==")[0] for pin in project["project"]["dependencies"]}
    assert names == {"fastmcp", "pydantic"}
    assert names.isdisjoint({"mcp", "pydantic-core", "pydantic-settings"})


def test_the_installed_version_is_the_pinned_one() -> None:
    assert fastmcp.__version__ == "3.4.6"


def test_the_resolved_stack_is_the_audited_one() -> None:
    """`mcp` and `pydantic` arrive transitively; their versions are pinned by the lock."""
    assert pydantic.VERSION == "2.13.4"
    assert version("pydantic") == "2.13.4"
    assert version("mcp") == "1.29.0"
    assert version("fastmcp") == "3.4.6"


def test_the_server_supports_strict_input_validation() -> None:
    """Without it the wire would lean on Pydantic's lenient coercion."""
    assert "strict_input_validation" in inspect.signature(FastMCP.__init__).parameters


def test_the_streamable_http_transport_is_available() -> None:
    """HTTP is the frozen peer transport; STDIO is probe-only."""
    assert StreamableHttpTransport is not None
    assert hasattr(FastMCP("t"), "http_app")


def test_the_client_and_call_support_a_timeout() -> None:
    """`response_timeout_sec` must be wirable rather than hard-coded."""
    assert "timeout" in inspect.signature(Client.__init__).parameters
    assert "timeout" in inspect.signature(Client.call_tool).parameters


def test_the_framework_error_type_is_available() -> None:
    assert issubclass(ToolError, Exception)


def test_only_the_transport_package_imports_the_framework_stack() -> None:
    """R17-R1 forbade these imports anywhere; R17-RESUME confines them.

    The stage that was authorized to write the adapter has written it, so the
    question changed from *whether* `fastmcp` and `pydantic` may be imported to
    *where*. The answer is the layers **inward** of the adapter: `app`, `domain`,
    `protocol` and `infra` must all remain testable, and portable, without the
    framework.

    Stage 5-R5 widened this by exactly one place. The composition root sits
    outside `transport` and its job is assembling the graph, so it names
    `FastMCP` for the type of the server it builds - and nothing else. The
    protection this test exists for is unchanged: the four inward layers are
    still checked, and the allowance is a named file, not a directory.
    """
    src = Path(__file__).resolve().parents[2] / "src"
    offenders = sorted(
        str(path.relative_to(src))
        for path in src.rglob("*.py")
        if path.parent.name != "transport"
        and path.name not in COMPOSITION_ROOT
        and any(
            line.startswith(("import fastmcp", "from fastmcp", "import pydantic", "from pydantic"))
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    )
    assert offenders == []


def test_the_transport_package_is_where_the_framework_actually_lives() -> None:
    """The converse: the confinement above is not vacuous.

    An inventory, not a prohibition - the rule is that the framework stays
    *inside* this package, and the list records who currently relies on that
    allowance. `session_deadline` joined it when the held session's response
    deadline had to follow the locked configuration: it builds the framework's
    own `StreamableHttpTransport` through the documented client-factory seam,
    which is precisely the kind of adapter this package exists to hold.
    """
    src = Path(__file__).resolve().parents[2] / "src"
    users = [
        path.name
        for path in src.rglob("*.py")
        if path.parent.name == "transport"
        and any(
            line.startswith(("import fastmcp", "from fastmcp"))
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    ]
    assert sorted(users) == [
        "client.py",
        "server.py",
        "session_deadline.py",
        "wire_errors.py",
    ]
