"""The second sealed holdout: fixed before a v2 candidate existed, and blind.

The first holdout is **spent** - a frozen candidate was evaluated against it
exactly once and the one-shot result is committed. A consumed holdout does not
become blind again by being reused, so a second promotion cycle needs a second
sealed set rather than a second look at the first.

These tests exist to make "sealed first" checkable rather than asserted, and to
pin the one thing a fresh namespace does *not* give you for free: blindness.
"""

import json
from pathlib import Path

from research.identity import baseline_identity
from research.sealed import (
    RESULTS_PRESENT_V2,
    SEALED_AT_V2,
    carried_over,
    sealed_document_v2,
    sealed_set,
    sealed_set_v2,
)
from research.seeds import (
    FINAL_HOLDOUT_V2,
    SEALED_NAMESPACE,
    SEALED_NAMESPACE_V2,
    disjoint,
    final_holdout_bank,
    final_holdout_v2_bank,
    working_banks,
)

MANIFEST = Path(__file__).resolve().parents[2] / "results/final_holdout_v2.json"
COMMITMENT = "5bf90845113384c6364d24f9216a0e74f01986ab74b9b4c7f5dd2b0ffe72a787"
SEEDS = "34bddb9b9c24e387d73e40439ca0ba7a946957654860384f630f5d0a2a826ae1"


def role() -> str:
    return baseline_identity().role


def test_the_committed_manifest_is_reproduced_exactly() -> None:
    """Anyone may recompute it; nobody may quietly change what will be judged."""
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == sealed_document_v2(role())


def test_the_commitment_and_seed_digests_are_the_recorded_ones() -> None:
    document = sealed_document_v2(role())
    assert document["commitment_sha256"] == COMMITMENT
    assert document["seed_sha256"] == SEEDS


def test_no_v2_outcome_exists_yet() -> None:
    """Sealed means unopened. A result file appearing is what consumption looks like."""
    assert RESULTS_PRESENT_V2 is False
    assert sealed_document_v2(role())["results_present"] is False


def test_the_seal_records_the_stage_that_fixed_it() -> None:
    assert SEALED_AT_V2 == "stage-E-0"
    assert sealed_document_v2(role())["sealed_at"] == "stage-E-0"


def test_the_v2_bank_has_its_own_namespace() -> None:
    assert SEALED_NAMESPACE_V2 != SEALED_NAMESPACE
    assert sealed_document_v2(role())["namespace"] == SEALED_NAMESPACE_V2
    assert sealed_document_v2(role())["bank"] == FINAL_HOLDOUT_V2


def test_the_v2_bank_shares_no_seed_with_any_other_bank() -> None:
    v2 = final_holdout_v2_bank()
    assert disjoint(v2, final_holdout_bank())
    for working in working_banks():
        assert disjoint(v2, working)


def test_the_v2_set_shares_no_scenario_with_the_spent_v1_set() -> None:
    """A fresh namespace is not automatically a blind set.

    `scenario_id` covers the family, the configuration and both opening cells, so
    a configuration with a finite legal opening space produces the same scenarios
    however the seeds are drawn. Enumerating from a new namespace still
    reproduced scenarios v1 had already played; they are excluded.
    """
    assert not set(sealed_set_v2(role()).scenarios) & set(sealed_set(role()).scenarios)


def test_the_exclusion_actually_removed_something_and_says_how_much() -> None:
    """If this ever reads zero, the collision is gone and the claim is still true."""
    assert carried_over(role()) == 66
    assert sealed_document_v2(role())["excluded_as_already_played"] == 66


def test_the_recorded_count_is_the_count_after_exclusion() -> None:
    document = sealed_document_v2(role())
    assert document["count"] == len(sealed_set_v2(role()).scenarios) == 2181


def test_every_scenario_is_named_once() -> None:
    scenarios = sealed_set_v2(role()).scenarios
    assert len(set(scenarios)) == len(scenarios)


def test_the_seal_names_the_set_it_replaces() -> None:
    assert sealed_document_v2(role())["supersedes"] == "final_holdout"


def test_enumerating_the_set_plays_nothing() -> None:
    """The module names conditions; it builds no strategy and scores nothing.

    Read from the parsed module rather than from its text: the docstrings here
    discuss playing and scoring at length, and a substring scan would convict
    the explanation of being the thing it explains.
    """
    import ast
    import inspect

    from research import sealed

    tree = ast.parse(inspect.getsource(sealed))
    imported = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {"game", "runner", "strategy_port", "records"} & {
        one.lstrip(".").split(".")[-1] for one in imported
    }
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert not called & {"play", "play_game", "score_for", "run", "choose_action"}
