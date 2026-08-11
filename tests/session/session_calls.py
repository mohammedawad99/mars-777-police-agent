"""The nine inbound kinds as one production client would actually send them.

Also the two hostile variants: a Step-0 whose keyed proof does not verify, and a
result request contributing a group the session never authenticated.
"""

import dataclasses

import audit_builders
import peer_ops
import turn_builders

from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_final import encode_final_nonce, encode_result_agreement
from mars777_police.transport.codec_pregame import encode_lock, encode_proposal
from mars777_police.transport.codec_turn import (
    encode_acknowledgement,
    encode_commitment,
    encode_reveal,
)


def payloads() -> list[tuple[str, str, object]]:
    """Every kind, in the order one legitimate session would send them."""
    return [
        ("negotiate", "step0", encode_step0(peer_ops.step0_exchange())),
        ("negotiate", "config_proposal", encode_proposal(peer_ops.proposal())),
        ("negotiate", "config_lock", encode_lock(peer_ops.lock_evidence())),
        ("receive_turn", "commitment", encode_commitment(turn_builders.commitment())),
        (
            "receive_turn",
            "acknowledgement",
            encode_acknowledgement(turn_builders.acknowledgement()),
        ),
        ("receive_turn", "reveal", encode_reveal(turn_builders.legal_reveal())),
        (
            "submit_audit",
            "final_nonce_reveal",
            encode_final_nonce(audit_builders.nonce_batch()),
        ),
        ("submit_audit", "audit_disclosure", audit_builders.document()),
        (
            "receive_control",
            "result_agreement",
            encode_result_agreement(peer_ops.agreement()),
        ),
    ]


KINDS = [kind for _, kind, _ in payloads()]
"""The exact nine kind tokens, in send order."""


def forged_step0() -> object:
    """A structurally perfect Step-0 whose keyed proof does not verify."""
    exchange = peer_ops.step0_exchange()
    proof = dataclasses.replace(exchange.auth, value="0" * len(exchange.auth.value))
    return dataclasses.replace(exchange, auth=proof)


def spoofed_agreement() -> object:
    """A result request contributing a group the session never authenticated."""
    from r16_builders import COMMIT_A, GROUP_A, contribution

    return dataclasses.replace(peer_ops.agreement(), contribution=contribution(GROUP_A, COMMIT_A))
