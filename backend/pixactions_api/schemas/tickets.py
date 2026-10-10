from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_PK = "8sLbNZoA1cfnvMJLPfp98ZLAnFSYCFApfJKMbiXNLwxj"
EXAMPLE_TICKET = {
    "pubkey": _PK,
    "serial": 4,
    "owner": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "checked_in": False,
    "event": {"slug": "meetup-solana-sp-3f9a", "title": "Meetup Solana SP", "venue": "São Paulo, SP", "starts_at": "2026-10-20T22:00:00Z"},
    "url": f"https://pixactions.vercel.app/t/{_PK}",
    "explorer_url": f"https://explorer.solana.com/address/{_PK}?cluster=devnet",
}


class TicketEvent(BaseModel):
    slug: str
    title: str
    venue: str
    starts_at: datetime


class TicketOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [EXAMPLE_TICKET]})

    pubkey: str
    serial: int = Field(description="Ticket number within the event (0-based).")
    owner: str
    checked_in: bool
    event: TicketEvent | None
    url: str
    explorer_url: str


class CheckinTx(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"transaction": "AgAAAA...==", "checkin_token": "9f2c...e1.4b7a...0c"}]})

    transaction: str = Field(description="Base64 `check_in` tx for the organizer (check-in authority) to sign.")
    checkin_token: str = Field(description="Opaque token binding the issued transaction; send it back on submit.")


class CheckinSubmit(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"transaction": "AgAAAA...==", "checkin_token": "9f2c...e1.4b7a...0c"}]})

    transaction: str
    checkin_token: str
