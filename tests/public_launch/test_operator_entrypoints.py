"""The two commands an operator actually runs, and what they refuse.

Neither is allowed to invent an endpoint, a role or a run class. The launcher
reads its backends from configuration and its public URL from discovery; the
backend reads its role from this repository and its sub-games from the frozen
schedule. Both refuse operator input they cannot act on rather than starting
half a run.
"""

import asyncio

import pytest
from network_fixtures import POLICE_BACKEND, THIEF_BACKEND

from mars777_police import GROUP_CODE
from mars777_police.__main__ import ROLE
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.run_class import RunClass
from mars777_police.kit_backend_boot import KitBackendBoot, backend_client
from mars777_police.transport.kit_backend_routes import KitBackendRoutes
from mars777_police.transport.transport_profiles import TransportEnvelopeProfile


def gateway_argv() -> list[str]:
    return [
        "--police-endpoint",
        POLICE_BACKEND,
        "--thief-endpoint",
        THIEF_BACKEND,
        "--ngrok",
        "/usr/bin/ngrok",
    ]


def test_the_launcher_reads_both_backends_and_the_starting_role() -> None:
    from mars777_police.kit_gateway_main import parse_args

    arguments = parse_args([*gateway_argv(), "--first-role", "thief"])

    assert arguments.police_endpoint == POLICE_BACKEND
    assert arguments.thief_endpoint == THIEF_BACKEND
    assert arguments.first_role == "thief"


def test_the_launcher_defaults_to_the_police_first_schedule() -> None:
    from mars777_police.kit_gateway_main import parse_args

    assert parse_args(gateway_argv()).first_role == "police"


def test_the_launcher_refuses_a_starting_role_outside_the_two_sides() -> None:
    from mars777_police.kit_gateway_main import parse_args

    with pytest.raises(SystemExit):
        parse_args([*gateway_argv(), "--first-role", "referee"])


def test_the_launcher_reports_an_operator_settings_failure_as_status_two() -> None:
    """A local refusal, not a peer fault, and nothing is served."""
    from mars777_police import kit_gateway_main

    assert kit_gateway_main.main(gateway_argv()) == 2


def test_the_backend_requires_every_fact_it_cannot_invent() -> None:
    from mars777_police.kit_backend_main import parse_args

    for missing in ("--launch", "--port", "--opponent", "--gateway-admin"):
        argv = [
            "--launch",
            "doc.json",
            "--port",
            "1",
            "--opponent",
            "https://x/mcp",
            "--gateway-admin",
            "http://127.0.0.1:1/mcp",
        ]
        index = argv.index(missing)
        del argv[index : index + 2]
        with pytest.raises(SystemExit):
            parse_args(argv)


def test_the_backend_reports_a_missing_launch_document_as_status_two() -> None:
    from mars777_police import kit_backend_main

    status = kit_backend_main.main(
        [
            "--launch",
            "no-such-document.json",
            "--port",
            "1",
            "--opponent",
            "https://x.example/mcp",
            "--gateway-admin",
            "http://127.0.0.1:1/mcp",
        ]
    )

    assert status == 2


def test_a_backend_contribution_needs_a_pairing_that_actually_happened() -> None:
    from kit_backend_builders import backend

    from mars777_police.kit_backend_main import persist

    with pytest.raises(LocalDefectError):
        persist(backend(KitRole.POLICE), __import__("pathlib").Path("unused"))


def test_the_backend_client_speaks_the_kit_wire_and_nothing_else() -> None:
    client = backend_client("https://partner.example/mcp", 30.0)

    assert client.profile is TransportEnvelopeProfile.KIT_EXTERNAL
    assert client.url == "https://partner.example/mcp"


def test_the_counted_runtime_is_unreachable_from_a_friendly_backend() -> None:
    """Not a stub standing in for something - a wiring defect that says so."""
    from mars777_police.kit_backend_boot import _Unreached

    with pytest.raises(LocalDefectError):
        _Unreached().on_commitment(None, None)  # type: ignore[attr-defined]


def test_a_backend_boot_serves_its_private_port_and_releases_it() -> None:
    from kit_backend_builders import backend

    held = backend(KitRole.POLICE)
    boot = KitBackendBoot(
        held,
        held.context,
        backend_client("https://x.example/mcp", 5.0),
        "http://127.0.0.1:1/mcp",
        0,
    )

    async def run() -> None:
        await boot._serve()
        from mars777_police.ingress_release import release

        assert boot.served is not None
        await release(boot.served.task, boot.served.listener)

    asyncio.run(run())

    assert boot.served is not None


def test_the_routes_open_one_session_per_role_and_close_them_together() -> None:
    routes = KitBackendRoutes({KitRole.POLICE: POLICE_BACKEND}, 5.0)

    assert sorted(routes.forwarders()) == [KitRole.POLICE]
    asyncio.run(routes.close())
    assert routes.clients == {}


def test_the_launcher_names_this_group_and_this_run_class() -> None:
    from mars777_police.public_launch_values import PublicLaunchStatus

    status = PublicLaunchStatus(
        group_id=GROUP_CODE,
        public_endpoint=None,
        run_class=RunClass.KIT_FRIENDLY_ONLY,
        evidence_root="runtime/friendly",
        backends_configured=2,
    )

    assert status.group_id == "MaRs-777"
    assert status.counted_eligible is False
    assert ROLE.value in ("police", "thief")
