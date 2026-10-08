use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, TransferChecked};

declare_id!("DZ5ddra1TXhkbS9ZBnimtZPVeTxoXmxbCGvFHJqKVPa9");

pub const MAX_FEE_BPS: u16 = 1_000;

#[program]
pub mod pixactions {
    use super::*;

    pub fn initialize_config(ctx: Context<InitializeConfig>, fee_bps: u16, treasury: Pubkey) -> Result<()> {
        require!(fee_bps <= MAX_FEE_BPS, PixError::InvalidFee);
        let config = &mut ctx.accounts.config;
        config.admin = ctx.accounts.admin.key();
        config.fee_bps = fee_bps;
        config.treasury = treasury;
        config.bump = ctx.bumps.config;
        Ok(())
    }

    pub fn create_event(
        ctx: Context<CreateEvent>,
        event_id: u64,
        price: u64,
        capacity: u32,
        starts_at: i64,
        checkin_authority: Pubkey,
    ) -> Result<()> {
        require!(capacity > 0, PixError::InvalidCapacity);
        let event = &mut ctx.accounts.event;
        event.organizer = ctx.accounts.organizer.key();
        event.event_id = event_id;
        event.payment_mint = ctx.accounts.payment_mint.key();
        event.price = price;
        event.capacity = capacity;
        event.sold = 0;
        event.starts_at = starts_at;
        event.checkin_authority = checkin_authority;
        event.bump = ctx.bumps.event;
        Ok(())
    }

    pub fn buy_ticket(ctx: Context<BuyTicket>) -> Result<()> {
        let event_key = ctx.accounts.event.key();
        let (price, sold, capacity) = {
            let e = &ctx.accounts.event;
            (e.price, e.sold, e.capacity)
        };
        require!(sold < capacity, PixError::SoldOut);

        let fee = ((price as u128) * (ctx.accounts.config.fee_bps as u128) / 10_000) as u64;
        {
            let a = &ctx.accounts;
            let decimals = a.payment_mint.decimals;
            pay(&a.token_program, &a.buyer_token, &a.payment_mint, &a.organizer_token, &a.buyer, price - fee, decimals)?;
            if fee > 0 {
                pay(&a.token_program, &a.buyer_token, &a.payment_mint, &a.treasury_token, &a.buyer, fee, decimals)?;
            }
        }

        let ticket = &mut ctx.accounts.ticket;
        ticket.event = event_key;
        ticket.owner = ctx.accounts.buyer.key();
        ticket.serial = sold;
        ticket.checked_in = false;
        ticket.bump = ctx.bumps.ticket;
        ctx.accounts.event.sold = sold + 1;
        Ok(())
    }

    pub fn check_in(ctx: Context<CheckIn>) -> Result<()> {
        let ticket = &mut ctx.accounts.ticket;
        require!(!ticket.checked_in, PixError::AlreadyCheckedIn);
        ticket.checked_in = true;
        Ok(())
    }
}

fn pay<'info>(
    token_program: &Program<'info, Token>,
    from: &Account<'info, TokenAccount>,
    mint: &Account<'info, Mint>,
    to: &Account<'info, TokenAccount>,
    authority: &Signer<'info>,
    amount: u64,
    decimals: u8,
) -> Result<()> {
    token::transfer_checked(
        CpiContext::new(
            token_program.key(),
            TransferChecked {
                from: from.to_account_info(),
                mint: mint.to_account_info(),
                to: to.to_account_info(),
                authority: authority.to_account_info(),
            },
        ),
        amount,
        decimals,
    )
}

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    pub admin: Signer<'info>,
    #[account(init, payer = payer, space = 8 + Config::INIT_SPACE, seeds = [b"config"], bump)]
    pub config: Account<'info, Config>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(event_id: u64)]
pub struct CreateEvent<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    pub organizer: Signer<'info>,
    pub payment_mint: Account<'info, Mint>,
    #[account(
        init,
        payer = payer,
        space = 8 + Event::INIT_SPACE,
        seeds = [b"event", organizer.key().as_ref(), &event_id.to_le_bytes()],
        bump
    )]
    pub event: Account<'info, Event>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct BuyTicket<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    pub buyer: Signer<'info>,
    #[account(seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, Config>,
    #[account(
        mut,
        seeds = [b"event", event.organizer.as_ref(), &event.event_id.to_le_bytes()],
        bump = event.bump
    )]
    pub event: Account<'info, Event>,
    #[account(address = event.payment_mint @ PixError::MintMismatch)]
    pub payment_mint: Account<'info, Mint>,
    #[account(mut, token::mint = payment_mint, token::authority = buyer)]
    pub buyer_token: Account<'info, TokenAccount>,
    #[account(mut, token::mint = payment_mint, token::authority = event.organizer)]
    pub organizer_token: Account<'info, TokenAccount>,
    #[account(mut, token::mint = payment_mint, token::authority = config.treasury)]
    pub treasury_token: Account<'info, TokenAccount>,
    #[account(
        init,
        payer = payer,
        space = 8 + Ticket::INIT_SPACE,
        seeds = [b"ticket", event.key().as_ref(), &event.sold.to_le_bytes()],
        bump
    )]
    pub ticket: Account<'info, Ticket>,
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CheckIn<'info> {
    pub checkin_authority: Signer<'info>,
    #[account(has_one = checkin_authority @ PixError::Unauthorized)]
    pub event: Account<'info, Event>,
    #[account(mut, has_one = event)]
    pub ticket: Account<'info, Ticket>,
}

#[account]
#[derive(InitSpace)]
pub struct Config {
    pub admin: Pubkey,
    pub fee_bps: u16,
    pub treasury: Pubkey,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Event {
    pub organizer: Pubkey,
    pub event_id: u64,
    pub payment_mint: Pubkey,
    pub price: u64,
    pub capacity: u32,
    pub sold: u32,
    pub starts_at: i64,
    pub checkin_authority: Pubkey,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Ticket {
    pub event: Pubkey,
    pub owner: Pubkey,
    pub serial: u32,
    pub checked_in: bool,
    pub bump: u8,
}

#[error_code]
pub enum PixError {
    #[msg("Event is sold out")]
    SoldOut,
    #[msg("Ticket already checked in")]
    AlreadyCheckedIn,
    #[msg("Fee above the 10% maximum")]
    InvalidFee,
    #[msg("Capacity must be greater than zero")]
    InvalidCapacity,
    #[msg("Payment mint does not match the event")]
    MintMismatch,
    #[msg("Signer is not the event check-in authority")]
    Unauthorized,
}
