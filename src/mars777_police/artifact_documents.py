"""The three official documents whose representation already exists elsewhere.

An artifact is not a new schema. The declaration and the config are already
frozen as wire models with codecs the peer validates against, and the result core
is already the exact projection `result_sha256` covers. So this module renders
nothing itself: it asks the existing owner and hands the document on.

That is why it lives out here beside `composition` rather than in `app`. The
codecs belong to `transport`, and the layer rule that keeps `app` free of the
framework is worth more than the convenience of importing one function inward.

**The result carries its hash, and never inside the core.** `result_sha256`,
`mutual_agreement` and `reported_by` sit beside the core, exactly as
`RESULT_CONTRACT.md` requires - a core that contained its own hash could not be
hashed twice to the same value.

**The config artifact is an envelope, and the core is one section of it.**
`CONFIG_CONTRACT.md` §R12-E keeps four layers apart: the 35-member core, the
unkeyed `config_sha256` **outside** it, the keyed proof beside that, and the
local lock transition that has no bytes at all. The document mirrors exactly
that - `config` is still the one representation both peers digest, and the
digest, the proof and the agreed scent model sit outside it, never inside the
bytes they cover. That is also what makes the file replay-sufficient: a reader
holding it can recompute both identities and check them against the one
authenticated context, without the live session that produced it.
"""

from .app.artifact_store import ArtifactDocument
from .app.config_artifact_values import ConfigArtifactContent
from .app.declaration_values import Declaration
from .app.pregame_session_runtime import PregameSessionRuntime
from .app.protocol_errors import LocalDefectError
from .app.result_exchange import ResultExchange
from .domain.negotiated_config import NegotiatedConfig
from .protocol.config_lock import config_sha256
from .protocol.result_core import result_core
from .protocol.scent_model import scent_model_sha256
from .transport.codec_artifacts import encode_config_artifact
from .transport.codec_declaration import encode_declaration


def declaration_document(declaration: Declaration) -> ArtifactDocument:
    """The declaration exactly as Step-0 carries it - the launch input's inverse."""
    document: dict[str, object] = encode_declaration(declaration).model_dump(
        mode="json", exclude_none=True
    )
    return document


def config_document(config: NegotiatedConfig, pregame: PregameSessionRuntime) -> ArtifactDocument:
    """The locked config, the lock that authenticated it, and the agreed model.

    Every section reports a fact that already happened. The evidence is the one
    *this round verified* - never our own unanswered proposal and never a
    previous sub-game's, because `open_round` drops it - so a sub-game whose lock
    was refused has nothing to write and says so instead of writing a file that
    claims a lock nobody performed.

    The model is the one the round actually agreed, read from the lock runtime
    that verified with it. Nothing here reconstructs a default: a series that
    agreed a different valid model persists **that** model.
    """
    evidence = pregame.locked_evidence
    if evidence is None:
        raise LocalDefectError("a config artifact waits for a lock this side verified")
    model = pregame.lock.scent_model
    digest = scent_model_sha256(model)
    if digest != evidence.context.scent_model_sha256:
        raise LocalDefectError("the agreed model is not the one the verified lock names")
    if config_sha256(config) != evidence.context.config_sha256:
        raise LocalDefectError("the config offered for the record is not the locked core")
    content = ConfigArtifactContent(config, model, digest, evidence)
    document: dict[str, object] = encode_config_artifact(content).model_dump(mode="json")
    return document


def result_document(exchange: ResultExchange, reported_by: str) -> ArtifactDocument:
    """The agreed result: the approval core, its hash, and who is reporting it."""
    digest = exchange.local_digest
    if digest is None:
        raise LocalDefectError("an agreed result always has a local digest")
    document: dict[str, object] = dict(result_core(exchange.approval_core()))
    document["result_sha256"] = digest.value
    document["mutual_agreement"] = True
    document["reported_by"] = reported_by
    return document
