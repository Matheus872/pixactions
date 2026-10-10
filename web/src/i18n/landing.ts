export type Lang = "pt" | "en";

const pt = {
  nav: { how: "Como funciona", devs: "Developers", docs: "API", cta: "Começar a vender" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Venda on-chain para 180 milhões de brasileiros.",
    accent: "Eles só precisam de Pix.",
    subtitle:
      "Pix Actions transforma qualquer ação na Solana (ingressos, assinaturas, produtos digitais, doações e tokens) num link pago com Pix que funciona em qualquer lugar: WhatsApp, Instagram, site ou QR code impresso. O comprador não instala carteira. Quem vende recebe na hora.",
    primary: "Começar a vender",
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
      { title: "Quem vende recebe na hora", body: "O pagamento cai na carteira de quem vende na mesma transação que entrega o que foi comprado. Sem esperar repasse." },
      { title: "À prova de fraude", body: "Cada compra é registrada na Solana: comprovante falso não passa e um ingresso não entra duas vezes." },
    ],
  },
  steps: {
    title: "Como funciona",
    subtitle: "Do link à entrega on-chain, em quatro passos.",
    items: [
      { title: "Crie sua ação", body: "Ingresso, assinatura, produto digital, doação ou token: defina o preço em reais e tudo fica registrado na Solana." },
      { title: "Compartilhe o link", body: "Mande no WhatsApp, poste no Instagram, coloque no seu site ou imprima o QR code. A prévia mostra o que você vende e o preço." },
      { title: "O comprador paga com Pix", body: "QR ou copia e cola. O Pix vira stablecoin e a compra é assinada automaticamente." },
      { title: "Entrega on-chain", body: "O que foi comprado cai na carteira de quem pagou, com comprovante público. Ingressos ainda têm check-in na porta." },
    ],
  },
  devs: {
    title: "Para devs: um padrão aberto",
    body: "Cada ação é uma Solana Action: vira Blink no X para quem já tem carteira e checkout Pix para quem não tem. API documentada, programa e código abertos (MIT).",
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
    roles: { organizer: "Quero vender", buyer: "Quero comprar", developer: "Sou dev" },
    submit: "Quero participar",
    success: "Pronto! Você está na lista.",
    already: "Você já estava na lista 😉",
    error: "Não deu certo. Tente de novo.",
  },
  final: { title: "O que você vende pode chegar a todo o Brasil." },
  footer: { tagline: "Pague com Pix, receba on-chain.", built: "Feito para o Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export type LandingCopy = typeof pt;

const en: LandingCopy = {
  nav: { how: "How it works", devs: "Developers", docs: "API", cta: "Start selling" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Sell onchain to 180 million Brazilians.",
    accent: "All they need is Pix.",
    subtitle:
      "Pix Actions turns any Solana action (tickets, subscriptions, digital products, donations and tokens) into a link paid with Pix that works anywhere: WhatsApp, Instagram, a website or a printed QR code. Buyers install no wallet. Sellers get paid instantly.",
    primary: "Start selling",
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
      { title: "Sellers get paid instantly", body: "Payment lands in the seller's wallet in the same transaction that delivers what was bought. No payout delays." },
      { title: "Fraud-proof", body: "Every purchase is recorded on Solana: fake receipts don't get through and a ticket can't get in twice." },
    ],
  },
  steps: {
    title: "How it works",
    subtitle: "From a link to onchain delivery, in four steps.",
    items: [
      { title: "Create your action", body: "Ticket, subscription, digital product, donation or token: set a BRL price and everything is recorded on Solana." },
      { title: "Share the link", body: "Send it on WhatsApp, post it on Instagram, put it on your website or print the QR code. The preview shows what you sell and the price." },
      { title: "Buyers pay with Pix", body: "QR or copy-paste. Pix becomes a stablecoin and the purchase is signed automatically." },
      { title: "Onchain delivery", body: "What was bought lands in the buyer's wallet with a public receipt. Tickets also get check-in at the door." },
    ],
  },
  devs: {
    title: "For devs: an open standard",
    body: "Every action is a Solana Action: a Blink on X for wallet users and a Pix checkout for everyone else. Documented API, open program and code (MIT).",
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
    roles: { organizer: "I want to sell", buyer: "I want to buy", developer: "I'm a dev" },
    submit: "Count me in",
    success: "Done! You're on the list.",
    already: "You were already on the list 😉",
    error: "Something went wrong. Try again.",
  },
  final: { title: "What you sell can reach all of Brazil." },
  footer: { tagline: "Pay with Pix, receive onchain.", built: "Built for the Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export const copy: Record<Lang, LandingCopy> = { pt, en };
