import hashlib
import hmac

from fastapi import APIRouter
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User, UserDep
from ..config import Settings
from ..deps import GatewayDep, ServiceDep, SessionDep, SettingsDep
from ..errors import ApiError, ErrorCode, error_responses
from ..links import explorer_url, ticket_url
from ..models import EventRow
from ..schemas.tickets import CheckinSubmit, CheckinTx, TicketEvent, TicketOut
from ..solana.accounts import TicketAccount, decode_ticket
from ..solana.gateway import SolanaGateway
from ..solana.instructions import check_in_ix
from ..solana.pda import ticket_pda
from ..solana.tx import build_tx, cosign, message_hash, tx_to_b64
from ..timeutil import as_utc

router = APIRouter(prefix="/v1/tickets", tags=["Tickets"])
E = ErrorCode


def _hmac(service: Keypair, msg_hash: str) -> str:
    return hmac.new(bytes(service)[:32], msg_hash.encode(), hashlib.sha256).hexdigest()


def checkin_token(service: Keypair, msg_hash: str) -> str:
    return f"{msg_hash}.{_hmac(service, msg_hash)}"


def verify_checkin_token(service: Keypair, token: str) -> str:
    msg_hash, _, mac = token.partition(".")
    if not mac or not hmac.compare_digest(mac, _hmac(service, msg_hash)):
        raise ApiError(E.TX_MISMATCH, "Invalid check-in token")
    return msg_hash


async def _load(
    session: AsyncSession, gateway: SolanaGateway, pubkey: str
) -> tuple[Pubkey, TicketAccount, EventRow | None]:
    try:
        pk = Pubkey.from_string(pubkey)
    except ValueError as exc:
        raise ApiError(E.NOT_FOUND, "Ticket not found") from exc
    data = await gateway.get_account_data(pk)
    try:
        ticket = decode_ticket(data) if data else None
    except ValueError:
        ticket = None
    # Only the program can create an account at its PDA: this rejects Ticket-shaped accounts made elsewhere.
    if ticket is None or pk != ticket_pda(ticket.event, ticket.serial):
        raise ApiError(E.NOT_FOUND, "Ticket not found")
    event = await session.scalar(select(EventRow).where(EventRow.onchain_pubkey == str(ticket.event)))
    return pk, ticket, event


def _owned(event: EventRow | None, user: User) -> EventRow:
    if event is None or event.organizer_did != user.did:
        raise ApiError(E.NOT_FOUND, "Ticket not found")
    return event


def _out(pk: Pubkey, ticket: TicketAccount, event: EventRow | None, settings: Settings, *, checked_in: bool) -> TicketOut:
    return TicketOut(
        pubkey=str(pk),
        serial=ticket.serial,
        owner=str(ticket.owner),
        checked_in=checked_in,
        event=TicketEvent(slug=event.slug, title=event.title, venue=event.venue, starts_at=as_utc(event.starts_at)) if event else None,
        url=ticket_url(settings, str(pk)),
        explorer_url=explorer_url(settings, str(pk)),
    )


@router.get("/{pubkey}", response_model=TicketOut, summary="Verify a ticket", responses=error_responses(E.NOT_FOUND, E.RPC_ERROR))
async def get_ticket(pubkey: str, session: SessionDep, settings: SettingsDep, gateway: GatewayDep) -> TicketOut:
    """Reads the ticket account onchain. Public: this is what the entry QR points to."""
    pk, ticket, event = await _load(session, gateway, pubkey)
    return _out(pk, ticket, event, settings, checked_in=ticket.checked_in)


@router.post(
    "/{pubkey}/checkin",
    response_model=CheckinTx,
    summary="Issue a check-in transaction",
    responses=error_responses(E.UNAUTHORIZED, E.NOT_FOUND, E.ALREADY_CHECKED_IN, E.RPC_ERROR),
)
async def issue_checkin(
    pubkey: str, user: UserDep, session: SessionDep, gateway: GatewayDep, service: ServiceDep
) -> CheckinTx:
    """For the event organizer at the door. Returns the `check_in` transaction to sign with the
    organizer wallet plus a `checkin_token` to send back on submit."""
    pk, ticket, event = await _load(session, gateway, pubkey)
    event = _owned(event, user)
    if ticket.checked_in:
        raise ApiError(E.ALREADY_CHECKED_IN, "Ticket already checked in")
    ix = check_in_ix(checkin_authority=Pubkey.from_string(event.organizer_wallet), event=ticket.event, ticket=pk)
    tx = build_tx([ix], service.pubkey(), await gateway.latest_blockhash())
    return CheckinTx(transaction=tx_to_b64(tx), checkin_token=checkin_token(service, message_hash(tx)))


@router.post(
    "/{pubkey}/checkin/submit",
    response_model=TicketOut,
    summary="Submit the signed check-in",
    responses=error_responses(
        E.UNAUTHORIZED, E.NOT_FOUND, E.TX_MISMATCH, E.TX_EXPIRED, E.ALREADY_CHECKED_IN, E.VALIDATION_ERROR, E.RPC_ERROR
    ),
)
async def submit_checkin(
    pubkey: str, body: CheckinSubmit, user: UserDep, session: SessionDep, settings: SettingsDep,
    gateway: GatewayDep, service: ServiceDep,
) -> TicketOut:
    """Verifies the organizer-signed `check_in`, co-signs and broadcasts. A second check-in of the
    same ticket fails onchain with `ALREADY_CHECKED_IN`."""
    pk, ticket, event = await _load(session, gateway, pubkey)
    event = _owned(event, user)
    tx = cosign(body.transaction, verify_checkin_token(service, body.checkin_token), service)
    if pk not in tx.message.account_keys:
        raise ApiError(E.TX_MISMATCH, "Transaction is for a different ticket")
    await gateway.send_and_confirm(tx)
    return _out(pk, ticket, event, settings, checked_in=True)
