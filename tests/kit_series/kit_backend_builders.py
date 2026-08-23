"""One role backend, built from this repository's own role and nothing else."""

from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_backend_settlement import BackendSettlement
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.infra.clock import SystemClock
from mars777_police.kit_backend import KitRoleBackend
from mars777_police.protocol.secure_nonce import SecretsNonceSource

TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}


def backend(first: KitRole) -> KitRoleBackend:
    """This repository's backend, scheduled from *first*. It never changes role."""
    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    role = KitRole(ROLE.value)
    return KitRoleBackend(
        context=KitSessionContext("MaRs-777", role, PeerPayload(TERMS), 1, friendly=friendly),
        friendly=friendly,
        transport=None,  # type: ignore[arg-type]
        settled=None,  # type: ignore[arg-type]
        config=config(),
        role=ROLE,
        strategy=None,  # type: ignore[arg-type]
        model=default_scent_model(),
        nonces=SecretsNonceSource(),
        clock=SystemClock(),
        codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1,
        deadline=5.0,
        first_role=first,
        settlement=BackendSettlement(contribute=collect, series_rows=nothing),
    )


ROWS: list[dict[str, object]] = []
"""Every finished row the builder's backends contributed, in the order they did."""


async def collect(row: dict[str, object]) -> None:
    """Take a finished row, so a test can see what a played sub-game settled as."""
    ROWS.append(row)


async def nothing() -> tuple[dict[str, object], ...]:
    """No assembled series: these fixtures play rows, they do not settle them."""
    return ()


async def drop(message: object) -> None:
    """A send that goes nowhere, for a test about what is never sealed."""
