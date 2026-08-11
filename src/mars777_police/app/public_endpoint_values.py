"""The three peer endpoint identities, which must never be interchangeable.

`PRD05-FR-003` requires the system to distinguish **local bind address**, **own
public tunnel URL** and **opponent endpoint**, and to never substitute one for
another. A single `str` type cannot enforce that: every one of the three is a
string, so any of them type-checks wherever another is expected, and the mistake
that FR-003 exists to prevent - advertising a loopback bind as the counted
endpoint - becomes a one-character slip.

These are therefore three **distinct frozen types**, deliberately sharing no base
class that would let one satisfy another's annotation.

`MCP_PATH` is the Stage-4E-R17 FastMCP path, read from the shipped composition
(`build_server(...).http_app(path="/mcp")`) rather than assumed. The tunnel
carries a local HTTP **origin**, so the public endpoint is that origin plus this
exact path - which is why the constant lives here beside the values that use it.
"""

from dataclasses import dataclass
from typing import Final

MCP_PATH: Final[str] = "/mcp"
"""The exact FastMCP endpoint path the R17 server is mounted on."""


def _require_text(value: object, field: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field} must be a non-empty str")
    return value


@dataclass(frozen=True, slots=True)
class LocalPeerEndpoint:
    """Where our own FastMCP server is bound, locally. **Never advertised.**"""

    host: str
    port: int

    def __post_init__(self) -> None:
        _require_text(self.host, "host")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("port must be an int in 1..65535")

    @property
    def origin(self) -> str:
        """The local HTTP origin a tunnel provider is asked to expose."""
        return f"http://{self.host}:{self.port}"

    @property
    def url(self) -> str:
        """The local MCP URL, for local clients only."""
        return f"{self.origin}{MCP_PATH}"


@dataclass(frozen=True, slots=True)
class OwnPublicPeerEndpoint:
    """Our own group-level public MCP endpoint, as discovered from the provider.

    Construction only checks that a URL is present; **publicity** is a policy
    question answered by `public_endpoint_policy`, because it needs resolution
    and therefore cannot be a pure value invariant.
    """

    url: str

    def __post_init__(self) -> None:
        _require_text(self.url, "url")


@dataclass(frozen=True, slots=True)
class OpponentPublicPeerEndpoint:
    """The other group's public MCP endpoint, learned from **their** declaration.

    It is never produced by our own tunnel discovery. A separate type is what
    makes that structurally true rather than merely intended.
    """

    url: str

    def __post_init__(self) -> None:
        _require_text(self.url, "url")


def public_url_for(origin: str) -> OwnPublicPeerEndpoint:
    """Join a provider's public **origin** with the exact FastMCP path.

    The provider returns an origin such as `https://host`; appending the path by
    hand is where a double slash or a dropped segment would come from, so the
    join happens once, here, and strips exactly one trailing slash.
    """
    _require_text(origin, "origin")
    return OwnPublicPeerEndpoint(f"{origin.rstrip('/')}{MCP_PATH}")
