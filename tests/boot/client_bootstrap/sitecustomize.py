"""Test-only bootstrap that times the real CLI's own HTTP writes.

The shipped entrypoint is `python -m mars777_police`, and this checkpoint has
to know when *that* process actually put a request body on the wire - which no
amount of instrumenting the opponent can answer. Editing `src` to find out is
exactly what must not happen, so the measurement is installed the way an
operator installs one from outside: a `sitecustomize` module the interpreter
imports at startup, placed on `PYTHONPATH` by the test that spawns the process.

It is inert unless `MARS777_CLIENT_TRACE` names a file, so a process that was
not asked to be measured is untouched, and it never reaches into the agent -
only into the installed HTTP client library, wrapping two calls transparently.
"""

import os
import sys
from pathlib import Path

_TRACE = os.environ.get("MARS777_CLIENT_TRACE", "")

if _TRACE:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        import process_trace

        process_trace.install_client(process_trace.HandlerTrace(Path(_TRACE)))
    except Exception:  # pragma: no cover - a diagnostic must never break a run
        pass
