"""Assembling a replay session from two files on disk, and nothing more.

The viewer needs three things it cannot invent: the log, the locked
configuration the log was played under, and the commitment authority. This
composition reads the first two through the defensive reader and injects the
third, exactly as production injects it for the live audit.

**The config is checked against the log before a single step is replayed.** A
log names the `config_sha256` it was played under; if the configuration handed
to the viewer does not hash to that value, the two files do not describe the
same sub-game and replaying them together would produce a fiction.
"""

from pathlib import Path

from .app.config_rules import rules_of
from .app.replay_log import read_log
from .app.replay_session import ReplaySession
from .app.replay_values import ReplayError
from .infra.replay_files import read_document
from .protocol.audit_commitment import CommitmentRecomputer
from .protocol.config_lock import config_sha256
from .transport.codec_artifacts import decode_config_artifact
from .transport.codec_replay import replay_action

OFFICIAL = "OFFICIAL"
"""Counted evidence: the four official artifact families."""


def open_replay(log: Path, config: Path, root: Path | None = None) -> ReplaySession:
    """Return a session over one official sub-game log and its configuration."""
    document = read_log(read_document(log, root))
    content = decode_config_artifact(read_document(config, root))
    digest = config_sha256(content.config).value
    if digest != document.config_sha256:
        raise ReplayError(
            f"this configuration hashes to {digest}, but the log was played under"
            f" {document.config_sha256}"
        )
    return ReplaySession(
        log=document,
        rules=rules_of(content.config),
        commitments=CommitmentRecomputer(),
        decode=replay_action,
        evidence_class=OFFICIAL,
        notes=(
            "The keyed authorship proof is not checked here: a reader without the"
            " provisioned key can verify every digest and every rule, and is told"
            " so rather than sold a false guarantee.",
        ),
    )
