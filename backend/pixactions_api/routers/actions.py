from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from solders.pubkey import Pubkey

from ..deps import GatewayDep, ServiceDep, SessionDep, SettingsDep
from ..errors import ApiError
from ..pricing import format_token
from ..schemas.actions import (
    ActionError,
    ActionGetResponse,
    ActionLink,
    ActionLinks,
    ActionPostRequest,
    ActionPostResponse,
    ActionRule,
    ActionsJson,
)
from ..services.events import get_live_event_by_slug, read_event_account
from ..services.orders import SELF_PURCHASE_MESSAGE
from ..solana.constants import DEVNET_GENESIS_HASH
from ..solana.instructions import buy_ticket_ix
from ..solana.pda import ata_address
from ..solana.spl import create_ata_idempotent_ix, mint_to_ix
from ..solana.tx import build_tx, tx_to_b64
from ..timeutil import as_utc

router = APIRouter(tags=["Solana Actions"])
ACTION_HEADERS = {"X-Action-Version": "2.4", "X-Blockchain-Ids": f"solana:{DEVNET_GENESIS_HASH}"}
_ERR = {"model": ActionError}


def _headers(response: Response) -> None:
    response.headers.update(ACTION_HEADERS)


def _error(message: str, status: int) -> JSONResponse:
    return JSONResponse({"message": message}, status_code=status, headers=ACTION_HEADERS)


@router.get("/actions.json", response_model=ActionsJson, summary="Actions rules")
async def actions_json(response: Response) -> ActionsJson:
    """Maps website paths to Action API paths, so Blink clients can discover actions on this domain."""
    _headers(response)
    return ActionsJson(rules=[ActionRule(pathPattern="/actions/**", apiPath="/actions/**")])


@router.get(
    "/actions/events/{slug}",
    response_model=ActionGetResponse,
    summary="Event action metadata",
    responses={404: _ERR | {"description": "Event not found"}},
)
async def get_event_action(
    slug: str, response: Response, session: SessionDep, settings: SettingsDep, gateway: GatewayDep
) -> ActionGetResponse | JSONResponse:
    """Solana Actions GET: what a Blink client renders (icon, title, button). Disabled when sold out."""
    try:
        row = await get_live_event_by_slug(session, slug)
        acc = await read_event_account(gateway, row)
    except ApiError as exc:
        return _error(exc.message, exc.status_code)
    sold_out = acc is not None and acc.sold >= acc.capacity
    label = f"Comprar ingresso · {format_token(row.price_token)} USDC"
    _headers(response)
    return ActionGetResponse(
        icon=row.image_url or f"{settings.public_web_url}/opengraph-image",
        title=row.title,
        description=(
            f"{row.venue} · {as_utc(row.starts_at):%d/%m/%Y %H:%M} UTC · R$ {row.price_brl_cents / 100:.2f}. "
            f"Sem carteira? Pague com Pix em {settings.public_web_url}/e/{row.slug}"
        ),
        label=label,
        disabled=sold_out,
        links=ActionLinks(actions=[ActionLink(label=label, href=f"/actions/events/{row.slug}")]),
        error=ActionError(message="Esgotado") if sold_out else None,
    )


@router.post(
    "/actions/events/{slug}",
    response_model=ActionPostResponse,
    summary="Build the purchase transaction for a wallet",
    responses={400: _ERR | {"description": "Invalid account"}, 404: _ERR | {"description": "Event not found"}, 409: _ERR | {"description": "Sold out"}},
)
async def post_event_action(
    slug: str, body: ActionPostRequest, response: Response, session: SessionDep,
    settings: SettingsDep, gateway: GatewayDep, service: ServiceDep,
) -> ActionPostResponse | JSONResponse:
    """Solana Actions POST: returns `buy_ticket` for `account`, already signed by the API as fee payer.
    On devnet the same transaction first mints one ticket's worth of mock USDC to the wallet, so any
    devnet wallet can try the Blink."""
    try:
        buyer = Pubkey.from_string(body.account)
    except ValueError:
        return _error("Invalid account", 400)
    try:
        row = await get_live_event_by_slug(session, slug)
        acc = await read_event_account(gateway, row)
    except ApiError as exc:
        return _error(exc.message, exc.status_code)
    if body.account == row.organizer_wallet:
        return _error(SELF_PURCHASE_MESSAGE, 400)
    if acc is None:
        return _error("Event not found onchain", 404)
    if acc.sold >= acc.capacity:
        return _error("Event is sold out", 409)

    mint = Pubkey.from_string(row.payment_mint)
    organizer = Pubkey.from_string(row.organizer_wallet)
    payer = treasury = service.pubkey()
    ixs = []
    if not settings.is_production:
        ixs += [
            create_ata_idempotent_ix(payer=payer, owner=buyer, mint=mint),
            mint_to_ix(mint=mint, destination=ata_address(buyer, mint), authority=payer, amount=row.price_token),
        ]
    ixs += [
        create_ata_idempotent_ix(payer=payer, owner=organizer, mint=mint),
        create_ata_idempotent_ix(payer=payer, owner=treasury, mint=mint),
        buy_ticket_ix(
            payer=payer, buyer=buyer, organizer=organizer, event=Pubkey.from_string(row.onchain_pubkey),
            payment_mint=mint, treasury=treasury, serial=acc.sold,
        ),
    ]
    tx = build_tx(ixs, payer, await gateway.latest_blockhash())
    tx.partial_sign([service], tx.message.recent_blockhash)
    _headers(response)
    return ActionPostResponse(transaction=tx_to_b64(tx), message=f"Ingresso para {row.title} emitido na Solana!")
