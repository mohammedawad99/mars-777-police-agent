"""HardwareDeclaration: the frozen numeric types and the gpu/vram rule."""

from decimal import Decimal

import pytest
from pregame_builders import hardware

from mars777_police.app.team_declaration_values import InvalidTeamDeclarationError, RepositoryLinks


def test_valid_no_gpu_hardware() -> None:
    assert hardware().vram_gb is None


def test_valid_named_gpu_requires_positive_vram() -> None:
    card = hardware(gpu="RTX 4090", vram_gb=24)
    assert card.gpu == "RTX 4090"
    assert card.vram_gb == 24


@pytest.mark.parametrize("bad", [None, 1, ""])
def test_os_must_be_non_empty_str(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        hardware(os=bad)


@pytest.mark.parametrize("bad", [True, "8", 8.0, Decimal(8), None])
def test_cpu_cores_is_strict_int(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="cpu_cores must be an int"):
        hardware(cpu_cores=bad)


@pytest.mark.parametrize("bad", [0, -1])
def test_cpu_cores_must_be_positive(bad: int) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="cpu_cores must be > 0"):
        hardware(cpu_cores=bad)


@pytest.mark.parametrize("bad", [3.2, "3.2", 3, None])
def test_cpu_freq_must_be_decimal(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="cpu_freq_ghz must be a Decimal"):
        hardware(cpu_freq_ghz=bad)


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal(0), Decimal(-1)])
def test_cpu_freq_must_be_finite_and_positive(bad: Decimal) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="finite and > 0"):
        hardware(cpu_freq_ghz=bad)


@pytest.mark.parametrize("bad", [True, "16", Decimal(16), 16.0])
def test_ram_gb_is_strict_int_not_decimal(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="ram_gb must be an int"):
        hardware(ram_gb=bad)


def test_ram_gb_must_be_positive() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="ram_gb must be > 0"):
        hardware(ram_gb=0)


@pytest.mark.parametrize("bad", [True, "", 1, None])
def test_gpu_is_false_or_non_empty_str(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        hardware(gpu=bad, vram_gb=8)


def test_no_gpu_forbids_vram() -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="vram_gb must be None"):
        hardware(gpu=False, vram_gb=8)


@pytest.mark.parametrize("bad", [None, True, "8", 8.0, Decimal(8)])
def test_named_gpu_requires_strict_int_vram(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="vram_gb must be an int"):
        hardware(gpu="RTX", vram_gb=bad)


@pytest.mark.parametrize("bad", [0, -8])
def test_named_gpu_requires_positive_vram(bad: int) -> None:
    with pytest.raises(InvalidTeamDeclarationError, match="vram_gb must be > 0"):
        hardware(gpu="RTX", vram_gb=bad)


@pytest.mark.parametrize("bad", [None, 1, ""])
def test_repository_links_require_non_empty_str(bad: object) -> None:
    with pytest.raises(InvalidTeamDeclarationError):
        RepositoryLinks(bad, "https://example.invalid/t")  # type: ignore[arg-type]
    with pytest.raises(InvalidTeamDeclarationError):
        RepositoryLinks("https://example.invalid/p", bad)  # type: ignore[arg-type]
