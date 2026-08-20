"""That reporting reuses the gate that exists, and owns no second one.

Ch 9 §9.3.1 asks for **one** Gatekeeper pattern in the communication module.
A reporting path with a limiter, a queue or a backoff engine of its own would
satisfy the words and defeat the design, so the absence of a second one is
checked in the source rather than promised in a docstring.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "mars777_police"
REPORTING = (
    "app/report_values.py",
    "app/report_eligibility.py",
    "app/report_message.py",
    "app/report_service.py",
    "app/report_source.py",
    "infra/gmail_credentials.py",
    "infra/gmail_sender.py",
    "infra/report_evidence.py",
    "compose_report.py",
    "report_main.py",
)

SECOND_LIMITER = (
    "GmailLimiter",
    "EmailRetryManager",
    "RateLimiter",
    "Backoff",
    "class .*Queue",
    "time.sleep",
    "asyncio.sleep",
)
"""Every shape a second limiter would take. The first is the one the gate owns."""


def source(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8")


def imports(name: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(source(name))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def test_no_reporting_module_owns_a_limiter_a_queue_or_a_sleep() -> None:
    for name in REPORTING:
        body = source(name)
        for forbidden in SECOND_LIMITER:
            assert forbidden not in body, f"{name} contains {forbidden}"


def test_the_service_reaches_the_provider_only_through_an_injected_gate() -> None:
    body = source("app/report_service.py")

    assert "self.gate(" in body
    assert "Gatekeeper(" not in body, "the service takes a gate, it does not build one"
    assert "import" not in body.split("class ReportService")[1]


def test_the_composition_is_the_only_module_that_builds_the_gate() -> None:
    builders = [name for name in REPORTING if "Gatekeeper(" in source(name)]

    assert builders == ["compose_report.py"]


def test_the_application_layer_names_no_oauth_or_http_type() -> None:
    for name in REPORTING:
        if not name.startswith("app/"):
            continue
        for module in imports(name):
            assert "urllib" not in module and "http" not in module, f"{name}: {module}"
            assert "gmail" not in module.lower(), f"{name}: {module}"


def test_the_gmail_adapter_uses_the_standard_library_like_every_other_provider() -> None:
    reached = imports("infra/gmail_sender.py")

    assert "urllib.request" in reached
    assert not any(one.startswith(("google", "googleapiclient", "httpx")) for one in reached)


def test_the_send_operation_reuses_the_shared_retry_classification() -> None:
    assert "..app.gatekeeper_retry" in imports("infra/gmail_sender.py")


def test_nothing_outside_the_reporting_path_reaches_the_gmail_adapter() -> None:
    reachers = sorted(
        path.name
        for path in SRC.rglob("*.py")
        if path.name != "gmail_sender.py" and "gmail_sender" in path.read_text(encoding="utf-8")
    )

    assert reachers == ["compose_report.py"]
