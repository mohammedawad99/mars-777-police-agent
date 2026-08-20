"""Reading a persisted official log back into typed values, strictly.

This is the inverse of `log_document.finalized_log` and nothing more: it parses,
it refuses, and it invents no field. A viewer reads files somebody else may have
written, so every shape that is not a log ends in a `ReplayError` naming what
failed rather than in a traceback.

**No verdict is formed here.** Legality, trajectory and digests all belong to
authorities that already exist; this module only makes their inputs available.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from .replay_values import ReplayError

PHASES: Final[frozenset[str]] = frozenset({"commit", "ack", "reveal"})
TOP: Final[tuple[str, ...]] = ("game_id", "game_uid", "sub_game", "config_sha256", "entries")


@dataclass(frozen=True, slots=True)
class ReplayLog:
    """One sub-game's official log, exactly as it was written."""

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: str
    entries: tuple[Mapping[str, object], ...]
    nonces: dict[tuple[int, str], str]
    result: str
    tampered_step: int | None
    semantic: Mapping[str, object]

    def phase(self, name: str) -> tuple[Mapping[str, object], ...]:
        """Every entry of one phase, in the order the log recorded them."""
        return tuple(entry for entry in self.entries if entry.get("phase") == name)


def _text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if type(value) is not str or not value:
        raise ReplayError(f"the log field {field!r} is missing or is not text")
    return value


def _entries(raw: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        raise ReplayError("the log field 'entries' must be a list")
    parsed: list[Mapping[str, object]] = []
    for entry in raw:
        if not isinstance(entry, Mapping) or "phase" not in entry:
            raise ReplayError("a log entry has no 'phase'")
        phase = entry["phase"]
        if phase not in PHASES:
            raise ReplayError(f"a log entry has the unknown phase {phase!r}")
        if phase == "commit" and not isinstance(entry.get("state"), Mapping):
            raise ReplayError("a commit entry has no sealed 'state'")
        if phase == "commit" and type(entry.get("commit")) is not str:
            raise ReplayError("a commit entry has no 'commit' digest to check")
        parsed.append(entry)
    return tuple(parsed)


def _nonces(audit: Mapping[str, object]) -> dict[tuple[int, str], str]:
    """Every disclosed nonce, keyed by `(step, role)` as the log itself writes it.

    **Keyed by both, because a lockstep step has two of them.** `final_reveal`
    carries our own nonces and the peer's, each labelled with its role; a map
    keyed by step alone would let the second entry overwrite the first, and every
    commitment of the losing role would then be recomputed with somebody else's
    nonce and reported as `TAMPERED`. A false accusation is the one outcome this
    viewer must never produce.
    """
    disclosed = audit.get("final_reveal", ())
    if not isinstance(disclosed, Sequence) or isinstance(disclosed, str | bytes):
        raise ReplayError("the audit block's 'final_reveal' must be a list")
    found: dict[tuple[int, str], str] = {}
    for entry in disclosed:
        if isinstance(entry, Mapping) and type(entry.get("step")) is int:
            nonce, role = entry.get("nonce"), entry.get("role")
            if type(nonce) is str and type(role) is str:
                found[(entry["step"], role)] = nonce
    return found


def read_log(document: object) -> ReplayLog:
    """Return the log *document* describes, or refuse it with a reason."""
    if not isinstance(document, Mapping):
        raise ReplayError("this file is not a log document")
    if "evidence_class" in document:
        raise ReplayError(
            "this is development evidence, not an official log: a friendly"
            " contribution carries settled facts only and deliberately holds no"
            " board, position, barrier set or nonce, so it cannot be replayed"
        )
    for field in TOP:
        if field not in document:
            raise ReplayError(f"the log field {field!r} is missing")
    if type(document["sub_game"]) is not int:
        raise ReplayError("the log field 'sub_game' must be a whole number")
    audit = document.get("audit")
    if not isinstance(audit, Mapping):
        raise ReplayError("the log has no 'audit' block")
    semantic = audit.get("semantic")
    if not isinstance(semantic, Mapping):
        raise ReplayError("the audit block has no 'semantic' finding")
    tampered = audit.get("tampered_step")
    if tampered is not None and type(tampered) is not int:
        raise ReplayError("the audit block's 'tampered_step' must be a step or nothing")
    return ReplayLog(
        game_id=_text(document, "game_id"),
        game_uid=_text(document, "game_uid"),
        sub_game=document["sub_game"],
        config_sha256=_text(document, "config_sha256"),
        entries=_entries(document["entries"]),
        nonces=_nonces(audit),
        result=str(audit.get("result", "")),
        tampered_step=tampered,
        semantic=semantic,
    )
