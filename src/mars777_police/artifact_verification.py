"""Reading a config artifact back, and proving what it claims from its bytes.

`ARTIFACT_LIFECYCLE.md` §10 asks the artifact set alone to let an independent
process verify the match with no live state and no network. For the config file
that means two identities and one authenticated context:

* the 35-member core, digested here and compared with the context's
  ``config_sha256``;
* the complete agreed scent model, digested here and compared both with the
  digest stored beside it and with the context's ``scent_model_sha256``;
* the keyed proof, verified over that exact context by an authority the caller
  supplies - the artifact carries a `key_id` and a tag, never key material, so a
  reader without the provisioned key can check everything except authorship and
  is told so rather than sold a false guarantee.

**Nothing is recomputed twice and nothing is redefined.** The digests come from
the same `protocol` functions the live lock uses, the model's own validators
decide whether it is a model at all, and the codec decides whether the bytes are
a config artifact. A doctored file therefore fails against production
authorities rather than against a second opinion written for reading.

The refusals reuse the identities those layers already own: bytes that are not
this shape are `MalformedMessageError`, evidence that contradicts itself is
`ConfigMismatchError`, and a proof that does not verify is `AuthFailureError`.
"""

from collections.abc import Mapping

from .app.config_artifact_values import ConfigArtifactContent
from .app.ports import ConfigLockAuthPort
from .app.protocol_errors import AuthFailureError, ConfigMismatchError
from .protocol.config_lock import config_sha256
from .protocol.scent_model import scent_model_sha256
from .transport.codec_artifacts import decode_config_artifact


def verify_config_artifact(
    document: Mapping[str, object], auth: ConfigLockAuthPort
) -> ConfigArtifactContent:
    """Return what *document* proves, or refuse it - never a boolean verdict.

    *auth* is the provisioned verification authority, exactly as the live lock
    receives one; the artifact never carries the material it needs.
    """
    content = decode_config_artifact(document)
    _require_digests(content)
    if not auth.verify(content.evidence.context, content.evidence.auth):
        raise AuthFailureError("the stored config lock proof does not verify over its context")
    return content


def _require_digests(content: ConfigArtifactContent) -> None:
    """Recompute both identities and hold the stored ones to them."""
    context = content.evidence.context
    derived = scent_model_sha256(content.scent_model)
    if derived != content.scent_model_sha256:
        raise ConfigMismatchError(
            "the stored scent model does not hash to the digest stored beside it",
        )
    if derived != context.scent_model_sha256:
        raise ConfigMismatchError(
            "the stored scent model is not the model the locked context names",
        )
    if config_sha256(content.config) != context.config_sha256:
        raise ConfigMismatchError(
            "the stored config core is not the core the locked context names",
        )
