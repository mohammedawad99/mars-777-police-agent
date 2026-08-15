"""Stage 6B built the strategy seam; this is where production finally uses it.

The point of the port was substitutability, so what is asserted here is that the
composition hands out something satisfying `StrategyPort` and that the driver
accepts that contract rather than the concrete baseline. Wiring the class
directly is deliberate: App F Table 22 calls the dotted-path plug-in table *"a
reference table only"*, so a loader has nothing to choose between yet.
"""

import dataclasses
import inspect

import composed_builders as build

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.strategy_api import StrategyPort
from mars777_police.app.sub_game_driver import SubGameDriver
from mars777_police.composition_values import AgentComposition


def test_the_composition_exposes_a_strategy() -> None:
    assert "strategy" in {field.name for field in dataclasses.fields(AgentComposition)}


def test_composing_an_agent_wires_the_repositorys_baseline() -> None:
    composition = build.compose()
    assert isinstance(composition.strategy, BaselineStrategy)


def test_the_wired_strategy_satisfies_the_port() -> None:
    composition = build.compose()
    port = inspect.signature(StrategyPort.choose_action)
    concrete = inspect.signature(type(composition.strategy).choose_action)
    assert list(concrete.parameters) == list(port.parameters)


def test_the_driver_depends_on_the_port_not_the_concrete_baseline() -> None:
    annotations = inspect.get_annotations(SubGameDriver, eval_str=False)
    assert annotations["strategy"] == "StrategyPort"


def test_no_plugin_loader_was_added() -> None:
    from mars777_police import composition

    source = inspect.getsource(composition)
    for forbidden in ("import_module", "entry_points", "importlib", "getattr("):
        assert forbidden not in source


def test_the_documented_port_register_is_still_twenty_one() -> None:
    from pathlib import Path

    register = Path("docs/architecture/API_BOUNDARIES.md").read_text(encoding="utf-8")
    assert "**21 ports** are registered here" in register


def test_two_composed_agents_hold_independent_strategies() -> None:
    a, b = build.both("https://a.example/mcp", "https://b.example/mcp")
    assert a.strategy is not b.strategy
