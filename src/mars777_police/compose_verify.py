"""Proving a stored config artifact from its own bytes, for a reader.

`artifact_verification` already owns every check; what was missing was a way to
reach it without assembling the verification authority by hand. That authority
is the operator's provisioned key - the same one the live lock uses - and it
comes from the environment exactly as it does at boot, because an artifact never
carries the material needed to check its own authorship.
"""

import os
from collections.abc import Mapping

from .app.config_artifact_values import ConfigArtifactContent
from .artifact_verification import verify_config_artifact
from .composition_inputs import keyed_authenticator
from .identity import ROLE
from .infra.settings import load_runtime_settings
from .protocol.config_lock import ConfigLockAuthenticator


def verify_stored_config(document: Mapping[str, object]) -> ConfigArtifactContent:
    """Return what *document* proves, or refuse it - never a boolean verdict."""
    settings = load_runtime_settings(os.environ, expected_role=ROLE)
    return verify_config_artifact(document, ConfigLockAuthenticator(keyed_authenticator(settings)))
