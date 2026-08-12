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
"""

from .app.artifact_store import ArtifactDocument
from .app.declaration_values import Declaration
from .app.protocol_errors import LocalDefectError
from .app.result_exchange import ResultExchange
from .domain.negotiated_config import NegotiatedConfig
from .protocol.result_core import result_core
from .transport.codec_config import encode_config
from .transport.codec_declaration import encode_declaration


def declaration_document(declaration: Declaration) -> ArtifactDocument:
    """The declaration exactly as Step-0 carries it - the launch input's inverse."""
    document: dict[str, object] = encode_declaration(declaration).model_dump(
        mode="json", exclude_none=True
    )
    return document


def config_document(config: NegotiatedConfig) -> ArtifactDocument:
    """The locked config in the one wire representation both peers digest."""
    document: dict[str, object] = encode_config(config).model_dump(mode="json")
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
