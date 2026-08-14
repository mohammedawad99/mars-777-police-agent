"""Real fixtures for the turn runtime: real board, real truth, real service.

There is no legality shortcut here and no sentinel hint. Legality comes from
`LocalTurnService` against `domain.rules`, so a test that says "illegal" is
asserting the game's own answer rather than a fixture's opinion: the square
south of the agent is genuinely blocked, which is why moving south is refused.
"""

from mars777_police.app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_runtime import TurnProtocolRuntime
from mars777_police.app.turn_service import LocalTurnService, TurnLimits
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.domain.truth import LocalTruth

PEER_DIGEST = Sha256Digest("a" * 64)
OTHER_DIGEST = Sha256Digest("b" * 64)
OUR_DIGEST = Sha256Digest("c" * 64)
START = TurnCursor(1, 1)
GRID = 10
CENTRE = Position(5, 5)
BLOCKED = Position(6, 5)


def board() -> Board:
    """An empty grid except for the one square that makes `S` genuinely illegal."""
    return Board(rows=GRID, cols=GRID, blocked=frozenset({BLOCKED}))


def truth() -> LocalTruth:
    """Own position at the centre, with room to move north."""
    return LocalTruth(board=board(), own_position=CENTRE, completed_steps=0)


def service() -> LocalTurnService:
    """The real local turn service, with limits generous enough not to confound."""
    return LocalTurnService(
        limits=TurnLimits(max_moves=35, survival_threshold=35),
        quota=BarrierQuota(max_barriers=14),
    )


def runtime(role: ActorRole = ActorRole.POLICE) -> TurnProtocolRuntime:
    """The production runtime over real collaborators."""
    return TurnProtocolRuntime(role=role, turns=service(), truth=truth(), cursor=START)


def commitment(cursor: TurnCursor = START, digest: Sha256Digest = PEER_DIGEST) -> Commitment:
    return Commitment(cursor, digest)


def acknowledgement(
    cursor: TurnCursor = START, digest: Sha256Digest = OUR_DIGEST
) -> Acknowledgement:
    return Acknowledgement(cursor, digest)


def emission(cell: Position | None = None) -> ScentEmission:
    """What the agreed model really deposits around *cell* - never a fixture."""
    model = default_scent_model()
    return emission_of(board(), model.kernel, cell or CENTRE, model.params)


def legal_reveal(cursor: TurnCursor = START) -> Reveal:
    """A move the real rules accept: north, onto an empty square."""
    return Reveal(cursor, MoveAction(Move.N), "heading north", None, emission())


def illegal_reveal(cursor: TurnCursor = START) -> Reveal:
    """A move the real rules refuse: south, into the blocked square."""
    return Reveal(cursor, MoveAction(Move.S), "heading south", None, emission())


def advanced(runtime_under_test: TurnProtocolRuntime) -> TurnProtocolRuntime:
    """Drive the frozen cadence up to the point a reveal is expected."""
    runtime_under_test.accept_commitment(commitment())
    runtime_under_test.acknowledge()
    return runtime_under_test
