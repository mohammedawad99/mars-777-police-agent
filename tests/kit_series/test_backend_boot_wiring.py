"""Every loopback call the backend cannot build itself is actually connected.

This is the defect a local rehearsal found and no unit test could: the fields
existed, the settler used them, and every test passed - because every test
injected its own callables. Production left two of the three at their refusal
defaults, and the police backend died the instant it finished sub-game 1.

So the assertions here are deliberately about **which object** each member is,
not about behaviour: a test that merely watched one of them work is exactly the
test that already passed while production was broken. Bound methods are rebuilt
on every attribute access, so equality - not `is` - is what compares them.
"""

import asyncio
from typing import Any

import pytest
from kit_backend_builders import backend

from mars777_police.app.kit_backend_settlement import BackendSettlement, unavailable, uncollected
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.kit_backend_boot import KitBackendBoot
from mars777_police.transport.kit_admin_client import KitAdminClient

ROWS: list[dict[str, Any]] = [{"sub_game_number": 1}]


class Admin(KitAdminClient):
    """A real `KitAdminClient` with its one network call replaced."""

    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:1/mcp")
        self.contributed: list[dict[str, Any]] = []
        self.reported: list[int] = []

    async def settled(self, sub_game: int) -> None:
        self.reported.append(sub_game)

    async def contribute(self, row: dict[str, Any]) -> None:
        self.contributed.append(row)

    async def series_rows(self) -> list[dict[str, Any]]:
        return list(ROWS)


def booted() -> tuple[KitBackendBoot, Admin]:
    """A backend at its **unwired** defaults, which is what production starts from."""
    held = backend(KitRole.POLICE)
    held.settlement = BackendSettlement()
    boot = KitBackendBoot(held, held.context, None, "http://127.0.0.1:1/mcp", 1)  # type: ignore[arg-type]
    return boot, Admin()


def test_an_unwired_backend_refuses_rather_than_working_quietly() -> None:
    """The defaults are refusals, so a missed connection cannot pass unnoticed."""
    with pytest.raises(LocalDefectError, match="contribute its rows"):
        asyncio.run(uncollected({}))
    with pytest.raises(LocalDefectError, match="read the group's series"):
        asyncio.run(unavailable())


def test_wiring_connects_the_settlement_report() -> None:
    boot, admin = booted()
    boot._wire(admin)
    assert boot.backend.settled == admin.settled


def test_wiring_connects_the_row_contribution() -> None:
    """The half that was missing: rows had nowhere to go."""
    boot, admin = booted()
    boot._wire(admin)
    assert boot.backend.settlement.contribute == admin.contribute
    assert boot.backend.settlement.contribute is not uncollected


def test_wiring_connects_the_assembled_series() -> None:
    """The other missing half: the settler had no way to read the six rows back."""
    boot, admin = booted()
    boot._wire(admin)
    assert boot.backend.settlement.series_rows is not unavailable
    assert asyncio.run(boot.backend.settlement.series_rows()) == tuple(ROWS)


def test_the_series_arrives_as_a_tuple_the_settler_can_hash() -> None:
    """The admin call answers with a list; the scope is built from a tuple."""
    boot, admin = booted()
    boot._wire(admin)
    assert isinstance(asyncio.run(boot.backend.settlement.series_rows()), tuple)


def test_all_three_are_connected_by_one_call() -> None:
    """None of them may be wired without the others; that asymmetry was the bug."""
    boot, admin = booted()
    assert boot.backend.settlement.contribute is uncollected
    assert boot.backend.settlement.series_rows is unavailable
    boot._wire(admin)
    assert boot.backend.settled == admin.settled
    assert boot.backend.settlement.contribute == admin.contribute
    assert boot.backend.settlement.series_rows is not unavailable
