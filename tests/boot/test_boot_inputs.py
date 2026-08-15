"""The two operator inputs permanent boot needs, and where each of them lives.

A process that plays by itself has to be told two things the serving process
never needed: **which config to open the negotiation with**, and **where its
official artifacts go**. They are deliberately given different homes.

The config candidate is a *series* fact, so it joins the launch document - and
it arrives in the frozen `NegotiatedConfigWire` shape the transport already
validates, so no second config schema exists anywhere. It is a **candidate**,
not an agreement: the peer still has to converge, and `ConfigLockRuntime` still
refuses a digest that differs.

The artifact root is a *local filesystem* fact, so it joins settings, which
`CONFIG_ARCHITECTURE.md` already makes the boundary for operator-local values.
It is never negotiated, never hashed and never crosses the wire.
"""

import json
from pathlib import Path

import executable_process as process
import pytest

from mars777_police import __main__ as entry
from mars777_police.infra.settings import ARTIFACT_ROOT, SettingsError, load_runtime_settings
from mars777_police.launch_input import LaunchInputError, parse_launch_document


def test_the_launch_document_carries_the_boot_config_candidate() -> None:
    document = json.loads(process.launch_document())
    assert set(document) == {"declaration", "profiles", "first_sub_game", "config"}


def test_the_boot_config_decodes_through_the_existing_authority() -> None:
    """No new schema: the same wire model and decoder the peer transport uses."""
    launch = parse_launch_document(process.launch_document())
    config = launch.config
    assert config.network_and_league.num_games == 6
    assert config.movement_and_barriers.max_moves >= 35
    assert launch.identity.game_id == launch.identity.declaration.game_id


def test_a_malformed_boot_config_is_refused_by_the_decoder() -> None:
    document = json.loads(process.launch_document())
    document["config"]["board_and_agents"]["grid_size"] = 1
    with pytest.raises(LaunchInputError):
        parse_launch_document(json.dumps(document))


def test_a_launch_document_without_a_config_is_refused() -> None:
    document = json.loads(process.launch_document())
    del document["config"]
    with pytest.raises(LaunchInputError):
        parse_launch_document(json.dumps(document))


def test_the_artifact_root_is_a_required_local_setting(tmp_path: Path) -> None:
    environment = process.environment(root=tmp_path)
    settings = load_runtime_settings(environment, expected_role=entry.ROLE)
    assert settings.artifact_root == tmp_path


def test_a_missing_artifact_root_refuses_the_process(tmp_path: Path) -> None:
    """No default: an ambiguous location would scatter official artifacts."""
    environment = {
        k: v for k, v in process.environment(root=tmp_path).items() if k != ARTIFACT_ROOT
    }
    with pytest.raises(SettingsError, match=ARTIFACT_ROOT):
        load_runtime_settings(environment, expected_role=entry.ROLE)


def test_the_artifact_root_never_reaches_the_peer() -> None:
    """It is local: no wire model, declaration or config names it."""
    from mars777_police.transport import wire_config, wire_declaration

    for module in (wire_config, wire_declaration):
        assert "artifact_root" not in module.__dict__
        assert "artifact_root" not in str(module.__dict__.keys())
