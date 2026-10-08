import re
from typing import Protocol

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.models import TxOpts
from solders.hash import Hash
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from ..errors import ApiError, ErrorCode

_PROGRAM_ERRORS = {
    6000: (ErrorCode.SOLD_OUT, "Event is sold out"),
    6001: (ErrorCode.ALREADY_CHECKED_IN, "Ticket already checked in"),
}


def map_rpc_error(text: str) -> ApiError:
    low = text.lower()
    if "blockhash not found" in low or "block height exceeded" in low or "has expired" in low:
        return ApiError(ErrorCode.TX_EXPIRED, "Transaction expired; fetch a fresh one and sign again")
    if "already in use" in low:
        return ApiError(
            ErrorCode.TX_STALE,
            "Ticket slot taken by a concurrent purchase; fetch a fresh transaction",
        )
    code: int | None = None
    if m := re.search(r"custom program error: 0x([0-9a-f]+)", low):
        code = int(m.group(1), 16)
    elif m := re.search(r"custom\((\d+)\)", low):
        code = int(m.group(1))
    if code in _PROGRAM_ERRORS:
        err_code, message = _PROGRAM_ERRORS[code]
        return ApiError(err_code, message)
    return ApiError(ErrorCode.RPC_ERROR, "Solana RPC error", {"detail": text[:500]})


class SolanaGateway(Protocol):
    async def latest_blockhash(self) -> Hash: ...
    async def send_and_confirm(self, tx: Transaction) -> str: ...
    async def get_account_data(self, pubkey: Pubkey) -> bytes | None: ...


class RpcSolanaGateway:
    """Real RPC gateway. Opens a client per call: safe across serverless event loops."""

    def __init__(self, url: str) -> None:
        self._url = url

    def _client(self) -> AsyncClient:
        return AsyncClient(self._url, commitment=Confirmed)

    async def latest_blockhash(self) -> Hash:
        try:
            async with self._client() as c:
                return (await c.get_latest_blockhash()).value.blockhash
        except Exception as exc:
            raise map_rpc_error(str(exc)) from exc

    async def send_and_confirm(self, tx: Transaction) -> str:
        try:
            async with self._client() as c:
                opts = TxOpts(skip_confirmation=True, preflight_commitment=Confirmed)
                sig = (await c.send_raw_transaction(bytes(tx), opts=opts)).value
                await c.confirm_transaction(sig, commitment=Confirmed, sleep_seconds=0.4)
                status = (await c.get_signature_statuses([sig])).value[0]
        except ApiError:
            raise
        except Exception as exc:
            raise map_rpc_error(str(exc)) from exc
        if status is not None and status.err is not None:
            raise map_rpc_error(str(status.err))
        return str(sig)

    async def get_account_data(self, pubkey: Pubkey) -> bytes | None:
        try:
            async with self._client() as c:
                resp = await c.get_account_info(pubkey)
        except Exception as exc:
            raise map_rpc_error(str(exc)) from exc
        return bytes(resp.value.data) if resp.value is not None else None
