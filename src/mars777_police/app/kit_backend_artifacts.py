"""What a role backend owes the group in official documents, once a sub-game ends.

Split from `kit_backend_settlement` for the reason that module was split from
the backend: settling a series, playing a sub-game and recording one are three
jobs that share a process and nothing else. This owns only the third.

**The lock context is rebuilt here, from facts the sub-game already fixed** -
the pairing's identity, this sub-game's number, the digest of the config both
sides loaded, the frozen profile set and the agreed scent model. Nothing is
invented and nothing is defaulted: a silent default is how two peers end up
believing they agreed on different things.

**Silent when unconfigured.** A backend given no profile set contributes
nothing rather than guessing one, and says so by returning `False`. That keeps
every existing development friendly working unchanged while a counted run gets
its documents.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from ..protocol.config_lock import config_sha256
from ..protocol.scent_model import scent_model_sha256
from .interop_profiles import InteropProfileSet
from .kit_artifact_build import sub_game_artifacts
from .kit_greeting import KitGreeting, KitPairing
from .kit_messages import KitAuditReveal, KitRecord
from .official_artifacts import CONFIG, LOG
from .peer_pregame_messages import ConfigLockContext
from .protocol_errors import LocalDefectError

Contribute = Callable[[str, int, dict[str, Any]], Awaitable[None]]


async def unwired(kind: str, sub_game: int, document: dict[str, Any]) -> None:
    """The default sink: a backend wired to no group cannot contribute."""
    raise LocalDefectError(
        f"this backend was never given a group to contribute its {kind} to (sub-game {sub_game})",
    )


@dataclass(slots=True)
class BackendArtifacts:
    """Everything a role backend needs to record one sub-game officially."""

    profiles: InteropProfileSet | None = None
    """The frozen profile set the lock context binds, or `None` for a friendly."""

    config: NegotiatedConfig | None = None
    model: ScentModelAgreement | None = None
    write_config: Any = None
    """The three per-backend constants: what was agreed, and who renders it.

    Held rather than passed per sub-game because they do not vary within a
    series, and a caller repeating them six times is six chances to pass the
    wrong one."""

    contribute: Contribute = field(default=unwired)

    async def record(
        self,
        *,
        pairing: KitPairing,
        sub_game: int,
        greeting: KitGreeting | None,
        ours: tuple[KitRecord, ...],
        disclosure: KitAuditReveal | None,
        peer_verified: bool,
        result: str,
    ) -> bool:
        """Build this sub-game's two official documents and hand them over.

        Returns whether anything was contributed, so a development friendly that
        was never given a profile set stays exactly as it was.
        """
        if self.profiles is None:
            return False
        config, model = self._agreed()
        made = sub_game_artifacts(
            sub_game=sub_game,
            greeting=greeting,
            context=self.context_for(pairing, sub_game, config, model),
            config=config,
            model=model,
            ours=ours,
            disclosure=disclosure,
            peer_verified=peer_verified,
            result=result,
            build_config=self.write_config,
        )
        await self.contribute(CONFIG, sub_game, made.config)
        await self.contribute(LOG, sub_game, made.log)
        return True

    def _agreed(self) -> tuple[NegotiatedConfig, ScentModelAgreement]:
        """The agreed config and model, or a refusal naming the wiring gap."""
        if self.config is None or self.model is None or self.write_config is None:
            raise LocalDefectError(
                "an artifact-recording backend needs the agreed config, model and writer",
            )
        return self.config, self.model

    def context_for(
        self,
        pairing: KitPairing,
        sub_game: int,
        config: NegotiatedConfig,
        model: ScentModelAgreement,
    ) -> ConfigLockContext:
        """The binding this sub-game's documents are recorded under."""
        if self.profiles is None:  # pragma: no cover - `record` returns before this
            raise LocalDefectError("a lock context needs the frozen profile set")
        return ConfigLockContext(
            pairing.game_id,
            pairing.game_uid,
            sub_game,
            config_sha256(config),
            self.profiles,
            scent_model_sha256(model),
        )
