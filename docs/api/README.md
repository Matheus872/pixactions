# Pix Actions API

The Pix Actions API lets anyone pay with Pix and receive an onchain asset on Solana, with no wallet setup. The first use case is event tickets: organizers publish events onchain, buyers pay a Pix charge, and the ticket is minted as a Solana account owned by the buyer's embedded wallet.

## Environments

| Item | Value |
|---|---|
| Cluster | Solana devnet |
| Base URL | `https://pixactions-api.vercel.app` (replace with your deployment) |
| Interactive reference | `GET /docs` (Scalar, with "try it" and code samples) |
| Alternative reference | `GET /redoc` |
| OpenAPI document | `GET /openapi.json`, also committed at [`openapi.json`](openapi.json) |
| Health | `GET /health` returns the program id, service wallet and payment mint in use |

## The transaction pattern: build, sign, submit

Every onchain write follows the same three steps:

1. **Build.** The API builds the transaction. The API is always the fee payer and pays rent, so users never need SOL.
2. **Sign.** The client signs with the user's wallet (the Privy embedded wallet in the web app).
3. **Submit.** The client sends the signed transaction back. The API checks that the message is byte for byte the one it issued (sha256 of the message), co-signs as fee payer and broadcasts.

A signed transaction that differs from the issued one is rejected with `TX_MISMATCH`. Transactions expire with their blockhash (about a minute); see [errors](errors.md) for how to recover.

## Guides

- [Authentication](authentication.md): Privy access tokens and what the API stores.
- [Checkout flow](checkout-flow.md): buyer journey from Pix charge to onchain ticket, with a sequence diagram.
- [Organizer flow](organizer-flow.md): create and publish events, list sales, check tickets in.
- [Solana Actions](solana-actions.md): every event is also a Blink.
- [Webhooks](webhooks.md): Pix provider callbacks and how to plug a real on-ramp.
- [Errors](errors.md): every error code and what the client should do.
- [Onchain program](onchain-program.md): accounts, instructions, PDAs and error codes.

## Routes

| Tag | Method and path | Auth |
|---|---|---|
| Health | `GET /health` | no |
| Waitlist | `POST /v1/waitlist` | no |
| Events | `POST /v1/events` | organizer |
| Events | `POST /v1/events/{event_id}/transaction` | organizer |
| Events | `POST /v1/events/{event_id}/submit` | organizer |
| Events | `GET /v1/me/events` | organizer |
| Events | `GET /v1/events/{slug}` | no |
| Events | `GET /v1/events/{event_id}/orders` | organizer |
| Orders | `POST /v1/orders` | buyer |
| Orders | `GET /v1/orders/{order_id}` | buyer |
| Orders | `POST /v1/orders/{order_id}/submit` | buyer |
| Tickets | `GET /v1/tickets/{pubkey}` | no |
| Tickets | `POST /v1/tickets/{pubkey}/checkin` | organizer |
| Tickets | `POST /v1/tickets/{pubkey}/checkin/submit` | organizer |
| Solana Actions | `GET /actions.json` | no |
| Solana Actions | `GET /actions/events/{slug}` | no |
| Solana Actions | `POST /actions/events/{slug}` | no |
| Webhooks | `POST /v1/webhooks/pix/{provider}` | provider signature |
| Dev | `POST /v1/dev/orders/{order_id}/simulate-payment` | no (disabled when `ENV=production`) |

## Quick check

```bash
curl https://pixactions-api.vercel.app/health
```

```json
{
  "status": "ok",
  "version": "0.1.0",
  "env": "demo",
  "cluster": "devnet",
  "program_id": "DZ5ddra1TXhkbS9ZBnimtZPVeTxoXmxbCGvFHJqKVPa9",
  "service_wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "payment_mint": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
}
```
