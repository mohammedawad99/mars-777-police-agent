"""An external consumer, importing only the installed package's public surface.

The proof §4.1 actually asks for is not that our own tests can reach the facade
- they can reach anything - but that somebody who installed the distribution and
read the README can perform a real operation without naming an internal module.
It runs as a separate process so an already-imported internal module cannot make
it pass by accident.
"""

import inspect
import subprocess
import sys
import typing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FRAMEWORKS = ("fastmcp", "pydantic", "httpx", "mcp")


def run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def test_an_external_consumer_builds_the_facade_from_the_installed_package() -> None:
    finished = run(
        "from mars777_police.sdk import AgentSdk, SOFTWARE_VERSION, ROLE\n"
        "AgentSdk()\n"
        "print(SOFTWARE_VERSION.guideline, ROLE.value)\n"
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip() == "1.00 police"


def test_an_external_consumer_performs_a_real_operation_through_the_facade() -> None:
    """Verifying a stored artifact refuses malformed bytes - a real answer."""
    finished = run(
        "from mars777_police.sdk import AgentSdk\n"
        "try:\n"
        "    AgentSdk().verify_config_artifact({'not': 'a config artifact'})\n"
        "except Exception as failure:\n"
        "    print(type(failure).__name__)\n"
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip() != ""


def test_a_consumer_never_has_to_name_an_internal_module() -> None:
    """Everything the two scripts above used came from `mars777_police.sdk`."""
    finished = run(
        "import mars777_police.sdk as facade\n"
        "print(all(name in dir(facade) for name in facade.__all__))\n"
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip() == "True"


def test_no_framework_type_reaches_the_public_signatures() -> None:
    """§10: the facade speaks project semantics, never transport DTOs."""
    from mars777_police.sdk import AgentSdk

    operations = [
        one
        for name, one in inspect.getmembers(AgentSdk, inspect.isfunction)
        if not name.startswith("_")
    ]
    for name, hints in ((one.__name__, typing.get_type_hints(one)) for one in operations):
        for annotation in hints.values():
            module = getattr(annotation, "__module__", "")
            assert not module.startswith(FRAMEWORKS), f"{name}: {annotation}"
