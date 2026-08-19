"""Which configuration schema versions this build can actually run.

`VERSIONING.md` records the whole provenance: the **key** `schema_version` is
source-explicit (it appears in the App B config example), the book **binds no
value** and **defines no compatibility rule**, and this project therefore owns
the token - `mars777-1` by JDEC-003, made a negotiated pre-match term by NDEC-004
because it sits inside the signed core and so affects `config_sha256`.

**Agreement is not compatibility.** Byte-identity with the opponent proves the
two sides hold the same document; it proves nothing about whether either side can
represent it. Two peers can agree perfectly on a version neither one supports.
The excellence guideline §8.1 asks for the second, local question - *does this
installed code support this configuration version?* - and that is the only
question this module answers.

**There is no fallback.** An unsupported version is refused: never normalised to
the current one, never replaced by a default, and never accepted because both
peers happened to send it. A configuration this build cannot represent is not a
value it will construct.

Deliberately absent: the software package version, the interoperability pin, the
rate-limit configuration version and any artifact version. Those are four other
concepts with four other owners, and folding any of them in here would make a
local packaging fact look like a peer contract.
"""

from typing import Final

from .config_sections import InvalidConfigSectionError

SUPPORTED_CONFIG_SCHEMA_VERSIONS: Final[frozenset[str]] = frozenset({"mars777-1"})
"""Every configuration schema revision this build can represent and play."""


class UnsupportedConfigSchemaError(InvalidConfigSectionError):
    """A well-formed configuration this build cannot represent.

    Deliberately a **subclass** of the section error: an unsupported revision is
    a proposed-config violation like any other, so every existing caller that
    classifies configuration failures keeps working, while a caller that wants to
    tell "malformed" from "unsupported" now can.
    """


def require_supported_schema_version(value: object) -> str:
    """Return *value* when this build supports it, otherwise refuse it.

    Shape first, then support: a version that is not a non-empty string is
    malformed rather than unsupported, and saying so keeps the two failures
    distinguishable in a log.
    """
    if type(value) is not str or not value:
        raise InvalidConfigSectionError("schema_version must be a non-empty str")
    if value not in SUPPORTED_CONFIG_SCHEMA_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_CONFIG_SCHEMA_VERSIONS))
        raise UnsupportedConfigSchemaError(
            f"schema_version {value!r} is not supported by this build; supported: {supported}",
        )
    return value
