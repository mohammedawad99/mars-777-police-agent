"""The one conditional member of the Step-0 core, proved on both branches.

`hardware.vram_gb` is present **exactly when** `gpu` is not `False`. That makes
the produced core carry **18** present leaves for a CPU-only participant and
**19** for one with a GPU - while the *inventory* stays 19 members either way.
The two numbers answer different questions, and conflating them is what this
file exists to prevent.

The absent case must be an **omitted key**, never `null`: the canonical domain
refuses `None` outright, so emitting one would not merely be untidy - it would
make a lawful CPU-only declaration impossible to authenticate at all.
"""

import pytest
from r16_builders import COMMIT_A, GROUP_A, partial

from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.declaration import STEP0_CORE_MEMBERS, step0_core

HARDWARE_KEYS = ("os", "cpu_cores", "cpu_freq_ghz", "ram_gb", "gpu")


def hardware_of(vram: int | None) -> dict[str, object]:
    core = step0_core(partial(GROUP_A, COMMIT_A, "group_a", vram=vram), GROUP_A)
    teams = core["teams"]
    assert isinstance(teams, dict)
    hardware = teams["group_a"]["hardware"]
    assert isinstance(hardware, dict)
    return hardware


def leaves(node: object, prefix: str = "") -> list[str]:
    """Return every **present** leaf path of a produced core."""
    if isinstance(node, dict):
        found: list[str] = []
        for key, value in node.items():
            found.extend(leaves(value, f"{prefix}.{key}" if prefix else key))
        return sorted(found)
    return [prefix]


def core_of(vram: int | None) -> dict[str, object]:
    return step0_core(partial(GROUP_A, COMMIT_A, "group_a", vram=vram), GROUP_A)


def test_a_cpu_only_participant_omits_the_vram_key_entirely() -> None:
    hardware = hardware_of(None)
    assert tuple(hardware) == HARDWARE_KEYS
    assert "vram_gb" not in hardware
    assert hardware["gpu"] is False


def test_a_gpu_participant_carries_vram_exactly_once() -> None:
    hardware = hardware_of(24)
    assert tuple(hardware) == (*HARDWARE_KEYS, "vram_gb")
    assert hardware["vram_gb"] == 24
    assert hardware["gpu"] == "RTX 4090"


def test_the_cpu_only_core_has_eighteen_present_leaves() -> None:
    assert len(leaves(core_of(None))) == 18 == STEP0_CORE_MEMBERS - 1


def test_the_gpu_core_has_nineteen_present_leaves() -> None:
    assert len(leaves(core_of(24))) == 19 == STEP0_CORE_MEMBERS


def test_vram_is_the_only_structural_difference_between_the_two_branches() -> None:
    """Nothing else becomes optional because one member is conditional."""
    absent, present = set(leaves(core_of(None))), set(leaves(core_of(24)))
    assert present - absent == {"teams.group_a.hardware.vram_gb"}
    assert absent - present == set()


def test_no_json_null_is_ever_emitted_for_the_absent_member() -> None:
    raw = canonical_json_bytes(core_of(None))
    assert b'"vram_gb"' not in raw
    assert b"null" not in raw
    assert b'"gpu":false' in raw


def test_the_absent_member_is_omitted_rather_than_zeroed_or_blanked() -> None:
    hardware = hardware_of(None)
    for fabricated in (0, "", False, None):
        assert hardware.get("vram_gb", "<absent>") != fabricated or "vram_gb" not in hardware
    assert "vram_gb" not in hardware


def test_the_canonical_domain_would_have_refused_an_emitted_none() -> None:
    """Why omission is the only correct answer, not merely the tidy one."""
    with pytest.raises(ValueError):
        canonical_json_bytes({**hardware_of(None), "vram_gb": None})


def test_the_gpu_value_is_serialized_as_a_bare_json_integer() -> None:
    raw = canonical_json_bytes(core_of(24))
    assert b'"vram_gb":24' in raw
    assert b'"vram_gb":"24"' not in raw


def test_both_branches_canonicalize_deterministically() -> None:
    for vram in (None, 24):
        first, second = canonical_json_bytes(core_of(vram)), canonical_json_bytes(core_of(vram))
        assert first == second
        assert b"\r" not in first
        assert first.decode("utf-8")


def test_the_two_branches_produce_different_authenticated_bytes() -> None:
    assert canonical_json_bytes(core_of(None)) != canonical_json_bytes(core_of(24))
