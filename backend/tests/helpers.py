from solders.hash import Hash
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from pixactions_api.solana.accounts import EventAccount, encode_event
from pixactions_api.solana.tx import tx_from_b64, tx_to_b64


def sign_b64(b64: str, *signers: Keypair) -> str:
    """Simulates the user's wallet (Privy) signing a transaction issued by the API."""
    tx = tx_from_b64(b64)
    tx.partial_sign(list(signers), tx.message.recent_blockhash)
    return tx_to_b64(tx)


class FakeSolanaGateway:
    """In-memory stand-in for the RPC: records sent txs, serves seeded account data."""

    def __init__(self) -> None:
        self.sent: list[Transaction] = []
        self.accounts: dict[str, bytes] = {}
        self.fail_next: Exception | None = None
        self.blockhash = Hash.new_unique()

    async def latest_blockhash(self) -> Hash:
        return self.blockhash

    async def send_and_confirm(self, tx: Transaction) -> str:
        if self.fail_next is not None:
            err, self.fail_next = self.fail_next, None
            raise err
        assert all(tx.verify_with_results()), "fake RPC got a tx with missing signatures"
        self.sent.append(tx)
        return str(tx.signatures[0])

    async def get_account_data(self, pubkey: Pubkey) -> bytes | None:
        return self.accounts.get(str(pubkey))


def sent_to_program(gateway: FakeSolanaGateway, program_id: Pubkey) -> list[Transaction]:
    """Transactions with at least one instruction for `program_id`."""
    out = []
    for tx in gateway.sent:
        keys = tx.message.account_keys
        if any(keys[ix.program_id_index] == program_id for ix in tx.message.instructions):
            out.append(tx)
    return out


async def create_draft(client, auth, organizer: Keypair, **overrides) -> dict:
    body = {
        "title": "Meetup Solana SP",
        "description": "Primeiro meetup",
        "venue": "São Paulo, SP",
        "starts_at": "2026-10-20T22:00:00Z",
        "price_brl_cents": 2000,
        "capacity": 50,
        "wallet": str(organizer.pubkey()),
    } | overrides
    r = await client.post("/v1/events", json=body, headers=auth())
    assert r.status_code == 201, r.text
    return r.json()


def seed_event_account(gateway, event: dict, *, sold: int = 0, capacity: int | None = None) -> None:
    """Pretend the Event PDA exists onchain with the given counters."""
    organizer = Pubkey.from_string(event["organizer_wallet"])
    gateway.accounts[event["onchain_pubkey"]] = encode_event(
        EventAccount(
            organizer=organizer,
            event_id=0,
            payment_mint=Pubkey.from_string(event["payment_mint"]),
            price=event["price_token"],
            capacity=capacity if capacity is not None else event["capacity"],
            sold=sold,
            starts_at=0,
            checkin_authority=organizer,
            bump=255,
        )
    )
