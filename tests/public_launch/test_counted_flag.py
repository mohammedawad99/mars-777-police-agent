"""The operator's word turning into what a run is allowed to be worth.

Nothing about a running process makes its own worth visible, so the distinction
travels from the command line rather than being inferred from a launch document,
a secret being present or an endpoint answering. These tests pin that the safe
value is the default, that the flag is the only way to leave it, and that the
run class an operator is shown follows the same decision.
"""

from pathlib import Path

from network_fixtures import launcher, service, tracking_ingress

from mars777_police.app.counted_mode import CountedMode, counted, rehearsal
from mars777_police.app.run_class import RunClass
from mars777_police.kit_gateway_main import parse_args
from mars777_police.operator_requests import PublicGatewayRequest

ARGS = [
    "--police-endpoint",
    "http://127.0.0.1:1/mcp",
    "--thief-endpoint",
    "http://127.0.0.1:2/mcp",
    "--ngrok",
    "/usr/bin/ngrok",
]


def test_a_command_without_the_flag_is_a_rehearsal() -> None:
    """Nobody reaches a counted run by omission."""
    assert parse_args(ARGS).counted is False


def test_the_flag_is_the_only_way_to_a_counted_run() -> None:
    assert parse_args([*ARGS, "--counted"]).counted is True


def test_the_request_defaults_to_the_safe_value() -> None:
    request = PublicGatewayRequest(
        police_endpoint="http://127.0.0.1:1/mcp",
        thief_endpoint="http://127.0.0.1:2/mcp",
        ngrok=Path("/usr/bin/ngrok"),
    )
    assert request.counted is False


def test_the_operator_view_reports_a_rehearsal_as_friendly_only() -> None:
    live = launcher(service(tracking_ingress("https://x.example.com/mcp")))
    live.counted = rehearsal()
    assert live.status().run_class is RunClass.KIT_FRIENDLY_ONLY


def test_the_operator_view_reports_a_counted_run_as_counted_capable() -> None:
    """The status an operator reads must not disagree with what the run may do."""
    live = launcher(service(tracking_ingress("https://x.example.com/mcp")))
    live.counted = counted()
    assert live.status().run_class is RunClass.COUNTED_CAPABLE


def test_a_launcher_built_without_a_mode_is_a_rehearsal() -> None:
    live = launcher(service(tracking_ingress("https://x.example.com/mcp")))
    assert live.counted.mode is CountedMode.REHEARSAL
    assert not live.counted.may_report
