"""Strict parsing of the ngrok 3.39.10 local Agent API.

The shape below was **measured** against the installed agent, not recalled:
`GET /api/tunnels` returns `{"tunnels": [...], "uri": ...}`, and each entry
carries `ID`, `config`, `metrics`, `name`, `proto`, `public_url` and `uri`, with
the local target at `config.addr`.

Two measured facts drive the design. First, the API answers **200 with an empty
collection** while an endpoint is still registering, so a single read is not a
readiness signal and polling is a correctness requirement rather than patience.
Second, one agent can serve several tunnels, so selecting `tunnels[0]` would
cross-assign under concurrency; selection matches the **upstream we asked for**.

Malformed provider JSON is a local ingress failure. It is never a peer protocol
error - the peer did not send it and cannot be blamed for it.
"""

import json
from dataclasses import dataclass
from typing import Protocol

from ..app.public_ingress import PublicIngressError

TUNNELS_RESOURCE = "/api/tunnels"


class JsonFetcher(Protocol):
    """Fetches a URL and returns its raw body."""

    def fetch(self, url: str) -> bytes:
        """Return the body of *url*, raising `OSError` on any transport problem."""
        ...


@dataclass(frozen=True, slots=True)
class TunnelEntry:
    """One live endpoint as the Agent API describes it."""

    identifier: str
    name: str
    proto: str
    public_url: str
    upstream: str


def _text(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise PublicIngressError(f"agent API entry has no usable {key!r}")
    return value


def parse_tunnels(body: bytes) -> tuple[TunnelEntry, ...]:
    """Parse an `/api/tunnels` body strictly into entries."""
    try:
        payload = json.loads(body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as failure:
        raise PublicIngressError("agent API returned a body that is not JSON") from failure
    if not isinstance(payload, dict):
        raise PublicIngressError("agent API response is not a JSON object")
    listing = payload.get("tunnels")
    if not isinstance(listing, list):
        raise PublicIngressError("agent API response has no 'tunnels' collection")
    entries: list[TunnelEntry] = []
    for item in listing:
        if not isinstance(item, dict):
            raise PublicIngressError("agent API tunnel entry is not an object")
        config = item.get("config")
        if not isinstance(config, dict):
            raise PublicIngressError("agent API tunnel entry has no 'config' object")
        entries.append(
            TunnelEntry(
                _text(item, "ID"),
                _text(item, "name"),
                _text(item, "proto"),
                _text(item, "public_url"),
                _text(config, "addr"),
            )
        )
    return tuple(entries)


def select_for(entries: tuple[TunnelEntry, ...], port: int) -> TunnelEntry | None:
    """The HTTPS entry serving *port*, or `None` while none does yet.

    Matching on the upstream port is what prevents a second agent's endpoint
    from being adopted as ours when both are alive at once.
    """
    suffix = f":{port}"
    for entry in entries:
        if entry.public_url.startswith("https://") and entry.upstream.endswith(suffix):
            return entry
    return None
