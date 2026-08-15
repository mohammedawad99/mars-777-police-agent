"""What every strategy behind the seam must be, whatever it decides.

These are the role-neutral obligations: the port exists and offers exactly one
operation, the baseline satisfies it structurally, the answer is one of the
domain's own physical actions, and the observation handed in comes back
untouched. A policy that failed any of these could not be swapped for another
without the game owner noticing, which is the whole point of having a seam.
"""

import dataclasses
import inspect

from strategy_builders import CENTRE, seen

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.strategy_api import StrategyPort
from mars777_police.domain.actions import BarrierAction, MoveAction, PhysicalAction
from mars777_police.domain.observation import Observation


def test_the_port_offers_exactly_one_operation() -> None:
    operations = [
        name
        for name, _ in inspect.getmembers(StrategyPort, inspect.isfunction)
        if not name.startswith("_")
    ]
    assert operations == ["choose_action"]


def test_the_port_takes_an_observation_and_returns_a_physical_action() -> None:
    signature = inspect.signature(StrategyPort.choose_action)
    assert list(signature.parameters) == ["self", "observation"]
    hints = inspect.get_annotations(StrategyPort.choose_action, eval_str=True)
    assert hints["observation"] is Observation
    assert hints["return"] is PhysicalAction


def test_the_baseline_satisfies_the_port_structurally() -> None:
    port = inspect.signature(StrategyPort.choose_action)
    concrete = inspect.signature(BaselineStrategy.choose_action)
    assert list(concrete.parameters) == list(port.parameters)
    returned = inspect.get_annotations(BaselineStrategy.choose_action, eval_str=True)["return"]
    assert returned in (PhysicalAction, MoveAction, BarrierAction)


def test_choosing_returns_one_of_the_domains_own_physical_actions() -> None:
    action = BaselineStrategy().choose_action(seen(CENTRE))
    assert isinstance(action, MoveAction | BarrierAction)


def test_the_observation_handed_in_is_returned_unchanged() -> None:
    observation = seen(CENTRE, CENTRE.__class__(2, 2))
    before = (observation.board, observation.own_position, observation.quota)
    BaselineStrategy().choose_action(observation)
    assert (observation.board, observation.own_position, observation.quota) == before
    assert observation.board.blocked == frozenset({CENTRE.__class__(2, 2)})


def test_the_strategy_carries_no_state_between_decisions() -> None:
    strategy = BaselineStrategy()
    assert dataclasses.fields(strategy) == ()
    assert not hasattr(strategy, "__dict__")


def test_two_independently_built_strategies_decide_alike() -> None:
    observation = seen(CENTRE, CENTRE.__class__(1, 1))
    assert BaselineStrategy().choose_action(observation) == BaselineStrategy().choose_action(
        observation
    )
