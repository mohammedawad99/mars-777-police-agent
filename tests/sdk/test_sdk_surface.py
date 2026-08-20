"""What an external caller may import, and what it must never need to.

Guideline §4.1 asks for one entry point for every consumer - menus, CLI, GUI,
third parties - so the surface is pinned here rather than left to whatever
happens to be importable. §14.2 asks the same of `__all__`: an export list is a
promise, and a promise nobody wrote down is not one.
"""

import inspect

from mars777_police import sdk

EXPECTED = {
    "AgentSdk",
    "ROLE",
    "SOFTWARE_VERSION",
    "StrictSeriesRequest",
    "RoleBackendRequest",
    "PublicGatewayRequest",
    "ExternalMode",
    "KitRole",
    "KitBackendBoot",
    "KitPublicLauncher",
    "KitRoleBackend",
    "SdkError",
    "SoftwareVersionError",
    "SettingsError",
    "LaunchInputError",
    "TransportFailureError",
    "PeerProtocolError",
    "LocalDefectError",
    "PublicIngressError",
    "LEGEND",
    "ReplayCheck",
    "ReplayError",
    "ReplaySession",
    "ReplayStep",
    "ReplaySummary",
    "ReplayTurn",
    "board_lines",
}

OPERATIONS = {
    "run_strict_series",
    "compose_role_backend",
    "write_contribution",
    "compose_public_gateway",
    "verify_config_artifact",
    "open_replay",
    "verify_replay",
}


def test_the_package_exposes_exactly_the_names_it_promises() -> None:
    assert set(sdk.__all__) == EXPECTED


def test_every_promised_name_actually_resolves() -> None:
    for name in sdk.__all__:
        assert getattr(sdk, name) is not None


def test_the_facade_is_reachable_without_naming_an_inner_module() -> None:
    """`from mars777_police.sdk import AgentSdk`, never `sdk.sdk._Thing`."""
    from mars777_police.sdk import AgentSdk

    assert AgentSdk is sdk.AgentSdk


def test_the_facade_offers_exactly_the_operations_it_documents() -> None:
    public = {
        name
        for name, _ in inspect.getmembers(sdk.AgentSdk, inspect.isfunction)
        if not name.startswith("_")
    }

    assert public == OPERATIONS


def test_the_facade_names_this_repositorys_role_and_nothing_else() -> None:
    assert sdk.ROLE.value == "police"


def test_the_facade_publishes_the_software_version_authority() -> None:
    from mars777_police.shared.version import VERSION

    assert sdk.SOFTWARE_VERSION is VERSION


def test_the_export_list_avoids_wildcards() -> None:
    from pathlib import Path

    source = Path(inspect.getfile(sdk)).read_text(encoding="utf-8")

    assert "import *" not in source
