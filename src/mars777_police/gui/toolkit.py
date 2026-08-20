"""Where the window toolkit is obtained, and where its absence becomes a sentence.

`tkinter` is part of the standard library, but it is not always **installed**:
Debian and Ubuntu ship it as a separate `python3-tk` package, so a perfectly
ordinary Python 3.12 can lack it - including the interpreter this project's own
Linux CI runs. Importing it at module scope therefore makes the whole graphical
package unimportable on a machine that could still draw every picture it needs.

So the import happens **here**, once, at the moment a window is actually asked
for. Everything that does not open a window - the layouts, the offscreen
rasteriser, `--png`, and every test of them - needs no toolkit at all, which is
exactly the separation the two adapters were built for.

Absence is reported as a refusal with a remedy, never as a traceback.
"""

import importlib
from types import ModuleType
from typing import Final

TOOLKIT: Final[str] = "tkinter"

REMEDY: Final[str] = (
    "this Python has no tkinter, so no window can be opened. On Debian or Ubuntu"
    " install it with `sudo apt install python3-tk`; on any machine, the same"
    " picture can be written to a file instead with `--png`."
)


class ToolkitMissingError(RuntimeError):
    """Raised when a window is asked for on an interpreter that cannot open one."""


def available() -> bool:
    """Whether this interpreter could open a window at all. Asks nothing else."""
    try:
        importlib.import_module(TOOLKIT)
    except ModuleNotFoundError:
        return False
    return True


def toolkit() -> ModuleType:
    """The window toolkit, or a refusal naming what to install instead."""
    try:
        return importlib.import_module(TOOLKIT)
    except ModuleNotFoundError as missing:
        raise ToolkitMissingError(REMEDY) from missing
