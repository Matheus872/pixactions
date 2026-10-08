# Solana Actions

Every live event is also a [Solana Action](https://solana.com/developers/guides/advanced/actions). Wallet users can buy straight from a Blink (on X with Phantom or Backpack, or on dial.to), while everyone else pays with Pix in the checkout. Both paths call the same `buy_ticket` instruction.

## Discovery: `actions.json`

```bash
curl https://pixactions.app/actions.json
```

```json
{ "rules": [{ "pathPattern": "/actions/**", "apiPath": "/actions/**" }] }
```

The web app rewrites `/actions.json` and `/actions/*` to the API, so actions live on the main domain.

## GET: metadata

```bash
curl https://pixactions.app/actions/events/meetup-solana-sp-3f9a
```

```json
{
  "type": "action",
  "icon": "https://pixactions.app/opengraph-image",
  "title": "Meetup Solana SP",
  "description": "São Paulo, SP · 20/10/2026 22:00 UTC · R$ 20.00. Sem carteira? Pague com Pix em https://pixactions.app/e/meetup-solana-sp-3f9a",
  "label": "Comprar ingresso · 3.64 USDC",
  "disabled": false,
  "links": { "actions": [{ "type": "transaction", "label": "Comprar ingresso · 3.64 USDC", "href": "/actions/events/meetup-solana-sp-3f9a" }] },
  "error": null
}
```

When the event is sold out, `disabled` is `true` and `error.message` is `Esgotado`.

## POST: transaction

```bash
curl -X POST https://pixactions.app/actions/events/meetup-solana-sp-3f9a \
  -H "Content-Type: application/json" \
  -d '{"account": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"}'
```

```json
{ "type": "transaction", "transaction": "<base64>", "message": "Ingresso para Meetup Solana SP emitido na Solana!" }
```

The transaction is already signed by the API as fee payer; the wallet adds its signature and sends it. It contains, in order:

1. Outside production only: create the buyer's token account and mint one ticket's worth of mock USDC to it, so any devnet wallet can try the Blink.
2. Create the organizer and treasury token accounts if missing (idempotent).
3. `buy_ticket`: pays the organizer and the treasury fee, creates the ticket PDA.

## Headers and errors

Every Actions response carries:

| Header | Value |
|---|---|
| `X-Action-Version` | `2.4` |
| `X-Blockchain-Ids` | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (devnet) |
| `Access-Control-Allow-Origin` | `*` |

Errors follow the Actions spec, `{"message": "..."}`, instead of the API's usual error shape:

| Status | When |
|---|---|
| 400 | `account` is not a valid Solana address |
| 404 | Event not found or still a draft |
| 409 | Sold out |

## Try it

Open the event's `links.blink_url` (a dial.to link), connect a devnet wallet and buy. The ticket appears at `/t/<ticket pubkey>` like any Pix purchase.
