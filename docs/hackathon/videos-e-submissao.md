# Vídeos e submissão: Pix Actions

Prazo: 12/out/2026, 23h59 PT (13/out, 3h59 em Brasília). Meta: enviar até o fim da tarde de 12/out.

Os textos em inglês são para ler em voz alta ou colar no formulário. As notas em português (entre colchetes) são só para você.

---

## 1. Vídeo de pitch (até 3 min)

[Grave a tela + sua voz. Câmera no rosto no começo e no fim, se puder. Fale devagar: ~380 palavras cabem em 3 min. Ensaie a demo antes; use o evento Pix Actions Demo Night.]

**[0:00 a 0:20] Gancho (câmera)**
180 million Brazilians pay with Pix every day. Almost none of them can buy anything onchain. I'm Matheus, a builder from Brazil, and this is Pix Actions: pay with Pix, receive onchain.

**[0:20 a 0:50] Problema**
Pix moved 35 trillion reais last year. But to buy a ticket, a token or anything onchain, people still have to install a wallet, write down twelve words, open an exchange account, do KYC, buy crypto and withdraw it. Every step loses people. Solana Actions and Blinks made onchain actions shareable, but only for people who already have a wallet.

**[0:50 a 1:15] Solução**
Pix Actions turns any Solana action into a link paid with Pix. The buyer logs in with an email, pays a Pix QR code, and the asset lands in a non-custodial wallet created on the spot. The seller gets paid in the same transaction. Users never touch SOL. We start with event tickets.

**[1:15 a 2:15] Demo (tela)**
[Mostre, sem cortes longos:]
1. Dashboard: create an event in seconds. It is registered on Solana.
2. Share the link on WhatsApp. [Mostre a prévia com nome e preço.]
3. On the phone: open the link, log in with email, pay with Pix. [Sandbox: confirma sozinho. Não mostre sua caixa de e-mail, abas do navegador nem dashboards na gravação.]
4. The ticket appears with a QR code. [Clique em "Ver no Explorer" e mostre a conta na devnet.]
5. At the door: scan the QR. Entry allowed. Scan again: already used.

Narração sugerida: "No wallet install, no seed phrase, no exchange. Just Pix. The ticket is a Solana account, the organizer was paid in the same transaction, and check-in is recorded onchain, so a screenshot can't get in twice."

**[2:15 a 2:40] Por que agora e mercado**
Pix is the payment habit of a whole country, and Brazilians lost 29 billion reais to payment scams in a year. Tickets are our first wedge. The same rails work for subscriptions with Pix Automático, digital products, donations and any existing Solana Action. We charge a 1% fee per transaction, enforced by the program.

**[2:40 a 2:55] Primeiros usuários**
Our first users are Solana community events in Brazil and small producers who sell on WhatsApp today. Every event is also a standard Solana Action, so builders get a Pix checkout for free. The code is open source.

**[2:55 a 3:00] Fechamento (câmera)**
Pix Actions. Pay with Pix, receive onchain.

[Se tiver qualquer número real até a gravação (pessoas que compraram na demo, inscritos na lista de espera, conversas com organizadores), fale em 1 frase no bloco de primeiros usuários. Não invente número.]

---

## 2. Vídeo técnico (2 a 3 min)

[Tela com o README, o diagrama, trechos de código e o Explorer. Tom direto.]

**[0:00 a 0:20] Visão geral**
Pix Actions has three parts: an Anchor program on Solana, a FastAPI backend that builds transactions and runs the Pix rail, and a Next.js app where users log in with Privy embedded wallets. Everything is live on devnet and open source.

**[0:20 a 0:55] Programa on-chain**
[Mostre `onchain/programs/pixactions/src/lib.rs`.]
The program has four instructions. `create_event` creates an event PDA with price, capacity and a check-in authority. `buy_ticket` is atomic: it transfers the price to the organizer, a 1% fee to the treasury, creates a ticket PDA whose seed is the event's sold counter, and increments the counter. `check_in` flips a flag on the ticket, so a second check-in fails onchain. Nine Anchor tests cover payments, capacity, mint mismatch and check-in rules.

**[0:55 a 1:35] Build, sign, submit**
[Mostre `backend/pixactions_api/solana/tx.py` e o diagrama do checkout.]
Every write follows the same pattern. The API builds the transaction and is always the fee payer, so users never need SOL. The user's wallet signs. Before co-signing, the API checks that the signed message is byte for byte the one it issued, so nobody can make our fee payer sign something else. If two buyers race for the same ticket serial, the second transaction fails with "already in use" and the client simply signs a fresh one.

**[1:35 a 2:05] Pix e on-ramp**
[Mostre `backend/pixactions_api/pix/base.py`.]
Pix sits behind a provider interface. Today it's a sandbox that issues a real BR Code format and confirms automatically; a licensed on-ramp plugs in by implementing four methods. When the Pix is confirmed, stablecoins are delivered to the buyer's wallet and the purchase is signed. We designed it to settle domestically, in line with the Central Bank's 2026 rules for virtual asset providers.

**[2:05 a 2:30] Por que Solana**
Fee payer abstraction lets us hide crypto completely. Fees of a fraction of a cent make a 5 real ticket viable. Confirmation in seconds fits a checkout. And Solana Actions give us a distribution standard: every event is also a Blink, served from `actions.json` on our domain.

**[2:30 a 2:45] Qualidade e fechamento**
The API has 83 tests and an interactive reference at `/docs`, with guides for every flow. Pix Actions: pay with Pix, receive onchain.

---

## 3. Formulário de submissão (Colosseum)

**Project name:** Pix Actions

**One-liner (curto):** Pay with Pix, receive onchain: any Solana action as a link 180 million Brazilians can pay with Pix, no wallet setup.

**Description:**
Pix Actions turns Solana actions into payment links that anyone in Brazil can pay with Pix, the instant payment system used by about 180 million people. The buyer logs in with an email, pays a Pix QR code and receives the asset in a non-custodial embedded wallet created on the spot. The seller is paid in the same transaction. Users never hold SOL: our API is the fee payer and verifies every transaction it co-signs.

We start with event tickets: organizers create an event registered onchain, share the link on WhatsApp, Instagram or a printed QR code, sell with Pix and check tickets in at the door, with each check-in recorded onchain. Every event is also a standard Solana Action, so wallet users can buy from a Blink.

The same rails extend to subscriptions (Pix Automático), digital products, donations and a Pix checkout for any existing Solana Action. The demo runs on devnet with a sandbox Pix provider; a licensed on-ramp partner is the next step.

**Links:**
- Live demo: https://pixactions.vercel.app
- Demo event: https://pixactions.vercel.app/e/pix-actions-demo-night-0ed2
- GitHub: https://github.com/Matheus872/pixactions
- API docs: https://pixactions-api.vercel.app/docs
- Program (devnet): https://explorer.solana.com/address/DZ5ddra1TXhkbS9ZBnimtZPVeTxoXmxbCGvFHJqKVPa9?cluster=devnet
- Pitch video: [link do vídeo]
- Technical video: [link do vídeo]

**Track:** Solana (e marque a Trilha Brasil da Superteam no Superteam Earn com o mesmo projeto).

**Team:** Matheus (solo founder, full stack).

---

## 4. Tração rápida (você)

Mensagem para amigos e para o grupo do hackathon:

> Lancei o Pix Actions no hackathon da Solana: você paga com Pix e recebe um ingresso on-chain, sem instalar carteira. Me ajuda testando? Leva 1 minuto e não custa nada: o pagamento é simulado, então NÃO abra o app do banco, é só esperar uns segundos: https://pixactions.vercel.app/e/pix-actions-demo-night-0ed2
> Se curtir, entra na lista de espera: https://pixactions.vercel.app/#waitlist

Post no X (marque @colosseum e @SuperteamBR):

> Built Pix Actions for @colosseum World's Fair: pay with Pix, receive onchain. Buyers log in with email, pay a Pix QR code and get an onchain ticket on Solana, no wallet setup. Every event is also a Blink. Try the demo: https://pixactions.vercel.app #Solana @SuperteamBR
