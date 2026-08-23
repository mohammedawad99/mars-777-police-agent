"""The Step-0 authenticated core: a 19-member inventory, mechanically counted.

Every count here is derived by walking the produced projection, not by restating
a number - a member silently added to a semantic value would change the walk and
fail here rather than change a hashed payload unnoticed.

**Two different counts, and they must not be conflated.** The *declared
inventory* is **19** semantic members and never varies. The *present serialized
leaves* are **19** when the participant declares a GPU and **18** when it does
not, because `hardware.vram_gb` is the one conditional member: present exactly
when `gpu` is not `False`, and omitted - never `null` - otherwise. A test that
asserted an unconditional 19 present keys would fail on every lawful CPU-only
declaration. `test_step0_conditional_vram.py` owns that branch in full.
"""

import pytest
from r16_builders import COMMIT_A, GROUP_A, GROUP_B, START, merged, partial

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.declaration import STEP0_CORE_MEMBERS, locate, step0_core


def leaves(node: object, prefix: str = "") -> list[str]:
    """Return every leaf path of a nested projection, in sorted order."""
    if isinstance(node, dict):
        found: list[str] = []
        for key, value in node.items():
            found.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
        return sorted(found)
    return [prefix]


def test_the_declared_inventory_is_twenty_members() -> None:
    assert STEP0_CORE_MEMBERS == 20


def test_a_gpu_participant_serializes_all_twenty_inventory_members() -> None:
    core = step0_core(partial(GROUP_A, COMMIT_A), GROUP_A)
    assert len(leaves(core)) == STEP0_CORE_MEMBERS == 20


def test_a_cpu_only_participant_serializes_nineteen_of_them() -> None:
    """The inventory is unchanged; one conditional member is simply absent."""
    core = step0_core(partial(GROUP_A, COMMIT_A, vram=None), GROUP_A)
    assert len(leaves(core)) == 19 == STEP0_CORE_MEMBERS - 1


def test_vram_is_the_sole_conditional_member_of_the_inventory() -> None:
    """No other member is optional, now or by accident later."""
    with_gpu = set(leaves(step0_core(partial(GROUP_A, COMMIT_A), GROUP_A)))
    without = set(leaves(step0_core(partial(GROUP_A, COMMIT_A, vram=None), GROUP_A)))
    assert with_gpu - without == {"teams.group_b.hardware.vram_gb"}
    assert without - with_gpu == set()


def test_the_twenty_inventory_members_are_the_enumerated_ones() -> None:
    core = step0_core(partial(GROUP_A, COMMIT_A), GROUP_A)
    team = "teams.group_b"
    assert leaves(core) == sorted(
        [
            "game_id",
            "game_uid",
            "times.game_start",
            f"{team}.group_id",
            f"{team}.group_name",
            f"{team}.members",
            f"{team}.repos.police",
            f"{team}.repos.thief",
            f"{team}.mcp_endpoint",
            f"{team}.hardware.os",
            f"{team}.hardware.cpu_cores",
            f"{team}.hardware.cpu_freq_ghz",
            f"{team}.hardware.ram_gb",
            f"{team}.hardware.gpu",
            f"{team}.hardware.vram_gb",
            f"{team}.llm_model",
            f"{team}.code_version",
            f"{team}.github_commits.police",
            f"{team}.github_commits.thief",
            "token_budget_per_series",
        ]
    )


def test_the_subtree_sits_under_its_slot_key_never_under_the_group_id() -> None:
    core = step0_core(partial(GROUP_B, COMMIT_A), GROUP_B)
    teams = core["teams"]
    assert isinstance(teams, dict)
    assert list(teams) == ["group_a"]
    assert GROUP_B not in teams


def test_only_the_producing_teams_subtree_is_projected() -> None:
    core = step0_core(merged(), GROUP_A)
    teams = core["teams"]
    assert isinstance(teams, dict)
    assert list(teams) == ["group_b"]


def test_the_excluded_members_are_absent_from_the_bytes() -> None:
    raw = canonical_json_bytes(step0_core(merged(), GROUP_A))
    for forbidden in (b"game_end", b"auth_tag", b"auth_alg", b"key_id", b"step0_auth"):
        assert forbidden not in raw
    assert b"group_a" not in raw


def test_the_projection_is_deterministic_and_sorted() -> None:
    first = canonical_json_bytes(step0_core(merged(), GROUP_A))
    second = canonical_json_bytes(step0_core(merged(), GROUP_A))
    assert first == second
    assert first.index(b'"game_id"') < first.index(b'"teams"')


def test_the_cap_and_the_start_time_are_inside_the_core() -> None:
    core = step0_core(merged(), GROUP_A)
    assert core["token_budget_per_series"] == 200000
    assert core["times"] == {"game_start": START.value}


def test_an_undeclared_group_id_is_refused_rather_than_guessed() -> None:
    with pytest.raises(LocalDefectError):
        step0_core(merged(), "SOMEONE-ELSE")
    with pytest.raises(LocalDefectError):
        locate(merged(), "")


def test_locate_returns_the_slot_and_subtree() -> None:
    slot, team = locate(merged(), GROUP_B)
    assert slot == "group_a"
    assert team.group_id == GROUP_B
