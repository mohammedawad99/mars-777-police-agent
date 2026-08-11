"""The three endpoint identities are distinct types, not three strings.

`PRD05-FR-003` forbids substituting one for another. A test that only checked
values would pass on a codebase where all three were `str`; these tests check
that the *types* differ and that the local one can never present itself as the
public one.
"""

import pytest
from net_fakes import PUBLIC_URL

from mars777_police.app.public_endpoint_values import (
    MCP_PATH,
    LocalPeerEndpoint,
    OpponentPublicPeerEndpoint,
    OwnPublicPeerEndpoint,
    public_url_for,
)


def test_the_mcp_path_is_the_shipped_r17_path() -> None:
    """Derived from the R17 composition, not assumed."""
    assert MCP_PATH == "/mcp"


def test_a_local_endpoint_exposes_an_origin_and_a_local_url() -> None:
    local = LocalPeerEndpoint("127.0.0.1", 8801)
    assert local.origin == "http://127.0.0.1:8801"
    assert local.url == "http://127.0.0.1:8801/mcp"


@pytest.mark.parametrize("host", ["", 7, None])
def test_a_local_endpoint_refuses_a_non_string_host(host: object) -> None:
    with pytest.raises(ValueError, match="host"):
        LocalPeerEndpoint(host, 8801)  # type: ignore[arg-type]


@pytest.mark.parametrize("port", [0, 65536, -1, "8801", True])
def test_a_local_endpoint_refuses_an_impossible_port(port: object) -> None:
    with pytest.raises(ValueError, match="port"):
        LocalPeerEndpoint("127.0.0.1", port)  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", [OwnPublicPeerEndpoint, OpponentPublicPeerEndpoint])
def test_a_public_endpoint_requires_a_url(kind: type) -> None:
    assert kind(PUBLIC_URL).url == PUBLIC_URL
    with pytest.raises(ValueError, match="url"):
        kind("")


def test_the_three_identities_are_three_different_types() -> None:
    """The property FR-003 needs: no accidental substitution type-checks."""
    kinds = {LocalPeerEndpoint, OwnPublicPeerEndpoint, OpponentPublicPeerEndpoint}
    assert len(kinds) == 3
    own = OwnPublicPeerEndpoint(PUBLIC_URL)
    opponent = OpponentPublicPeerEndpoint(PUBLIC_URL)
    assert type(own) is not type(opponent)
    assert own != opponent
    assert not isinstance(own, OpponentPublicPeerEndpoint)
    assert not isinstance(LocalPeerEndpoint("127.0.0.1", 9), OwnPublicPeerEndpoint)


def test_a_public_url_joins_the_origin_to_the_exact_path_once() -> None:
    assert public_url_for("https://host.example").url == "https://host.example/mcp"
    assert public_url_for("https://host.example/").url == "https://host.example/mcp"
    assert "//mcp" not in public_url_for("https://host.example/").url


def test_a_public_url_refuses_an_empty_origin() -> None:
    with pytest.raises(ValueError, match="origin"):
        public_url_for("")
