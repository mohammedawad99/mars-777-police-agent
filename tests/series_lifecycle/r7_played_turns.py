"""Whole turns, played through the production runners rather than assembled.

These drive a real exchange to completion - including the deliberately
unvalidated variant, which exists so a test can reach the states a validating
path would have refused.
"""

import dataclasses

from r7_turn_builders import board, moved
from r16_builders import config

from mars777_police.app.capture_values import CaptureClaim, TurnOutcome
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction, PhysicalAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.config_model import GridConfig, InvalidScentError
from mars777_police.domain.config_sections import BoardAndAgentsTerms
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_observation import emission_of
from mars777_police.domain.truth import LocalTruth
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.series_runtime import SeriesRuntime

CONFIG = dataclasses.replace(
    config(),
    board_and_agents=BoardAndAgentsTerms(7, 2, Position(0, 0), Position(0, 1), "top-left", 0),
)
"""The locked config for a lifecycle run: the two start cells are neighbours.

Adjacency is what makes the capture routes reachable at all - BAR-004 lets the
police place only on its own cell or one beside it, so a thief that starts four
cells away cannot be captured by a barrier in the first turn of a sub-game."""
DIGEST = Sha256Digest(config_sha256(CONFIG).value)
POSITIONS = {
    ActorRole.POLICE: CONFIG.board_and_agents.cop_start,
    ActorRole.THIEF: CONFIG.board_and_agents.thief_start,
}
"""Where each side really starts - the cells this series' config locked.

The final audit replays the disclosed game against them, so a lifecycle fixture
that opened somewhere else would be disclosing a game that never happened."""
ACTIONS = {ActorRole.POLICE: MoveAction(Move.S), ActorRole.THIEF: MoveAction(Move.E)}
"""One legal opening move each, from the corner cells the config locks."""
HINT = "heading north"


def own_truth(cell: Position, walls: tuple[Position, ...]) -> LocalTruth:
    """This side's own truth after the steps it has actually played.

    The harness carries it because nothing in production does yet: an agent that
    adopts a turn's result is the game owner a later checkpoint will build. Until
    then a caller playing more than one step has to hand the next turn the cell
    and the barriers its own earlier actions produced, or the sender would
    validate this step against where it started.
    """
    terms = CONFIG.board_and_agents
    empty = GridConfig.from_grid_size(terms.grid_size, terms.axis_start_index).to_board()
    return LocalTruth(
        board=Board(rows=empty.rows, cols=empty.cols, blocked=frozenset(walls)),
        own_position=cell,
    )


async def one_turn(
    mover: SeriesRuntime,
    waiter: SeriesRuntime,
    role: ActorRole,
    cursor: TurnCursor,
    action: PhysicalAction | None = None,
    claim: CaptureClaim | None = None,
    cell: Position | None = None,
    barriers: tuple[Position, ...] = (),
) -> TurnOutcome:
    """Drive one real commit / acknowledge / reveal turn between two agents.

    *cell* and *barriers* are what this side seals about itself, so a caller
    playing more than one step has to carry the real ones forward - the final
    audit replays them against the placements both sides actually revealed.
    """
    prepared = await mover.composition.peer_runner.open_turn(
        state=SealedState(DIGEST, cell or POSITIONS[role], barriers, cursor.step, role),
        action=action or ACTIONS[role],
        intent=Intent.TRUTH,
        hint=HINT,
        cursor=cursor,
        claim=claim,
    )
    await waiter.composition.peer_runner.acknowledge_peer_turn()
    return await mover.composition.peer_runner.reveal_turn(prepared)


async def one_unvalidated_turn(
    mover: SeriesRuntime,
    waiter: SeriesRuntime,
    role: ActorRole,
    cursor: TurnCursor,
    action: PhysicalAction,
    cell: Position | None = None,
    barriers: tuple[Position, ...] = (),
) -> TurnOutcome:
    """One turn from a peer that does **not** validate its own action first.

    `PeerRunner.open_turn` projects this turn's scent before it seals anything,
    so an agent running the production path can no longer send an action its own
    rules refuse - which is the point of that guard. A misbehaving opponent is
    still possible, and the semantic audit exists for exactly that peer, so this
    harness reaches past the runner: it seals through the real evidence owner,
    registers and sends the real commitment, and reveals over the real transport
    with the emission its **post-action** cell produces.

    Bypassing the sender's legality guard is the whole point of this harness; it
    must not also inject a physical scent lie, or every scenario driven through
    it would carry `DISHONEST_SCENT_EMISSION` on top of what it meant to test.
    `moved` gives the same post-action cell the real projector would use.
    """
    composition = mover.composition
    model = composition.pregame.lock.scent_model
    source = cell or POSITIONS[role]
    try:
        emission = emission_of(board(), model.kernel, moved(source, action), model.params)
    except InvalidScentError:
        # An illegal move reaches no lawful cell, so it has no post-action
        # emission; the audit reports the illegality first either way.
        emission = emission_of(board(), model.kernel, source, model.params)
    prepared = composition.runtime_context.current_evidence().prepare_turn(
        state=SealedState(DIGEST, source, barriers, cursor.step, role),
        action=action,
        intent=Intent.TRUTH,
        hint=HINT,
        cursor=cursor,
        scent=emission,
    )
    composition.runtime_context.current_turn().register_local_commitment(prepared.commitment)
    await composition.peer_transport.send_commitment(prepared.commitment)
    await waiter.composition.peer_runner.acknowledge_peer_turn()
    return await composition.peer_runner.reveal_turn(prepared)
