from decimal import ROUND_HALF_UP, Decimal

TOKEN_DECIMALS = 6


def brl_cents_to_token_units(cents: int, brl_per_usd: Decimal) -> int:
    usd = Decimal(cents) / Decimal(100) / brl_per_usd
    return int((usd * Decimal(10**TOKEN_DECIMALS)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fee_units(price: int, fee_bps: int) -> int:
    return price * fee_bps // 10_000


def format_token(units: int) -> str:
    return f"{Decimal(units) / Decimal(10**TOKEN_DECIMALS):.2f}"
