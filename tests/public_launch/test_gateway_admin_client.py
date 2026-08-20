"""The loopback settlement client, before it has a session and after it has none.

Settlement is signalled, so the client that signals it has to refuse to report
without a session rather than pretend, and closing one that never opened has to
be safe - teardown runs on paths where nothing was ever acquired.
"""

import asyncio

import pytest


def test_the_admin_client_refuses_to_report_before_its_session_is_open() -> None:
    """A settlement that never left is worse than one that failed loudly."""
    from mars777_police.transport.kit_admin_client import KitAdminClient

    with pytest.raises(RuntimeError):
        asyncio.run(KitAdminClient("http://127.0.0.1:1/mcp").settled(1))


def test_closing_an_admin_client_that_never_opened_is_safe() -> None:
    from mars777_police.transport.kit_admin_client import KitAdminClient

    asyncio.run(KitAdminClient("http://127.0.0.1:1/mcp").__aexit__(None, None, None))
