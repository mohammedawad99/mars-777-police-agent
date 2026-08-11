"""The BOOT input boundary: operator environment in, typed immutable values out.

`STATE_OWNERSHIP.md` gives this module two rows and no more - **key material**
("`infra.settings` (env only)", never persisted, PROCESS lifetime, SECRET) and
**local runtime settings** ("infra only", loaded at process start, LOCAL).
`CONFIG_ARCHITECTURE.md` fixes the precedence: secrets are **environment only**,
and a missing required secret refuses the process rather than defaulting.
`STATE_MACHINE.md` makes BOOT's entry condition exactly "settings loaded, key
present", with "abort cleanly" on failure - which is why every refusal below
happens at load time and none of it is deferred.

**Reading the environment stops here.** `DEPENDENCY_RULES.md` D3 injects concrete
values inward, so no `app`, `domain` or `protocol` module ever consults
`os.environ`; they receive already-validated values. There is no global cache,
no singleton and no service locator - `load` returns a frozen value and the
caller owns it.

**The variable names are a project implementation choice, not a source contract.**
No current document freezes an operator vocabulary, and none of these names
crosses the wire, enters a declaration or is negotiated, so a narrow `MARS777_`
prefix (matching the existing live-test switch) introduces no external ambiguity.

**Identity that is already frozen is not an operator input.** `GROUP_CODE` is
fixed in the package and `role` is checked against the role this repository *is*,
so no environment value can boot the Police package as a Thief.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..app.auth_values import KeyId
from ..app.public_endpoint_values import LocalPeerEndpoint, OpponentPublicPeerEndpoint
from ..app.sealed_record_values import ActorRole

ROLE = "MARS777_ROLE"
BIND_HOST = "MARS777_BIND_HOST"
BIND_PORT = "MARS777_BIND_PORT"
OPPONENT_ENDPOINT = "MARS777_OPPONENT_ENDPOINT"
KEY_IDENTIFIER = "MARS777_KEY_ID"
AUTH_SECRET = "MARS777_AUTH_SECRET"


class SettingsError(Exception):
    """A local BOOT refusal: the operator environment cannot start this process.

    Deliberately **not** a `PeerProtocolError`: no peer is involved, nothing
    crosses `ToolError`, and it adds no identity to the frozen error register.
    Its message names the **variable**, never the value, so a malformed secret
    cannot be reconstructed from a stack trace.
    """


@dataclass(frozen=True, slots=True)
class AuthSecret:
    """Pre-shared keyed-auth key material, wrapped so it cannot be printed.

    `repr` and `str` are overridden because a frozen dataclass would otherwise
    render the key into any log line, exception or debugger frame that touched
    the settings object. `reveal()` is the single deliberate escape hatch, used
    once by composition to build the auth provider.
    """

    _value: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self._value) is not bytes or not self._value:
            raise SettingsError(f"{AUTH_SECRET} must be a non-empty value")

    def reveal(self) -> bytes:
        """Return the key material. The only call site should be composition."""
        return self._value

    def __repr__(self) -> str:
        return "AuthSecret(<withheld>)"

    def __str__(self) -> str:
        return "<withheld>"


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Everything BOOT needs from the operator, validated and immutable.

    Deliberately absent: `game_id`/`game_uid` (series identity, established at
    Step-0, not a process input), anything owned by `NegotiatedConfig` (a
    post-lock timeout must never be operator-overridable), and our **own public
    endpoint** (discovered from the ingress, never trusted from the environment).
    """

    role: ActorRole
    local: LocalPeerEndpoint
    key_id: KeyId
    secret: AuthSecret = field(repr=False)
    opponent: OpponentPublicPeerEndpoint | None = None


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if value is None or not value.strip():
        raise SettingsError(f"{name} is required and must not be empty")
    return value.strip()


def _port(env: Mapping[str, str]) -> int:
    text = _required(env, BIND_PORT)
    if not text.isdigit():
        raise SettingsError(f"{BIND_PORT} must be a decimal port number")
    return int(text)


def _role(env: Mapping[str, str], expected: ActorRole) -> ActorRole:
    text = _required(env, ROLE)
    try:
        role = ActorRole(text)
    except ValueError:
        raise SettingsError(f"{ROLE} must name a known role") from None
    if role is not expected:
        raise SettingsError(f"{ROLE} contradicts this repository's role")
    return role


def load_runtime_settings(env: Mapping[str, str], *, expected_role: ActorRole) -> RuntimeSettings:
    """Load and validate the operator environment for **this** repository.

    *env* is injected so tests never touch the real process environment, and so
    nothing here is a hidden global. Unknown variables are ignored rather than
    copied: the result carries only what BOOT asked for.
    """
    role = _role(env, expected_role)
    try:
        local = LocalPeerEndpoint(_required(env, BIND_HOST), _port(env))
        key_id = KeyId(_required(env, KEY_IDENTIFIER))
    except SettingsError:
        raise
    except Exception:
        raise SettingsError(f"{BIND_HOST}/{BIND_PORT}/{KEY_IDENTIFIER} are not valid") from None
    advertised = env.get(OPPONENT_ENDPOINT)
    opponent = (
        OpponentPublicPeerEndpoint(advertised.strip())
        if advertised is not None and advertised.strip()
        else None
    )
    return RuntimeSettings(
        role, local, key_id, AuthSecret(_required(env, AUTH_SECRET).encode()), opponent
    )
