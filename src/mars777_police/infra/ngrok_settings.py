"""Where the operator's ngrok lives, and how long we are willing to wait.

Every path is **injected**. Hard-coding an executable location or a home
directory would make the adapter untestable and unusable on another machine, and
`PRD05-FR-050` already requires the credential itself to come from the operator's
own environment rather than from anything the project ships.

The two waits exist because the agent's own behaviour demands them: it prints
its Agent API address only after starting the web service, and it answers that
API with an empty collection until registration completes.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class NgrokSettings:
    """Operator-supplied location and bounds for the ngrok Agent."""

    executable: Path
    config_paths: tuple[Path, ...] = ()
    startup_seconds: float = 30.0
    discovery_seconds: float = 45.0
    poll_seconds: float = 0.5

    def __post_init__(self) -> None:
        if not isinstance(self.executable, Path):
            raise ValueError("executable must be a Path")
        for bound in (self.startup_seconds, self.discovery_seconds, self.poll_seconds):
            if type(bound) is not float or bound <= 0:
                raise ValueError("every wait bound must be a positive float")

    def argv(self, port: int) -> tuple[str, ...]:
        """The exact command line used to expose *port*.

        **No credential appears here.** The agent reads the operator's own
        configuration; passing a token as an argument would publish it to the
        process list, which `FR-051` forbids. Structured JSON logging is
        requested because the Agent API address is only discoverable from it.
        """
        arguments = [str(self.executable), "http", str(port)]
        for path in self.config_paths:
            arguments += ["--config", str(path)]
        arguments += ["--log", "stdout", "--log-format", "json"]
        return tuple(arguments)
