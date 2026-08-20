"""Reading the one local rate-limit configuration file this repository ships.

Guideline §5.2 requires the limits to come from a file rather than from code, so
this is the only place that turns bytes into a `RateLimitConfig`. Every way the
file can be wrong ends in a typed refusal: a gate running limits nobody wrote
would be worse than no gate at all.

**Nothing is defaulted quietly.** A missing file, unreadable bytes, a missing
key, an unknown key or an unsupported version all refuse. The committed
`config/rate_limits.json` is the bundled configuration; there is no second,
code-declared copy of it to drift against.

**No secret belongs here.** The file carries limits only - the tunnel credential
is the operator's own agent configuration and the peer key is environment-only.
"""

import json
from pathlib import Path
from typing import Final

from ..shared.rate_limits import RateLimitConfig, RateLimitConfigError, RateLimitPolicy

RATE_LIMITS_PATH: Final[Path] = Path(__file__).resolve().parents[3] / "config" / "rate_limits.json"
"""The committed configuration, at the location the guideline names."""

FIELDS: Final[tuple[str, ...]] = (
    "requests_per_minute",
    "requests_per_hour",
    "concurrent_max",
    "queue_depth",
    "max_retries",
    "retry_after_seconds",
    "max_backoff_seconds",
    "retryable_statuses",
)
"""Required of every service. A document missing one of these is refused."""

OPTIONAL: Final[tuple[str, ...]] = (
    "admission",
    "burst_capacity",
    "daily_quota",
    "dos_burst_limit",
    "dos_window_seconds",
)
"""The admission extension. Absent, a service keeps the rolling windows exactly.

Optional rather than required because that is what keeps every already-valid
`1.00` document valid and unchanged in behaviour - see the version-bump policy
in `shared/rate_limits`."""


def _section(document: object) -> dict[str, object]:
    if not isinstance(document, dict) or not isinstance(document.get("rate_limits"), dict):
        raise RateLimitConfigError("the document has no `rate_limits` object")
    section: dict[str, object] = document["rate_limits"]
    return section


def _policy(name: str, raw: object) -> RateLimitPolicy:
    if not isinstance(raw, dict):
        raise RateLimitConfigError(f"service {name!r} is not an object")
    unknown = sorted(set(raw) - set(FIELDS) - set(OPTIONAL))
    if unknown:
        raise RateLimitConfigError(f"service {name!r} has unknown key(s): {', '.join(unknown)}")
    missing = sorted(set(FIELDS) - set(raw))
    if missing:
        raise RateLimitConfigError(f"service {name!r} is missing: {', '.join(missing)}")
    statuses = raw["retryable_statuses"]
    if not isinstance(statuses, list):
        raise RateLimitConfigError(f"service {name!r} retryable_statuses must be a list")
    values = {field: raw[field] for field in FIELDS if field != "retryable_statuses"}
    values.update({field: raw[field] for field in OPTIONAL if field in raw})
    return RateLimitPolicy(retryable_statuses=tuple(statuses), **values)


def load_rate_limits(path: Path | None = None) -> RateLimitConfig:
    """Return the configuration at *path*, or the committed one, or refuse."""
    source = RATE_LIMITS_PATH if path is None else path
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as failure:
        raise RateLimitConfigError(f"cannot read the rate-limit file {source}") from failure
    try:
        document = json.loads(text)
    except json.JSONDecodeError as failure:
        raise RateLimitConfigError(f"{source} is not valid JSON") from failure
    section = _section(document)
    version = section.get("version")
    if type(version) is not str:
        raise RateLimitConfigError('rate_limits.version must be a string such as "1.00"')
    services = section.get("services")
    if not isinstance(services, dict) or "default" not in services:
        raise RateLimitConfigError("rate_limits.services must name a `default` policy")
    policies = {name: _policy(name, raw) for name, raw in services.items()}
    return RateLimitConfig(version, policies.pop("default"), policies)
