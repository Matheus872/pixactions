from solders.keypair import Keypair

from pixactions_api.solana.tx import tx_from_b64, tx_to_b64


def sign_b64(b64: str, *signers: Keypair) -> str:
    """Simulates the user's wallet (Privy) signing a transaction issued by the API."""
    tx = tx_from_b64(b64)
    tx.partial_sign(list(signers), tx.message.recent_blockhash)
    return tx_to_b64(tx)
