# Organizer flow

Organizers create an event, publish it onchain with one signature, share the checkout link and check tickets in at the door.

## 1. Create the event (draft)

```bash
curl -X POST https://api.pixactions.app/v1/events \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "title": "Meetup Solana SP",
    "description": "Primeiro meetup da comunidade.",
    "venue": "São Paulo, SP",
    "starts_at": "2026-10-20T22:00:00Z",
    "price_brl_cents": 2000,
    "capacity": 50,
    "wallet": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
  }'
```

The response is an `EventDraft`: the event in `draft` status plus `transaction`, the unsigned `create_event` transaction. The price is converted from BRL to payment-token units at creation (`price_token`, 6 decimals). The `wallet` becomes the onchain organizer: it receives payments and is the check-in authority.

## 2. Sign and publish

Sign `transaction` with the organizer wallet and submit:

```bash
curl -X POST https://api.pixactions.app/v1/events/$EVENT_ID/submit \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"transaction": "<base64 signed by the organizer wallet>"}'
```

The event becomes `live`. Submitting again once live is harmless and returns the event.

If signing took too long and the submit returns `TX_EXPIRED`, get a fresh transaction and try again:

```bash
curl -X POST https://api.pixactions.app/v1/events/$EVENT_ID/transaction -H "Authorization: Bearer $TOKEN"
```

## 3. Share

Every event carries three links:

| Field | Use |
|---|---|
| `links.checkout_url` | Pix checkout page. Share it on WhatsApp or Instagram. |
| `links.action_url` | Solana Action endpoint. |
| `links.blink_url` | dial.to link that renders the event as a Blink for wallet users. |

## 4. Follow sales

```bash
curl https://api.pixactions.app/v1/me/events -H "Authorization: Bearer $TOKEN"
curl https://api.pixactions.app/v1/events/$EVENT_ID/orders -H "Authorization: Bearer $TOKEN"
```

`sold` is read from the onchain counter, so it includes tickets bought through Blinks. Orders list buyers by wallet only; no personal data is exposed.

## 5. Check in at the door

The ticket QR encodes `https://<web>/t/<ticket pubkey>`. For each scanned ticket:

```bash
# Issue the check_in transaction (organizer only)
curl -X POST https://api.pixactions.app/v1/tickets/$TICKET/checkin -H "Authorization: Bearer $TOKEN"
```

The response has `transaction` (sign it with the organizer wallet) and `checkin_token` (send it back unchanged):

```bash
curl -X POST https://api.pixactions.app/v1/tickets/$TICKET/checkin/submit \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"transaction": "<base64 signed>", "checkin_token": "<from the previous call>"}'
```

The ticket is marked `checked_in` onchain. A second check-in of the same ticket returns `409 ALREADY_CHECKED_IN`, both from the API and from the program itself. Anyone can verify a ticket with `GET /v1/tickets/{pubkey}`.
