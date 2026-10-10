from types import SimpleNamespace

import pytest
from solders.transaction_status import TransactionConfirmationStatus

from pixactions_api.errors import ApiError, ErrorCode
from pixactions_api.solana.gateway import poll_confirmation

CONFIRMED = SimpleNamespace(err=None, confirmation_status=TransactionConfirmationStatus.Confirmed)
PROCESSED = SimpleNamespace(err=None, confirmation_status=TransactionConfirmationStatus.Processed)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def responses(*items):
    """fetch_status stub: returns or raises each item in order."""
    queue = list(items)

    async def fetch():
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return fetch


async def test_retries_rate_limited_status_polls_until_confirmed():
    clock = FakeClock()
    rate_limited = RuntimeError("HTTPStatusError: 429 Too Many Requests")
    fetch = responses(rate_limited, rate_limited, None, PROCESSED, CONFIRMED)
    status = await poll_confirmation(fetch, sleep=clock.sleep, clock=clock)
    assert status is CONFIRMED
    assert clock.sleeps[:2] == [0.5, 1.0]  # backs off after rate limits


async def test_returns_failed_transactions_without_waiting_for_confirmation():
    clock = FakeClock()
    failed = SimpleNamespace(err="InstructionErrorCustom(6001)", confirmation_status=TransactionConfirmationStatus.Processed)
    assert await poll_confirmation(responses(failed), sleep=clock.sleep, clock=clock) is failed


async def test_gives_up_after_timeout_while_unconfirmed():
    clock = FakeClock()
    fetch = responses(*([None] * 200))
    with pytest.raises(ApiError) as err:
        await poll_confirmation(fetch, timeout=10, sleep=clock.sleep, clock=clock)
    assert err.value.code == ErrorCode.TX_EXPIRED


async def test_gives_up_after_timeout_when_rpc_keeps_failing():
    clock = FakeClock()
    fetch = responses(*([RuntimeError("HTTPStatusError: 503")] * 200))
    with pytest.raises(ApiError) as err:
        await poll_confirmation(fetch, timeout=10, sleep=clock.sleep, clock=clock)
    assert err.value.code == ErrorCode.RPC_ERROR
