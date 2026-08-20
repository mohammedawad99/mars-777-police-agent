"""Walking a finished sub-game step by step, over the authorities that own it.

The viewer replays; it does not judge. Trajectory and legality come from
`semantic_replay.Replay`, which is the same engine the live audit used, and the
digest comes from the commitment port. What this module adds is the thing a
grader needs and neither of those provides: an ordered, deterministic sequence
of whole steps, each projected into values that are safe to show.

**Deterministic by construction.** The sequence is derived once from the log's
own commit entries in step order; navigating cannot re-simulate anything,
because there is nothing left to simulate.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from ..domain.actions import PhysicalAction
from .ports import CommitmentPort
from .replay_crypto import barriers_of, check_commit, sealed_state
from .replay_log import ReplayLog
from .replay_status import worst_check
from .replay_values import ReplayError, ReplayStep, ReplaySummary, ReplayTurn
from .sealed_record_values import ActorRole
from .semantic_replay import PlayedTurn, Replay
from .semantic_values import SemanticRules

Decoder = Callable[[object], PhysicalAction]


@dataclass(slots=True)
class ReplaySession:
    """One sub-game, replayed once and then navigable without re-running."""

    log: ReplayLog
    rules: SemanticRules
    commitments: CommitmentPort
    decode: Decoder
    evidence_class: str = "OFFICIAL"
    notes: tuple[str, ...] = ()
    steps: tuple[ReplayStep, ...] = field(init=False, default=())
    cursor: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.steps = tuple(self._build())

    def _grouped(self) -> dict[int, list[Mapping[str, object]]]:
        grouped: dict[int, list[Mapping[str, object]]] = {}
        for entry in self.log.phase("commit"):
            step = entry.get("step")
            if type(step) is not int:
                raise ReplayError("a commit entry has no step number")
            grouped.setdefault(step, []).append(entry)
        return grouped

    def _reveal(self, step: int, role: str) -> Mapping[str, object]:
        for entry in self.log.phase("reveal"):
            if entry.get("step") == step and entry.get("role") == role:
                return entry
        return {}

    def _turn(self, entry: Mapping[str, object]) -> tuple[PlayedTurn, ReplayTurn]:
        state = sealed_state(entry, self.log.sub_game)
        action = self.decode(entry["move"])
        walls = barriers_of(entry["state"])  # type: ignore[arg-type]
        played = PlayedTurn(state.step, state.role, state.self_pos, walls, action)
        check = check_commit(entry, action, self.log.nonces, self.commitments, self.log.sub_game)
        revealed = self._reveal(state.step, state.role.value)
        shown = ReplayTurn(
            step=state.step,
            role=state.role.value,
            cell=(state.self_pos.row, state.self_pos.col),
            barriers=tuple((one.row, one.col) for one in walls),
            action=str(entry["move"]),
            hint=_text(revealed.get("hint")),
            intent=_text(entry.get("intent")),
            capture_claim=_text(revealed.get("capture_claim")),
            capture_answer=_text(revealed.get("capture_answer")),
            commitment=_text(entry.get("commit")),
            check=check,
        )
        return played, shown

    def _build(self) -> list[ReplayStep]:
        replay = Replay(self.rules)
        built: list[ReplayStep] = []
        for number in sorted(self._grouped()):
            pairs = [self._turn(entry) for entry in self._grouped()[number]]
            played = tuple(one for one, _ in pairs)
            finding = replay.check(played)
            replay.apply(played)
            built.append(
                ReplayStep(
                    number=number,
                    turns=tuple(shown for _, shown in pairs),
                    police_cell=_cell(replay, ActorRole.POLICE),
                    thief_cell=_cell(replay, ActorRole.THIEF),
                    barriers=tuple(sorted((one.row, one.col) for one in replay.board.blocked)),
                    grid_size=self.rules.board.rows,
                    semantic=finding.verdict.value,
                )
            )
        return built

    def first(self) -> ReplayStep:
        """Go to the first step and return it."""
        return self._at(0)

    def last(self) -> ReplayStep:
        """Go to the final step and return it."""
        return self._at(len(self.steps) - 1)

    def next(self) -> ReplayStep:
        """Advance one step, stopping at the end rather than wrapping."""
        return self._at(min(self.cursor + 1, len(self.steps) - 1))

    def previous(self) -> ReplayStep:
        """Go back one step, stopping at the beginning rather than wrapping."""
        return self._at(max(self.cursor - 1, 0))

    def current(self) -> ReplayStep:
        """The step now being shown."""
        return self._at(self.cursor)

    def _at(self, index: int) -> ReplayStep:
        if not self.steps:
            raise ReplayError("this log records no committed step to replay")
        self.cursor = index
        return self.steps[index]

    def summary(self) -> ReplaySummary:
        """What the whole replay establishes, and what it does not."""
        checks = [turn.check for step in self.steps for turn in step.turns]
        crypto = worst_check(checks)
        semantic = {step.semantic for step in self.steps} - {"CONSISTENT"}
        verdict = sorted(semantic)[0] if semantic else "CONSISTENT"
        recorded = str(self.log.semantic.get("verdict", ""))
        return ReplaySummary(
            game_id=self.log.game_id,
            game_uid=self.log.game_uid,
            sub_game=self.log.sub_game,
            config_sha256=self.log.config_sha256,
            steps=len(self.steps),
            crypto=crypto,
            recorded_result=self.log.result,
            tampered_step=self.log.tampered_step,
            semantic_verdict=verdict,
            outcome_agrees=verdict == recorded,
            evidence_class=self.evidence_class,
            notes=self.notes,
        )


def _cell(replay: Replay, role: ActorRole) -> tuple[int, int]:
    position = replay.cell_of(role)
    return (position.row, position.col)


def _text(value: object) -> str | None:
    return value if type(value) is str else None
