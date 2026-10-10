export type Lang = "pt" | "en";

const pt = {
  nav: { how: "Como funciona", devs: "Developers", docs: "API", cta: "Criar evento" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Venda on-chain para 180 milhões de brasileiros.",
    accent: "Eles só precisam de Pix.",
    subtitle:
      "Pix Actions transforma qualquer ação na Solana, começando por ingressos, num link de WhatsApp pago com Pix. O comprador não instala carteira. O organizador recebe na hora.",
    primary: "Criar meu evento",
    secondary: "Ver demo",
    note: "Demo na Solana devnet · Pix em sandbox",
  },
  builtWith: "Construído com",
  problems: {
    title: "Cripto ainda pede demais de quem só quer pagar",
    subtitle:
      "Para comprar algo on-chain hoje é preciso instalar carteira, anotar 12 palavras, abrir conta em corretora, fazer KYC, comprar e sacar. Cada passo perde gente.",
    items: [
      { title: "Sem carteira para instalar", body: "Login só com e-mail. A carteira é criada na hora e não é custodial: nem a gente consegue mover seus fundos." },
      { title: "Organizador recebe na hora", body: "O pagamento cai na carteira do organizador na mesma transação que emite o ingresso. Sem esperar repasse." },
      { title: "Ingresso à prova de fraude", body: "Cada ingresso é uma conta na Solana e o check-in fica gravado on-chain. Print não entra duas vezes." },
    ],
  },
  steps: {
    title: "Como funciona",
    subtitle: "Do link no WhatsApp ao check-in na porta, em quatro passos.",
    items: [
      { title: "Crie o evento", body: "Defina preço em reais, data e lotação. O evento é registrado na Solana." },
      { title: "Compartilhe o link", body: "Mande no WhatsApp, Instagram ou onde quiser. A prévia mostra o evento e o preço." },
      { title: "O comprador paga com Pix", body: "QR ou copia e cola. O Pix vira stablecoin e a compra é assinada automaticamente." },
      { title: "Ingresso on-chain e check-in", body: "O ingresso aparece com QR. Na porta, você escaneia e o check-in fica gravado na Solana." },
    ],
  },
  devs: {
    title: "Para devs: um padrão aberto",
    body: "Cada evento é uma Solana Action: vira Blink no X para quem já tem carteira e checkout Pix para quem não tem. API documentada, programa e código abertos (MIT).",
    docs: "Docs da API",
    github: "Código no GitHub",
  },
  numbers: {
    title: "O tamanho da porta de entrada",
    items: [
      { value: "R$ 35,3 tri", label: "movimentados no Pix em 2025" },
      { value: "~180 mi", label: "brasileiros usam Pix" },
      { value: "R$ 29 bi", label: "perdidos em golpes de Pix e boleto entre jul/24 e jun/25" },
    ],
    sources: "Fontes: Banco Central via Let's Money (2025); Migalhas (2025).",
  },
  waitlist: {
    title: "Entre na lista",
    body: "Seja dos primeiros a vender com Pix Actions.",
    email: "seu@email.com",
    roles: { organizer: "Organizo eventos", buyer: "Quero comprar", developer: "Sou dev" },
    submit: "Quero participar",
    success: "Pronto! Você está na lista.",
    already: "Você já estava na lista 😉",
    error: "Não deu certo. Tente de novo.",
  },
  final: { title: "Seu próximo evento pode vender para todo o Brasil." },
  footer: { tagline: "Pague com Pix, receba on-chain.", built: "Feito para o Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export type LandingCopy = typeof pt;

const en: LandingCopy = {
  nav: { how: "How it works", devs: "Developers", docs: "API", cta: "Create event" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Sell onchain to 180 million Brazilians.",
    accent: "All they need is Pix.",
    subtitle:
      "Pix Actions turns any Solana action, starting with event tickets, into a WhatsApp link paid with Pix. Buyers install no wallet. Organizers get paid instantly.",
    primary: "Create my event",
    secondary: "See the demo",
    note: "Demo on Solana devnet · Pix sandbox",
  },
  builtWith: "Built with",
  problems: {
    title: "Crypto still asks too much of people who just want to pay",
    subtitle:
      "Buying anything onchain today means installing a wallet, writing down 12 words, opening an exchange account, doing KYC, buying and withdrawing. Every step loses people.",
    items: [
      { title: "No wallet to install", body: "Log in with just your email. A non-custodial wallet is created on the spot: not even we can move your funds." },
      { title: "Organizers get paid instantly", body: "Payment lands in the organizer's wallet in the same transaction that issues the ticket. No payout delays." },
      { title: "Fraud-proof tickets", body: "Every ticket is a Solana account and check-in is recorded onchain. A screenshot can't get in twice." },
    ],
  },
  steps: {
    title: "How it works",
    subtitle: "From a WhatsApp link to door check-in, in four steps.",
    items: [
      { title: "Create the event", body: "Set a BRL price, date and capacity. The event is registered on Solana." },
      { title: "Share the link", body: "Send it on WhatsApp, Instagram or anywhere. The preview shows the event and price." },
      { title: "Buyers pay with Pix", body: "QR or copy-paste. Pix becomes a stablecoin and the purchase is signed automatically." },
      { title: "Onchain ticket and check-in", body: "The ticket shows up with a QR. At the door you scan it and check-in is recorded on Solana." },
    ],
  },
  devs: {
    title: "For devs: an open standard",
    body: "Every event is a Solana Action: a Blink on X for wallet users and a Pix checkout for everyone else. Documented API, open program and code (MIT).",
    docs: "API docs",
    github: "Code on GitHub",
  },
  numbers: {
    title: "The size of the front door",
    items: [
      { value: "R$ 35.3T", label: "moved through Pix in 2025" },
      { value: "~180M", label: "Brazilians use Pix" },
      { value: "R$ 29B", label: "lost to Pix and boleto scams, Jul/24 to Jun/25" },
    ],
    sources: "Sources: Central Bank of Brazil via Let's Money (2025); Migalhas (2025).",
  },
  waitlist: {
    title: "Join the waitlist",
    body: "Be among the first to sell with Pix Actions.",
    email: "you@email.com",
    roles: { organizer: "I run events", buyer: "I want to buy", developer: "I'm a dev" },
    submit: "Count me in",
    success: "Done! You're on the list.",
    already: "You were already on the list 😉",
    error: "Something went wrong. Try again.",
  },
  final: { title: "Your next event can sell to all of Brazil." },
  footer: { tagline: "Pay with Pix, receive onchain.", built: "Built for the Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export const copy: Record<Lang, LandingCopy> = { pt, en };
