"""`config_sha256`, the authenticated lock context, and the lock adapter.

Four layers, never conflated (`CONFIG_CONTRACT.md` §R12-E / §R12-FIX-L):

1. the **canonical binding bytes** of the 35 core members - content only, mapped
   by `protocol.config_projection`;
2. **`config_sha256`**, an *unkeyed* digest that proves content identity and
   authenticates nobody;
3. the **`AuthProof`** over `"config" ‖ canonical(ConfigLockContext)`, which
   proves a key-holder produced *this* context and therefore binds the game, the
   sub-game, the digest and the eleven series-wide profiles;
4. the local `CONFIG_LOCKED` transition, which has no bytes at all and lives in
   `app.config_lock_runtime`.

The App-B core is **byte-identical across every sub-game of a series**, so a
proof over it alone would bind no sub-game and no game. Hashing it and then
authenticating that digest inside an explicit context is what fixes it without
polluting the physics contract with protocol metadata (**D4**).

`config_sha256` is stored **outside** the bytes it covers, and the envelope is
never inside the bytes it authenticates.
"""

from hashlib import sha256

from ..app.auth_values import AuthProof
from ..app.peer_pregame_messages import ConfigLockContext
from ..app.protocol_values import Sha256Digest
from ..domain.negotiated_config import NegotiatedConfig
from .canonical import canonical_json_bytes
from .config_projection import config_core, profiles_core
from .keyed_auth import CONFIG_CONTEXT, KeyedAuthenticator


def config_sha256(config: NegotiatedConfig) -> Sha256Digest:
    """Return the unkeyed content digest over the canonical config bytes."""
    return Sha256Digest(sha256(canonical_json_bytes(config_core(config))).hexdigest())


def lock_context_core(context: ConfigLockContext) -> dict[str, object]:
    """Return the authenticated lock context - identity, sub-game, digest, profiles."""
    return {
        "game_id": context.game_id,
        "game_uid": context.game_uid,
        "sub_game": context.sub_game,
        "config_sha256": context.config_sha256.value,
        "profiles": profiles_core(context.profiles),
    }


class ConfigLockAuthenticator:
    """The `ConfigDigestPort` and `ConfigLockAuthPort` adapter."""

    def __init__(self, authenticator: KeyedAuthenticator) -> None:
        self._authenticator = authenticator

    def digest(self, config: NegotiatedConfig) -> Sha256Digest:
        """Return `config_sha256`, recomputed locally and never taken from a peer."""
        return config_sha256(config)

    def prove(self, context: ConfigLockContext) -> AuthProof:
        """Return this peer's proof over *context*."""
        return self._authenticator.prove(CONFIG_CONTEXT, lock_context_core(context))

    def verify(self, context: ConfigLockContext, proof: AuthProof) -> bool:
        """Return whether *proof* verifies over *context*."""
        return self._authenticator.verify(CONFIG_CONTEXT, lock_context_core(context), proof)
