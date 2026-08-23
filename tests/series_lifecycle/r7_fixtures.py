"""Fixtures that describe a series *after* it happened, or a variant of it.

They live apart from `r7_builders` because that module builds the live graph;
these build the values a completed - or deliberately incomplete - series shows.
"""

import composed_builders as compose
from r7_builders import CONFIG

from mars777_police.app.declaration_values import Declaration
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.result_core_runtime import participants_of
from mars777_police.app.series_roles import SeriesRoleAssignment, alternating
from mars777_police.series_runtime import SeriesRuntime


def test_roles(declaration: Declaration, group_id: str) -> SeriesRoleAssignment:
    """TEST-ONLY series authority, stated explicitly rather than inferred.

    Production reads the agreed pairing and refuses when it cannot; a synthetic
    fixture has no agreement to read, so it declares one here. Keeping the
    convenience on this side is what lets production stay fail-closed.
    """
    participants = participants_of(declaration)
    other = participants.group_b if participants.group_a == group_id else participants.group_a
    return alternating(group_id, KitRole.POLICE, other)


def merged_declaration() -> object:
    """A real merged declaration, exactly as Step-0 leaves it."""
    composition = compose.after_step0(compose.compose())
    return composition.pregame.declaration


def partial_declaration() -> object:
    """Our own half, before the peer's Step-0 has merged into it."""
    return compose.compose().identity.declaration


def cumulative_reference(lines: object) -> object:
    """The totals a reader would add up by hand, for the derivation to match."""
    from mars777_police.app.result_core_values import CumulativeResult

    cop = sum(line.cop_score for line in lines)  # type: ignore[attr-defined]
    thief = sum(line.thief_score for line in lines)  # type: ignore[attr-defined]
    outcome = "tie" if cop == thief else ("cop" if cop > thief else "thief")
    return CumulativeResult(cop, thief, outcome)


def declaration_round_trip(declaration: object) -> bool:
    """Whether the written declaration decodes back to the same semantic value."""
    from mars777_police.artifact_documents import declaration_document
    from mars777_police.transport.codec_declaration import decode_declaration
    from mars777_police.transport.wire_declaration import DeclarationWire

    document = declaration_document(declaration)  # type: ignore[arg-type]
    return decode_declaration(DeclarationWire.model_validate(document)) == declaration


def other_config() -> object:
    """A different but valid config - not the one this round locked.

    It varies the board size rather than `schema_version`: since Stage 9A-1B1F a
    configuration at an unsupported schema version is not a representable value,
    so that member can no longer stand in for "different but valid".
    """
    import dataclasses

    original = CONFIG.board_and_agents
    board = dataclasses.replace(original, grid_size=original.grid_size + 1)
    return dataclasses.replace(CONFIG, board_and_agents=board)


def unagreed_result(series: SeriesRuntime) -> object:
    """A real ResultExchange whose agreement never completed."""
    from mars777_police.app.series_record import contribution_of, cumulative_of, links_of

    composition = series.composition
    declared = composition.pregame.declaration
    roles = test_roles(declared, composition.group_id)
    return composition.complete_result(
        lines=series.lines,
        links=links_of(declared),
        cumulative=cumulative_of(series.lines),
        own=contribution_of(declared, composition.group_id, series.lines, series.tokens, roles),
        roles=roles,
    )
