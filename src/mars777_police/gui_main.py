"""`python -m mars777_police.gui_main` - the graphical viewer, live or replayed.

Two things an operator or a grader can do with a picture: watch this agent play,
or step through a finished sub-game and see its verification. Both are read-only.

    uv run python -m mars777_police.gui_main replay --log g01.json --config c.json
    uv run python -m mars777_police.gui_main replay --log g01.json --config c.json --png out.png
    uv run python -m mars777_police.gui_main live --launch launch.json

**`--png` is the same picture without a screen.** It renders the frame the window
would have drawn and writes it, so the graphical output can be produced where no
display exists - on CI, over a plain shell, or for the submission screenshots.

**Live is a spectator.** The series runs on its own thread through the ordinary
facade; the window polls a one-slot box and never calls back. Closing the window,
or never opening one, changes nothing about the match. Exit status follows the
replay viewer's: `0` verified and complete, `2` unreadable, `3` a finding, `4`
an incomplete audit.

An interpreter without `tkinter` - which Debian and Ubuntu package separately -
is also a `2`, printed as a sentence naming what to install and pointing at
`--png`, which needs no toolkit at all.
"""

import argparse
import asyncio
import sys
import threading
from pathlib import Path

from .app.live_view_sink import LatestSnapshot
from .gui.image_renderer import write_png
from .gui.replay_app import frame_for
from .gui.toolkit import ToolkitMissingError
from .identity import ROLE
from .replay_main import report
from .sdk import AgentSdk, ReplayError, StrictSeriesRequest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line. This opens no file and no window."""
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}.gui_main")
    modes = parser.add_subparsers(dest="mode", required=True)
    replay = modes.add_parser("replay", help="step through a finished sub-game")
    replay.add_argument("--log", required=True, type=Path, help="an official sub-game log")
    replay.add_argument("--config", required=True, type=Path, help="the config artifact it names")
    replay.add_argument("--root", type=Path, help="an evidence root every path must stay inside")
    replay.add_argument("--step", type=int, help="which step to draw (default: the first)")
    replay.add_argument("--png", type=Path, help="write the picture here instead of opening it")
    live = modes.add_parser("live", help="watch this agent play a counted series")
    live.add_argument("--launch", required=True, type=Path, help="this side's launch document")
    return parser.parse_args(argv)


def run_replay(arguments: argparse.Namespace) -> int:
    """Draw one finished sub-game, to a window or to a file, then report its verdict."""
    session = AgentSdk().open_replay(arguments.log, arguments.config, arguments.root)
    summary = session.summary()
    step = session.first()
    for _ in range(max(0, (arguments.step or step.number) - step.number)):
        step = session.next()
    if arguments.png is not None:
        print(f"wrote {write_png(frame_for(step, summary), arguments.png)}")
    else:
        from .gui.replay_app import open_window

        open_window(session).run()
    return report(session)


def run_live(arguments: argparse.Namespace) -> int:
    """Play a counted series on one thread and watch it from the window's own."""
    from .gui.live_app import open_window

    box = LatestSnapshot()
    request = StrictSeriesRequest(launch=arguments.launch, viewer=box)
    outcome: list[BaseException] = []

    def play() -> None:
        try:
            asyncio.run(AgentSdk().run_strict_series(request))
        except BaseException as failure:  # the window must still report it
            outcome.append(failure)

    thread = threading.Thread(target=play, name="series", daemon=True)
    thread.start()
    open_window(box, ROLE.value, arguments.launch.stem).run()
    thread.join()
    if outcome:
        print(f"the series ended badly: {outcome[0]}", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    """Open the viewer the arguments asked for; return the process status."""
    arguments = parse_args(argv)
    try:
        if arguments.mode == "live":
            return run_live(arguments)
        return run_replay(arguments)
    except ReplayError as failure:
        print(f"cannot replay: {failure}", file=sys.stderr)
        return 2
    except ToolkitMissingError as missing:
        print(f"cannot open a window: {missing}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
