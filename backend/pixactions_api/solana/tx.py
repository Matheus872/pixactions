import base64
import binascii
import hashlib
from collections.abc import Sequence

from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from ..errors import ApiError, ErrorCode


def build_tx(instructions: Sequence[Instruction], payer: Pubkey, blockhash: Hash) -> Transaction:
    return Transaction.new_unsigned(Message.new_with_blockhash(list(instructions), payer, blockhash))


def tx_to_b64(tx: Transaction) -> str:
    return base64.b64encode(bytes(tx)).decode()


def tx_from_b64(b64: str) -> Transaction:
    try:
        return Transaction.from_bytes(base64.b64decode(b64, validate=True))
    except (binascii.Error, ValueError, Exception) as exc:
        raise ApiError(
            ErrorCode.VALIDATION_ERROR, "transaction is not a valid base64 Solana transaction"
        ) from exc


def message_hash(tx: Transaction) -> str:
    return hashlib.sha256(bytes(tx.message)).hexdigest()


def cosign(signed_b64: str, expected_hash: str, signer: Keypair) -> Transaction:
    """Accept a user-signed tx only if its message is exactly the one we issued, then co-sign."""
    tx = tx_from_b64(signed_b64)
    if message_hash(tx) != expected_hash:
        raise ApiError(ErrorCode.TX_MISMATCH, "Transaction differs from the one issued by the API")
    tx.partial_sign([signer], tx.message.recent_blockhash)
    if not all(tx.verify_with_results()):
        raise ApiError(ErrorCode.TX_MISMATCH, "Transaction is missing a valid user signature")
    return tx
