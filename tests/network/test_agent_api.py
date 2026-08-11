"""Strict parsing of the measured ngrok 3.39.10 Agent API shape.

Every malformed form is a **local** ingress failure. The peer never sent this
JSON and cannot be blamed for it, so no peer protocol identity may appear here.
"""

import pytest
from net_fakes import PUBLIC_URL, tunnel_entry, tunnels_body

from mars777_police.app.protocol_errors import PeerProtocolError
from mars777_police.app.public_ingress import PublicIngressError
from mars777_police.infra.agent_api import TUNNELS_RESOURCE, parse_tunnels, select_for


def test_the_measured_resource_path_is_frozen() -> None:
    assert TUNNELS_RESOURCE == "/api/tunnels"


def test_a_measured_response_parses_into_entries() -> None:
    (entry,) = parse_tunnels(tunnels_body([tunnel_entry(8801)]))
    assert entry.identifier == "id-8801"
    assert entry.name == "command_line"
    assert entry.proto == "https"
    assert entry.public_url == PUBLIC_URL.removesuffix("/mcp")
    assert entry.upstream == "http://localhost:8801"


def test_an_empty_collection_parses_to_no_entries() -> None:
    """The measured registration window: 200 with nothing in it yet."""
    assert parse_tunnels(tunnels_body([])) == ()


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"\xff\xfe",
        b"[]",
        b'"text"',
        b"{}",
        b'{"tunnels": {}}',
        b'{"tunnels": [1]}',
        b'{"tunnels": [{"ID": "a"}]}',
        b'{"tunnels": [{"ID": "a", "config": []}]}',
        b'{"tunnels": [{"ID": "", "name": "n", "proto": "https",'
        b' "public_url": "u", "config": {"addr": "a"}}]}',
        b'{"tunnels": [{"ID": "a", "name": "n", "proto": "https",'
        b' "public_url": "u", "config": {"addr": 7}}]}',
    ],
)
def test_every_malformed_shape_is_a_local_ingress_failure(body: bytes) -> None:
    with pytest.raises(PublicIngressError) as raised:
        parse_tunnels(body)
    assert not isinstance(raised.value, PeerProtocolError)


def test_selection_matches_our_own_upstream_and_never_the_first_entry() -> None:
    """The property that prevents cross-assignment when two agents are alive."""
    entries = parse_tunnels(tunnels_body([tunnel_entry(1111), tunnel_entry(2222)]))
    chosen = select_for(entries, 2222)
    assert chosen is not None
    assert chosen.upstream.endswith(":2222")
    assert chosen is not entries[0]


def test_selection_ignores_a_non_https_entry_for_our_port() -> None:
    plain = tunnel_entry(3333, url="http://insecure.example")
    entries = parse_tunnels(tunnels_body([plain]))
    assert select_for(entries, 3333) is None


def test_selection_returns_none_while_our_endpoint_is_absent() -> None:
    entries = parse_tunnels(tunnels_body([tunnel_entry(1111)]))
    assert select_for(entries, 9999) is None
    assert select_for((), 1111) is None
