# Errors

Every error from the `/v1` API has the same shape:

```json
{
  "error": {
    "code": "SOLD_OUT",
    "message": "Event is sold out",
    "details": {}
  }
}
```

`code` is stable and safe to branch on; `message` is for humans and may change. Solana Actions routes are the exception: they return `{"message": "..."}` as the Actions spec requires (see [Solana Actions](solana-actions.md)).

## Codes

| Code | HTTP | When it happens | What the client should do |
|---|---|---|---|
| `UNAUTHORIZED` | 401 | Missing, invalid or expired Privy token; bad webhook signature | Refresh the token (`getAccessToken()`) or log in again |
| `NOT_FOUND` | 404 | Resource does not exist, is a draft, or belongs to someone else | Check the id; do not retry |
| `VALIDATION_ERROR` | 422 | Invalid body or parameters; `details.errors` lists each problem | Fix the request |
| `SOLD_OUT` | 409 | No tickets left | Stop and tell the buyer |
| `ORDER_NOT_FUNDED` | 409 | Submit called before the order reached `funded` | Keep polling `GET /v1/orders/{id}` |
| `TX_MISMATCH` | 400 | Signed transaction differs from the one issued, lacks a valid user signature, or the check-in token is invalid | Sign exactly the transaction the API returned |
| `TX_EXPIRED` | 409 | The transaction's blockhash expired | Fetch a fresh transaction (poll the order, or `POST /v1/events/{id}/transaction`) and sign again |
| `TX_STALE` | 409 | A concurrent purchase took the same ticket number | Poll the order for a fresh transaction and sign again |
| `ALREADY_CHECKED_IN` | 409 | The ticket was already used | Deny entry |
| `RPC_ERROR` | 502 | Solana RPC failure; `details.detail` has the raw message | Retry after a few seconds |

## Validation example

```bash
curl -X POST https://pixactions-api.vercel.app/v1/waitlist \
  -H "Content-Type: application/json" -d '{"email": "nope", "role": "organizer"}'
```

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": { "errors": [{ "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error" }] }
  }
}
```
