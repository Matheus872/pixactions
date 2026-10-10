export type Lang = "pt" | "en";

export type UseCaseId = "tickets" | "subscriptions" | "tokens" | "donations" | "digital" | "anyAction";

const pt = {
  nav: { how: "Como funciona", useCases: "Casos de uso", devs: "Developers", docs: "API", cta: "Começar" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Qualquer ação na Solana,",
    accent: "paga com Pix.",
    tagline: "Pagamentos do agora. Para um mundo sem fronteiras.",
    subtitle:
      "Pix Actions transforma ingressos, assinaturas, tokens e qualquer Solana Action num link de WhatsApp pago com Pix. Quem compra não instala carteira. Quem vende recebe na hora.",
    primary: "Criar minha ação",
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
      { title: "Quem vende recebe na hora", body: "O pagamento cai na carteira de quem vende na mesma transação que entrega o ativo. Sem esperar repasse." },
      { title: "Tudo verificável on-chain", body: "Cada compra fica registrada na Solana. Comprovante falso e ingresso duplicado não passam." },
    ],
  },
  useCases: {
    title: "O que dá para vender com um link",
    subtitle: "Começamos por ingressos. A mesma infraestrutura serve para qualquer ação na Solana.",
    live: "Ao vivo na demo",
    soon: "Em breve",
    items: {
      tickets: { title: "Ingressos", body: "Venda pelo WhatsApp, ingresso on-chain na carteira e check-in na porta." },
      subscriptions: { title: "Assinaturas", body: "Clubes, comunidades e conteúdo recorrente cobrados via Pix Automático." },
      tokens: { title: "Tokens e colecionáveis", body: "O token de uma comunidade ou um colecionável, comprado com Pix." },
      donations: { title: "Doações", body: "Campanhas com destino do dinheiro rastreável on-chain." },
      digital: { title: "Produtos digitais", body: "Cursos, arquivos e acessos entregues na hora da compra." },
      anyAction: { title: "Qualquer Solana Action", body: "Cole a URL de uma Action existente e ganhe um checkout Pix para ela." },
    } satisfies Record<UseCaseId, { title: string; body: string }>,
  },
  steps: {
    title: "Como funciona",
    subtitle: "Do link no WhatsApp ao ativo na carteira, em quatro passos.",
    items: [
      { title: "Crie a ação", body: "Defina o que vende e o preço em reais. A ação é registrada na Solana." },
      { title: "Compartilhe o link", body: "Mande no WhatsApp, Instagram ou onde quiser. A prévia mostra o produto e o preço." },
      { title: "Quem compra paga com Pix", body: "QR ou copia e cola. O Pix vira stablecoin e a compra é assinada automaticamente." },
      { title: "Entrega on-chain", body: "O ativo cai na carteira de quem comprou, com comprovante público. Ingressos ainda têm check-in na porta." },
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
  final: { title: "Seu próximo produto pode vender para todo o Brasil." },
  footer: { built: "Feito para o Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export type LandingCopy = typeof pt;

const en: LandingCopy = {
  nav: { how: "How it works", useCases: "Use cases", devs: "Developers", docs: "API", cta: "Get started" },
  hero: {
    badge: "Solana · Pix · Open-source",
    title: "Any action on Solana,",
    accent: "paid with Pix.",
    tagline: "Payments for right now. For a world without borders.",
    subtitle:
      "Pix Actions turns tickets, subscriptions, tokens and any Solana Action into a WhatsApp link paid with Pix. Buyers install no wallet. Sellers get paid instantly.",
    primary: "Create my action",
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
      { title: "Sellers get paid instantly", body: "Payment lands in the seller's wallet in the same transaction that delivers the asset. No payout delays." },
      { title: "Everything verifiable onchain", body: "Every purchase is recorded on Solana. Fake receipts and duplicate tickets don't get through." },
    ],
  },
  useCases: {
    title: "What you can sell with a link",
    subtitle: "We start with tickets. The same rails work for any action on Solana.",
    live: "Live in the demo",
    soon: "Coming soon",
    items: {
      tickets: { title: "Tickets", body: "Sell on WhatsApp, onchain ticket in the wallet and check-in at the door." },
      subscriptions: { title: "Subscriptions", body: "Clubs, communities and recurring content charged via Pix Automático." },
      tokens: { title: "Tokens and collectibles", body: "A community token or a collectible, bought with Pix." },
      donations: { title: "Donations", body: "Campaigns where the destination of every real is traceable onchain." },
      digital: { title: "Digital products", body: "Courses, files and access delivered the moment the payment clears." },
      anyAction: { title: "Any Solana Action", body: "Paste the URL of an existing Action and get a Pix checkout for it." },
    },
  },
  steps: {
    title: "How it works",
    subtitle: "From a WhatsApp link to the asset in the wallet, in four steps.",
    items: [
      { title: "Create the action", body: "Choose what you sell and set a BRL price. The action is registered on Solana." },
      { title: "Share the link", body: "Send it on WhatsApp, Instagram or anywhere. The preview shows the product and price." },
      { title: "Buyers pay with Pix", body: "QR or copy-paste. Pix becomes a stablecoin and the purchase is signed automatically." },
      { title: "Onchain delivery", body: "The asset lands in the buyer's wallet with a public receipt. Tickets also get check-in at the door." },
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
  final: { title: "Your next product can sell to all of Brazil." },
  footer: { built: "Built for the Colosseum Crypto World's Fair", license: "Open-source · MIT", network: "Solana devnet" },
};

export const copy: Record<Lang, LandingCopy> = { pt, en };
