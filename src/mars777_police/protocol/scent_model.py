"""The agreed scent model's canonical bytes, and the digest that locks them.

Four layers again, exactly as `config_lock` keeps them apart:

1. the **canonical binding bytes** of the agreed model - content only, mapped
   here member by member;
2. **`scent_model_sha256`**, an *unkeyed* content digest that identifies the
   model and authenticates nobody;
3. the **`AuthProof`** over the lock context, which now carries that digest and
   therefore binds the model to this game, sub-game and profile set;
4. the local `CONFIG_LOCKED` transition, which has no bytes at all.

**It is not `config_sha256`.** The 35-member Appendix-B core is untouched by
this module: the model is a *separate* agreement with a separate identity, so a
peer that proposes different weights changes this digest and leaves the config
digest exactly where it was. That separation is the whole point of C-14 - the
numeric contract stays Appendix-F, and the interpretation gets its own lock.

Mapping only. Nothing here validates the model (`domain.scent_model` and
`ScentKernel` do) and nothing re-implements canonicalization
(`protocol.canonical` does). Decimals reach the bytes as `Decimal`, so they are
written as their verbatim text and no `float` exists on the path.
"""

from decimal import Decimal
from hashlib import sha256

from ..app.protocol_values import Sha256Digest
from ..domain.scent_kernel import ScentKernel
from ..domain.scent_model import ScentExample, ScentModelAgreement
from .canonical import canonical_json_bytes


def kernel_core(kernel: ScentKernel) -> list[list[Decimal]]:
    """The 25 weights as rows, in the one order the kernel already stores them."""
    return [list(row) for row in kernel.weights]


def example_core(example: ScentExample) -> dict[str, object]:
    """One worked number, mapped explicitly - the expectation is part of the core."""
    return {
        "tau_before": example.tau_before,
        "delta": example.delta,
        "expected": example.expected,
    }


def scent_model_core(agreement: ScentModelAgreement) -> dict[str, object]:
    """The complete agreed model as JSON-native material, member by member.

    Every field the peers must interpret identically is here: the named
    interpretation, the three Appendix-F values, all 25 weights and every worked
    example. A member added to the agreement tomorrow does not silently enter
    the digest - it has to be mapped.
    """
    return {
        "model_id": agreement.model_id,
        "center_intensity": agreement.center_intensity,
        "decay": agreement.decay_rate,
        "field_size": agreement.field_size,
        "kernel": kernel_core(agreement.kernel),
        "examples": [example_core(example) for example in agreement.examples],
    }


def scent_model_bytes(agreement: ScentModelAgreement) -> bytes:
    """Return the canonical bytes two peers must produce identically."""
    return canonical_json_bytes(scent_model_core(agreement))


def scent_model_sha256(agreement: ScentModelAgreement) -> Sha256Digest:
    """Return the unkeyed content digest over the canonical model bytes."""
    return Sha256Digest(sha256(scent_model_bytes(agreement)).hexdigest())
