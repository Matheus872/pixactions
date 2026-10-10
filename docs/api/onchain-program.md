# Onchain program

The `pixactions` Anchor program holds the source of truth: events, ticket counters, tickets and check-ins. The API builds transactions for it; anyone can verify its state on the explorer.

| Item | Value |
|---|---|
| Program id (devnet) | `DZ5ddra1TXhkbS9ZBnimtZPVeTxoXmxbCGvFHJqKVPa9` |
| Framework | Anchor 1.2 |
| Source | [`onchain/programs/pixactions/src/lib.rs`](../../onchain/programs/pixactions/src/lib.rs) |
| IDL | [`backend/pixactions_api/solana/idl/pixactions.json`](../../backend/pixactions_api/solana/idl/pixactions.json) |

## Accounts (PDAs)

| Account | Seeds | Fields |
|---|---|---|
| `Config` | `["config"]` | `admin: Pubkey`, `fee_bps: u16`, `treasury: Pubkey`, `bump: u8` |
| `Event` | `["event", organizer, event_id as u64 little endian]` | `organizer: Pubkey`, `event_id: u64`, `payment_mint: Pubkey`, `price: u64`, `capacity: u32`, `sold: u32`, `starts_at: i64`, `checkin_authority: Pubkey`, `bump: u8` |
| `Ticket` | `["ticket", event, serial as u32 little endian]` | `event: Pubkey`, `owner: Pubkey`, `serial: u32`, `checked_in: bool`, `bump: u8` |

Each account starts with Anchor's 8 byte discriminator (`sha256("account:<Name>")[..8]`).

## Instructions

| Instruction | Args | Accounts (in order) | Signers | Effect |
|---|---|---|---|---|
| `initialize_config` | `fee_bps: u16`, `treasury: Pubkey` | payer, admin, config, system_program | payer, admin | Creates `Config` once |
| `create_event` | `event_id: u64`, `price: u64`, `capacity: u32`, `starts_at: i64`, `checkin_authority: Pubkey` | payer, organizer, payment_mint, event, system_program | payer, organizer | Creates `Event` with `sold = 0` |
| `buy_ticket` | none | payer, buyer, config, event, payment_mint, buyer_token, organizer_token, treasury_token, ticket, token_program, system_program | payer, buyer | Atomically pays the organizer and the fee, creates `Ticket` with `serial = sold`, increments `sold` |
| `check_in` | none | checkin_authority, event, ticket | checkin_authority | Marks the ticket `checked_in` |

## Fee

`fee = price * fee_bps / 10_000`, rounded down. The organizer receives `price - fee`, the treasury receives `fee`, in the same transaction. The demo uses `fee_bps = 100` (1%); the program rejects values above 1000 (10%).

## Errors

| Code | Name | Meaning |
|---|---|---|
| 6000 | `SoldOut` | `sold` reached `capacity` |
| 6001 | `AlreadyCheckedIn` | The ticket was already used |
| 6002 | `InvalidFee` | `fee_bps` above 1000 |
| 6003 | `InvalidCapacity` | `capacity` is zero |
| 6004 | `MintMismatch` | Payment mint differs from the event's |
| 6005 | `Unauthorized` | Signer is not the event's check-in authority |

The API maps 6000 and 6001 to `SOLD_OUT` and `ALREADY_CHECKED_IN`.

## Why the API is always the payer

Every instruction takes a separate `payer` that funds rent and fees. The API's service wallet fills that role, so buyers and organizers only sign for what they own (their tokens, their event) and never need SOL. A ticket's serial comes from the event's `sold` counter at build time; if two purchases race for the same serial, the second fails onchain with Anchor's `ConstraintSeeds` (2006, the ticket PDA no longer matches the new counter) and the API returns `TX_STALE` so the client signs a fresh transaction.
