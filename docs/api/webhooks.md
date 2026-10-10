# Webhooks

Pix providers notify the API when a charge is paid. The webhook marks the order's Pix as paid; the next `GET /v1/orders/{id}` funds the buyer and issues the purchase transaction.

## Contract

```
POST /v1/webhooks/pix/{provider}
X-Pix-Signature: <hex HMAC-SHA256 of the raw body, keyed with PIX_WEBHOOK_SECRET>
Content-Type: application/json

{"charge_id": "MOCKC0FFEE001111422283"}
```

| Response | Meaning |
|---|---|
| `200 {"received": true, "order_id": "..."}` | Charge matched an order and was marked paid |
| `200 {"received": true, "order_id": null}` | Unknown charge; acknowledged so the provider stops retrying |
| `401 UNAUTHORIZED` | Signature missing or invalid |
| `404 NOT_FOUND` | `{provider}` is not the configured provider |
| `422 VALIDATION_ERROR` | Body is not JSON with `charge_id` |

The webhook is idempotent: delivering the same payment twice keeps the first payment time.

## Computing the signature

Python:

```python
import hashlib, hmac, json

body = json.dumps({"charge_id": "MOCKC0FFEE001111422283"}).encode()
signature = hmac.new(b"<PIX_WEBHOOK_SECRET>", body, hashlib.sha256).hexdigest()
```

curl:

```bash
BODY='{"charge_id":"MOCKC0FFEE001111422283"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$PIX_WEBHOOK_SECRET" | cut -d' ' -f2)
curl -X POST https://pixactions-api.vercel.app/v1/webhooks/pix/mock \
  -H "Content-Type: application/json" -H "X-Pix-Signature: $SIG" -d "$BODY"
```

## Plugging a real on-ramp

The sandbox uses `MockPixProvider`. A licensed on-ramp (for example BlindPay, Transfero or Bitso) plugs in by implementing the `PixProvider` protocol in `backend/pixactions_api/pix/base.py`:

| Method | Responsibility |
|---|---|
| `name` | Provider id used in the webhook path |
| `create_charge(order_id, amount_brl_cents, description)` | Create the Pix charge, return `charge_id`, `brcode`, `expires_at` |
| `is_paid(order)` | Fallback status check while polling |
| `parse_webhook(body, headers)` | Verify the provider's signature and return the paid `charge_id` |

In production the on-ramp also delivers the stablecoins to the buyer's wallet, replacing the mock mint done by the API.
