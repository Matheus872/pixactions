import * as anchor from "@anchor-lang/core";
import { BN, Program } from "@anchor-lang/core";
import { Pixactions } from "../target/types/pixactions";
import {
  createAssociatedTokenAccount,
  createMint,
  getAccount,
  mintTo,
  TOKEN_PROGRAM_ID,
} from "@solana/spl-token";
import { ComputeBudgetProgram, Keypair, PublicKey, SystemProgram } from "@solana/web3.js";
import { assert } from "chai";

describe("pixactions", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  const program = anchor.workspace.pixactions as Program<Pixactions>;
  const conn = provider.connection;
  const payer = (provider.wallet as anchor.Wallet).payer;

  const admin = Keypair.generate();
  const treasury = Keypair.generate();
  const organizer = Keypair.generate();
  const buyer = Keypair.generate();
  const PRICE = new BN(3_636_364);
  const FEE = 36_363; // 1% de PRICE, arredondado para baixo

  let mint: PublicKey;
  let otherMint: PublicKey;
  let buyerToken: PublicKey;
  let organizerToken: PublicKey;
  let treasuryToken: PublicKey;

  const pda = (seeds: Buffer[]) => PublicKey.findProgramAddressSync(seeds, program.programId)[0];
  const configPda = pda([Buffer.from("config")]);
  const eventPda = (id: BN) =>
    pda([Buffer.from("event"), organizer.publicKey.toBuffer(), id.toArrayLike(Buffer, "le", 8)]);
  const ticketPda = (event: PublicKey, serial: number) => {
    const b = Buffer.alloc(4);
    b.writeUInt32LE(serial);
    return pda([Buffer.from("ticket"), event.toBuffer(), b]);
  };

  async function expectError(p: Promise<unknown>, code: string) {
    try {
      await p;
    } catch (e: any) {
      const got = e?.error?.errorCode?.code ?? String(e);
      assert.include(got, code);
      return;
    }
    assert.fail(`expected error ${code}`);
  }

  const createEvent = (id: BN, capacity: number) =>
    program.methods
      .createEvent(id, PRICE, capacity, new BN(Math.floor(Date.now() / 1000) + 86_400), organizer.publicKey)
      .accountsPartial({
        payer: payer.publicKey,
        organizer: organizer.publicKey,
        paymentMint: mint,
        event: eventPda(id),
        systemProgram: SystemProgram.programId,
      })
      .signers([organizer])
      .rpc();

  const buy = (event: PublicKey, serial: number, paymentMint: PublicKey = mint) =>
    program.methods
      .buyTicket()
      .accountsPartial({
        payer: payer.publicKey,
        buyer: buyer.publicKey,
        config: configPda,
        event,
        paymentMint,
        buyerToken,
        organizerToken,
        treasuryToken,
        ticket: ticketPda(event, serial),
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([buyer])
      .rpc();

  const checkIn = (signer: Keypair, event: PublicKey, ticket: PublicKey, cuLimit = 200_000) =>
    program.methods
      .checkIn()
      .accountsPartial({ checkinAuthority: signer.publicKey, event, ticket })
      .preInstructions([ComputeBudgetProgram.setComputeUnitLimit({ units: cuLimit })])
      .signers([signer])
      .rpc();

  before(async () => {
    mint = await createMint(conn, payer, payer.publicKey, null, 6);
    otherMint = await createMint(conn, payer, payer.publicKey, null, 6);
    buyerToken = await createAssociatedTokenAccount(conn, payer, mint, buyer.publicKey);
    organizerToken = await createAssociatedTokenAccount(conn, payer, mint, organizer.publicKey);
    treasuryToken = await createAssociatedTokenAccount(conn, payer, mint, treasury.publicKey);
    await mintTo(conn, payer, mint, buyerToken, payer, 100_000_000);
  });

  it("rejects a fee above 10%", async () => {
    await expectError(
      program.methods
        .initializeConfig(1001, treasury.publicKey)
        .accountsPartial({ payer: payer.publicKey, admin: admin.publicKey, config: configPda, systemProgram: SystemProgram.programId })
        .signers([admin])
        .rpc(),
      "InvalidFee",
    );
  });

  it("initializes config", async () => {
    await program.methods
      .initializeConfig(100, treasury.publicKey)
      .accountsPartial({ payer: payer.publicKey, admin: admin.publicKey, config: configPda, systemProgram: SystemProgram.programId })
      .signers([admin])
      .rpc();
    const cfg = await program.account.config.fetch(configPda);
    assert.equal(cfg.feeBps, 100);
    assert.ok(cfg.treasury.equals(treasury.publicKey));
    assert.ok(cfg.admin.equals(admin.publicKey));
  });

  it("rejects zero capacity", async () => {
    await expectError(createEvent(new BN(99), 0), "InvalidCapacity");
  });

  it("creates an event", async () => {
    await createEvent(new BN(1), 2);
    const ev = await program.account.event.fetch(eventPda(new BN(1)));
    assert.equal(ev.sold, 0);
    assert.equal(ev.capacity, 2);
    assert.ok(ev.price.eq(PRICE));
    assert.ok(ev.organizer.equals(organizer.publicKey));
    assert.ok(ev.paymentMint.equals(mint));
    assert.ok(ev.checkinAuthority.equals(organizer.publicKey));
  });

  it("sells a ticket and splits the payment", async () => {
    const ev = eventPda(new BN(1));
    await buy(ev, 0);
    assert.equal(Number((await getAccount(conn, organizerToken)).amount), PRICE.toNumber() - FEE);
    assert.equal(Number((await getAccount(conn, treasuryToken)).amount), FEE);
    assert.equal(Number((await getAccount(conn, buyerToken)).amount), 100_000_000 - PRICE.toNumber());
    const t = await program.account.ticket.fetch(ticketPda(ev, 0));
    assert.ok(t.owner.equals(buyer.publicKey));
    assert.ok(t.event.equals(ev));
    assert.equal(t.serial, 0);
    assert.isFalse(t.checkedIn);
    assert.equal((await program.account.event.fetch(ev)).sold, 1);
  });

  it("enforces capacity", async () => {
    const ev = eventPda(new BN(1));
    await buy(ev, 1);
    await expectError(buy(ev, 2), "SoldOut");
  });

  it("rejects a payment mint different from the event's", async () => {
    await createEvent(new BN(2), 5);
    await expectError(buy(eventPda(new BN(2)), 0, otherMint), "MintMismatch");
  });

  it("checks a ticket in exactly once", async () => {
    const ev = eventPda(new BN(1));
    const t = ticketPda(ev, 0);
    await checkIn(organizer, ev, t);
    assert.isTrue((await program.account.ticket.fetch(t)).checkedIn);
    await expectError(checkIn(organizer, ev, t, 200_001), "AlreadyCheckedIn");
  });

  it("rejects a stranger at the door", async () => {
    const ev = eventPda(new BN(1));
    await expectError(checkIn(Keypair.generate(), ev, ticketPda(ev, 1)), "Unauthorized");
  });
});
