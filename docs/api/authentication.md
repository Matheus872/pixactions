# Authentication

Authenticated routes expect a Privy access token in the `Authorization` header. Privy handles login (email or SMS code) and creates the user's embedded Solana wallet; the API only verifies the token.

## Getting a token

In the web app, with the Privy React SDK:

```ts
import { usePrivy } from "@privy-io/react-auth";

const { getAccessToken } = usePrivy();
const token = await getAccessToken();

await fetch("https://pixactions-api.vercel.app/v1/me/events", {
  headers: { Authorization: `Bearer ${token}` },
});
```

## How the API verifies it

The token is a JWT signed with ES256. The API checks:

| Claim | Expected |
|---|---|
| signature | valid for one of the app's published keys (JWKS at `https://auth.privy.io/api/v1/apps/<app id>/jwks.json`, chosen by the token's `kid`); a fixed PEM in `PRIVY_VERIFICATION_KEY` overrides it |
| `iss` | `privy.io` |
| `aud` | the Privy app id (`PRIVY_APP_ID`) |
| `exp` | in the future |

The `sub` claim is the user's Privy DID (for example `did:privy:cm...`). It identifies the organizer or buyer for ownership checks.

## Wallet ownership

Requests that involve a wallet (`wallet` in `POST /v1/events` and `POST /v1/orders`) do not need a separate proof: every onchain write must be signed by that wallet, so a client can only act for a wallet it controls.

## What is stored, and what never goes onchain

| Data | Where |
|---|---|
| Email or phone number | Privy only. The API never receives it. |
| Privy DID | API database, to link events and orders to their owner. |
| Wallet address | API database and onchain (ticket owner, event organizer). |
| Personal data | Never onchain. Tickets reference a wallet, not a person. |

Embedded wallets are non-custodial: the key is split into shares and neither Pix Actions nor Privy can move user funds alone.

## Errors

A missing, malformed or expired token returns `401`:

```bash
curl -X POST https://pixactions-api.vercel.app/v1/events -H "Content-Type: application/json" -d '{}'
```

```json
{ "error": { "code": "UNAUTHORIZED", "message": "Missing bearer token", "details": {} } }
```

Accessing a resource that belongs to another user returns `404 NOT_FOUND`, never `403`, so the API does not reveal that the resource exists.
