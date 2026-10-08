from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from solders.pubkey import Pubkey

EXAMPLE_WALLET = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"


def _validate_pubkey(value: str) -> str:
    try:
        Pubkey.from_string(value)
    except Exception as exc:
        raise ValueError("must be a base58 Solana address") from exc
    return value


SolanaAddress = Annotated[
    str,
    AfterValidator(_validate_pubkey),
    Field(description="Base58 Solana address.", examples=[EXAMPLE_WALLET]),
]


class SignedTransaction(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"transaction": "AgAAAAAAAAAAAAAAAAAA...=="}]})

    transaction: str = Field(
        description="Base64 Solana transaction previously issued by the API, now signed by the user's wallet."
    )
