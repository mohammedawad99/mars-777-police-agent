"""Where the strategy is forbidden to reach, asserted against its own code.

A strategy that could open a socket, read the final audit or re-derive board
geometry would be a second game engine wearing a policy's name. These guards
read the modules' *code* - literals and comments stripped by `r16_source` - so a
docstring explaining why a boundary exists never trips the guard that enforces
it.

The legality guard is the sharpest one: `baseline_strategy` may **call** the
rules, but the moment it contains a bound, a blocked-cell test or a coordinate
delta of its own, there are two legality authorities and one of them is wrong.
"""

import inspect

from r16_source import imports_of, tokens_of

from mars777_police.app import baseline_strategy, strategy_api
from mars777_police.domain import observation, reachability

STRATEGY = (observation, reachability, strategy_api, baseline_strategy)

OUTWARD = ("protocol", "transport", "infra", "fastmcp", "mcp", "httpx", "socket", "asyncio")
MODELS = ("anthropic", "openai", "google", "ollama", "gemini", "llm", "requests")
TRUTH = ("semantic_replay", "audit_runtime", "outbound_evidence_runtime", "audit_scent")


def test_no_strategy_module_reaches_outward_to_a_boundary() -> None:
    for module in STRATEGY:
        for imported in imports_of(module):
            head = imported.lstrip(".").split(".")[0].lower()
            assert head not in OUTWARD
            assert head not in MODELS


def test_no_strategy_module_imports_a_language_model_or_randomness() -> None:
    for module in STRATEGY:
        assert "random" not in imports_of(module)
        assert tokens_of(module).isdisjoint({"random", "seed", "shuffle", "choice", "uniform"})


def test_no_strategy_module_can_see_post_game_or_peer_evidence() -> None:
    for module in STRATEGY:
        code = tokens_of(module)
        for forbidden in TRUTH:
            assert forbidden not in code
        assert code.isdisjoint({"Replay", "PlayedTurn", "AuditRuntime", "Reveal", "nonce"})


def test_no_strategy_module_names_an_opponent_at_all() -> None:
    for module in STRATEGY:
        code = {token.lower() for token in tokens_of(module)}
        assert code.isdisjoint(
            {"opponent", "enemy", "peer", "thief", "police", "belief", "scent", "hint"}
        )


def test_the_policy_re_implements_no_part_of_game_legality() -> None:
    code = tokens_of(baseline_strategy)
    assert code.isdisjoint(
        {
            "rows",
            "cols",
            "blocked",
            "is_blocked",
            "contains",
            "is_traversable",
            "orthogonal_neighbours",
            "ORTHOGONAL_OFFSETS",
            "is_legal_move",
            "is_placeable",
            "is_adjacent_or_same",
            "place_barrier",
            "apply_move",
            "delta_of",
            "row",
            "col",
        }
    )


def test_the_policy_enumerates_only_through_the_rules_authority() -> None:
    assert "legal_moves" in tokens_of(baseline_strategy)


def test_reachability_carries_no_geometry_of_its_own() -> None:
    code = tokens_of(reachability)
    assert code.isdisjoint({"row", "col", "abs", "ORTHOGONAL_OFFSETS", "delta_of", "_DELTAS"})
    assert {"orthogonal_neighbours", "is_traversable"} <= code


def test_the_observation_wall_reaches_no_further_than_the_domain() -> None:
    for imported in imports_of(observation):
        assert imported.startswith(".") or imported == "dataclasses"


def test_every_new_strategy_module_stays_within_the_line_budget() -> None:
    for module in STRATEGY:
        assert len(inspect.getsource(module).splitlines()) <= 150
