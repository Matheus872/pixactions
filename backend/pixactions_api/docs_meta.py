API_DESCRIPTION = """
**Pix Actions** lets anyone pay with **Pix** and receive an **onchain asset on Solana**, with no wallet setup.
The first use case is event tickets.

## Flow
1. **Organizer** creates an event (`POST /v1/events`), signs `create_event` with their Privy embedded wallet
   and submits it (`POST /v1/events/{id}/submit`).
2. **Buyer** opens the checkout link and creates an order (`POST /v1/orders`), which returns a Pix charge.
3. When the Pix is confirmed, the on-ramp delivers stablecoins to the buyer's wallet and the order
   (`GET /v1/orders/{id}`) exposes the `buy_ticket` transaction to sign (`POST /v1/orders/{id}/submit`).
4. At the door, the organizer scans the ticket and signs `check_in`.

## Transaction pattern: build → sign → submit
The API builds every transaction and is always the **fee payer** (users never need SOL). The client signs
with the user's wallet; the API checks that the signed message is byte-for-byte the one it issued,
co-signs and broadcasts.

## Authentication
`Authorization: Bearer <Privy access token>` (from `getAccessToken()` in the Privy SDK).

## Errors
Every error has the shape `{"error": {"code", "message", "details"}}`. Codes are stable; see `ErrorResponse`.
Solana Actions routes follow the Actions spec and return `{"message"}` instead.

Guides with sequence diagrams live in `docs/api/` in the repository.
"""

TAGS = [
    {"name": "Health", "description": "Service status and the onchain configuration in use."},
    {"name": "Waitlist", "description": "Landing page waitlist."},
    {"name": "Events", "description": "Organizer events: create, publish onchain, list."},
    {"name": "Orders", "description": "Buyer checkout: Pix charge → onchain funding → signed purchase."},
    {"name": "Tickets", "description": "Ticket verification and onchain check-in."},
    {"name": "Solana Actions", "description": "Spec-compliant Actions so any event is also a Blink."},
    {"name": "Webhooks", "description": "Pix provider callbacks."},
    {"name": "Dev", "description": "Sandbox helpers, disabled in production."},
]
