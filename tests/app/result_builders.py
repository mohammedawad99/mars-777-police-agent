"""Shared builders for the result semantic-value tests."""

from mars777_police.app.artifact_values import GitCommitSha, UtcTimestamp
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry

COMMIT_A = "2113e68d141ab087b849f83a7d91d66620e8ad85"
COMMIT_B = "0000000000000000000000000000000000000000"
GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
DECLARATION_REF = f"declaration_{GAME_ID}.json"
STAMP = "2026-08-07T01:00:00Z"


def entry(sub_game: int = 1, commit: str = COMMIT_A, tokens: int = 0) -> ResultContributionEntry:
    return ResultContributionEntry(sub_game, GitCommitSha(commit), tokens)


def entries(commit: str = COMMIT_A) -> tuple[ResultContributionEntry, ...]:
    return tuple(entry(i, commit, i * 10) for i in range(1, 7))


def contribution(**over: object) -> ResultContribution:
    fields: dict[str, object] = {"group_id": "MaRs-777", "entries": entries()}
    fields.update(over)
    return ResultContribution(**fields)  # type: ignore[arg-type]


def agreement(**over: object) -> ResultAgreement:
    fields: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": "uid0001",
        "declaration_ref": DECLARATION_REF,
        "timestamp": UtcTimestamp(STAMP),
        "contribution": contribution(),
    }
    fields.update(over)
    return ResultAgreement(**fields)  # type: ignore[arg-type]
