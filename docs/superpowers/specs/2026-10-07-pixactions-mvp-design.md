# Pix Actions: design do MVP (Colosseum World's Fair)

- **Data:** 07/out/2026
- **Autor:** Matheus, com Claude
- **Status:** aprovado (08/out/2026)
- **Prazo de submissão:** 12/out/2026 às 23h59 PT (13/out às 3h59 em Brasília)

## 1. Objetivo

**Qualquer pessoa paga com Pix e recebe um ativo on-chain na Solana, sem instalar carteira. O organizador recebe na hora.**

O primeiro caso de uso são **ingressos de eventos**. O mesmo evento também é uma Solana Action, então funciona como Blink para quem já tem carteira.

**Posicionamento para o júri:** "Blinks levam a Solana para o feed; o Pix Actions leva a Solana para os 180 milhões de brasileiros que só têm Pix."

### Critérios de sucesso

1. O fluxo completo funciona na **devnet**, num deploy público (não em localhost): criar evento → link → login por e-mail → Pix → ingresso on-chain → check-in.
2. A demo nunca quebra: o Pix simulado é determinístico.
3. A landing page está publicada e capta inscrições na lista de espera (métrica de tração).
4. A API tem documentação de referência (OpenAPI) mais guias de fluxo.
5. O repositório GitHub é público (open-source, licença MIT), com README, para o vídeo técnico e para concorrer ao prêmio Public Good.

### Fora de escopo (roadmap do pitch)

- Ingresso como NFT colecionável; revenda com teto e royalty.
- Pix real em produção; saque do organizador para Pix (off-ramp).
- Assinaturas (Pix Automático + Subscriptions & Allowances da Solana).
- Checkout para Actions de terceiros; SDK publicado no npm.
- Prova de posse do ingresso no check-in (assinatura do dono). No MVP, o QR contém o endereço do ingresso, e o check-in on-chain impede o reuso.

**Stretch (só se sobrar tempo):** BlindPay em modo de desenvolvimento como segundo `PixProvider`.

## 2. Arquitetura

```
pixactions/
├── programs/pixactions/   Programa Anchor (Rust), testes com LiteSVM
├── backend/               FastAPI (Python 3.12, uv), pytest
├── web/                   Next.js (TypeScript, Tailwind): landing, checkout, painel, check-in
└── docs/                  specs, guias de API, tração
```

```
Comprador/Organizador (navegador)
   │  Privy (login por e-mail/SMS, carteira Solana embutida, assina transações)
   ▼
web (Next.js, Vercel) ──HTTP/JSON──► backend (FastAPI, Vercel Python)
                                       ├── Postgres (Neon): eventos, pedidos, lista de espera
                                       ├── PixProvider: MockPixProvider (padrão) | BlindPay (stretch)
                                       └── Solana RPC (devnet): monta transações, paga o gas, envia
                                                 ▼
                                       Programa pixactions (devnet)
```

**Princípios:**
- **A verdade fica on-chain** (evento, lotação, ingresso, check-in). O banco guarda o estado do pagamento e serve de cache para leitura.
- **Não custodial:** o backend nunca tem a chave do usuário. O backend só assina como *fee payer* (gas) e como "on-ramp simulado" (mint de token de teste).
- **Um padrão único de transação:** o backend **monta** a transação, o cliente **assina** com a Privy e o backend **confere e envia**.

## 3. Programa on-chain (Anchor)

**Moeda de pagamento:** cada evento guarda o próprio `payment_mint` (qualquer token SPL). A demo usa um **mock de USDC na devnet** (mint nosso, 6 casas decimais). Em produção, a recomendação é uma stablecoin de real (BRZ/BRLA), para evitar câmbio via cripto (Res. BCB 561). Isso entra como argumento no pitch.

### Contas (PDAs)

| Conta | Seeds | Campos |
|---|---|---|
| `Config` | `["config"]` | `admin: Pubkey`, `fee_bps: u16`, `treasury: Pubkey`, `bump` |
| `Event` | `["event", organizer, event_id: u64 LE]` | `organizer`, `event_id`, `payment_mint`, `price: u64`, `capacity: u32`, `sold: u32`, `starts_at: i64`, `checkin_authority: Pubkey`, `bump` |
| `Ticket` | `["ticket", event, serial: u32 LE]` | `event`, `owner`, `serial`, `checked_in: bool`, `bump` |

### Instruções

| Instrução | Quem assina | Efeito |
|---|---|---|
| `initialize_config(fee_bps, treasury)` | admin + payer | Cria o `Config`. Uma vez só |
| `create_event(event_id, price, capacity, starts_at, checkin_authority)` | organizer + payer | Cria o `Event` com `sold = 0` |
| `buy_ticket()` | buyer + payer | Exige `sold < capacity`. Transfere `price − fee` do ATA do comprador para o ATA do organizador e `fee` para o ATA do tesouro. Cria o `Ticket` com `serial = sold` e incrementa `sold`. Tudo de forma atômica |
| `check_in()` | `checkin_authority` | Exige `!checked_in` e marca `checked_in = true` |

- `fee = price × fee_bps / 10_000`, arredondado para baixo. A demo usa `fee_bps = 100` (1%).
- O `payer` (fee payer e rent) é sempre a carteira de serviço do backend. O usuário nunca precisa de SOL.
- **Erros:** `SoldOut`, `AlreadyCheckedIn`, `InvalidFee` (`fee_bps > 1000`), `InvalidCapacity` (`capacity = 0`), `MintMismatch`.

### Testes (Rust + LiteSVM)

- Compra feliz: saldos corretos para organizador, tesouro e comprador; `sold` incrementado; `Ticket` criado.
- Lotação esgotada falha com `SoldOut`.
- Check-in duplo falha com `AlreadyCheckedIn`.
- Check-in com assinante errado falha.
- Pagamento com mint diferente falha com `MintMismatch`.

## 4. Backend (FastAPI)

**Stack:** Python 3.12, uv, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + Alembic, asyncpg (Neon), `solders` + `solana-py` (RPC), PyJWT (validação do token da Privy), `qrcode` (QR do Pix), pytest + httpx, ruff.

### Autenticação

- O cliente envia `Authorization: Bearer <privy access token>`.
- O backend valida o JWT (ES256) com a chave de verificação do app na Privy e extrai o `privy_did`.
- A carteira Solana do usuário vem no corpo da requisição e é **conferida** contra as carteiras vinculadas ao usuário via API da Privy, com cache curto.
- **Privacidade:** o banco guarda só `privy_did` e o endereço da carteira. E-mail e telefone ficam na Privy. **Nenhum dado pessoal vai para a cadeia.**

### Modelo de dados (Postgres)

- `events`: `id (uuid)`, `slug`, `onchain_pubkey`, `event_id (u64)`, `organizer_did`, `organizer_wallet`, `title`, `description`, `image_url`, `venue`, `starts_at`, `price_brl_cents`, `price_token (u64)`, `payment_mint`, `capacity`, `status (draft|live)`, `create_tx_message_hash`, `created_at`.
- `orders`: `id (uuid)`, `event_id`, `buyer_did`, `buyer_wallet`, `amount_brl_cents`, `amount_token`, `status`, `pix_provider`, `pix_charge_id`, `pix_brcode`, `pix_expires_at`, `funding_tx_sig`, `buy_tx_message_hash`, `buy_tx_sig`, `ticket_pubkey`, `error`, timestamps.
- `waitlist`: `id`, `email (único)`, `role (organizer|buyer|developer)`, `lang`, `created_at`.

### Máquina de estados do pedido

```
pending_payment ──(Pix confirmado)──► paid ──(on-ramp entrega tokens)──► funded
funded ──(cliente assina, backend envia e confirma)──► confirmed
qualquer estado ──(erro)──► failed     pending_payment ──(expirou)──► expired
```

- **Fluxo do Pix:** o comprador paga o Pix, o on-ramp converte e entrega o token na carteira do comprador (`funded`), e a carteira do comprador assina `buy_ticket`. Esse é o modelo de produção (on-ramp → carteira do usuário), e o mock o reproduz fielmente.
- **`MockPixProvider`:** gera um BR Code no formato "copia e cola" (com payload marcado como simulação) e o QR. A confirmação é **preguiçosa**: no `GET` do pedido, se passaram `MOCK_PIX_AUTOPAY_SECONDS` (padrão 8 s), o pedido passa a `paid`. Há também o endpoint `POST /v1/dev/orders/{id}/simulate-payment`, ativo só quando `ENV != production`. Funciona em serverless, sem worker em segundo plano.
- **On-ramp simulado:** em `paid`, a carteira de serviço faz o mint de `amount_token` do mock de USDC no ATA do comprador (criando o ATA, se preciso). O pedido vai para `funded` e guarda `funding_tx_sig`.
- **Conversão BRL → token:** taxa fixa configurável `MOCK_BRL_PER_USD` (padrão 5,50). O preço on-chain é gravado na criação do evento.

### Segurança do fee payer

- O backend monta a mensagem da transação e guarda o `sha256` dela no pedido ou evento.
- No envio, o backend confere que a mensagem assinada pelo cliente tem **exatamente** esse hash. Só então adiciona a própria assinatura e envia.
- Isso impede que um cliente altere a transação para gastar a carteira de serviço.
- A mensagem expira junto com o blockhash. Nesse caso, o backend remonta a transação no próximo `GET`.

### Endpoints (`/v1`)

| Método e rota | Auth | Descrição |
|---|---|---|
| `GET /health` | não | Status, versão, cluster e program id |
| `POST /v1/waitlist` | não | Inscrição na lista de espera (idempotente por e-mail) |
| `GET /v1/events/{slug}` | não | Dados públicos do evento e vagas restantes (lidas on-chain, com cache) |
| `POST /v1/events` | organizador | Cria o rascunho e devolve `transaction` (base64) de `create_event` para assinar |
| `POST /v1/events/{id}/submit` | organizador | Recebe a transação assinada, confere o hash, envia e marca o evento como `live` |
| `GET /v1/me/events` | organizador | Eventos do organizador, com vendas |
| `GET /v1/events/{id}/orders` | organizador | Pedidos do evento (sem dados pessoais) |
| `POST /v1/orders` | comprador | `{event_slug, wallet}` → cria o pedido e a cobrança Pix (`brcode`, `qr_png_base64`, `expires_at`) |
| `GET /v1/orders/{id}` | comprador | Status do pedido. Em `funded`, inclui `transaction` de `buy_ticket` para assinar |
| `POST /v1/orders/{id}/submit` | comprador | Recebe a transação assinada, confere, envia e confirma; devolve o ingresso |
| `GET /v1/tickets/{pubkey}` | não | Estado on-chain do ingresso (evento, dono, `checked_in`) e link do explorer |
| `POST /v1/tickets/{pubkey}/checkin` | organizador | Devolve a transação de `check_in` para a `checkin_authority` assinar |
| `POST /v1/tickets/{pubkey}/checkin/submit` | organizador | Confere, envia e confirma o check-in |
| `POST /v1/webhooks/pix/{provider}` | assinatura do provedor | Webhook de confirmação do Pix (provedores reais; o mock não usa) |
| `POST /v1/dev/orders/{id}/simulate-payment` | não (só fora de produção) | Força a confirmação do Pix |
| `GET /actions.json` · `GET`/`POST /actions/events/{slug}` | não | Solana Actions (spec oficial, cabeçalhos CORS das Actions). O `POST` devolve `buy_ticket` com o backend como fee payer e já assinado parcialmente |

- **Erros:** formato único `{"error": {"code": "SOLD_OUT", "message": "...", "details": {}}}` com códigos estáveis e documentados (`UNAUTHORIZED`, `NOT_FOUND`, `SOLD_OUT`, `ORDER_NOT_FUNDED`, `TX_MISMATCH`, `TX_EXPIRED`, `ALREADY_CHECKED_IN`, `VALIDATION_ERROR`, `RPC_ERROR`).
- **Solana Actions:** a web (Next.js) faz rewrite de `/actions.json` e `/actions/*` para o backend, assim as Actions ficam no domínio principal.

### Documentação da API (requisito explícito)

1. **OpenAPI 3.1 rico:** tags por domínio (Events, Orders, Tickets, Waitlist, Webhooks, Solana Actions, Dev), `summary` e `description` em cada rota, `examples` de request e response nos modelos Pydantic, respostas de erro tipadas por rota e um esquema de segurança Bearer.
2. **Scalar API Reference** em `/docs` (interface moderna, com "try it" e trechos de código) e Redoc em `/redoc`. O `openapi.json` é exportado e commitado em `docs/api/openapi.json`.
3. **Guias em `docs/api/`** (inglês): `README.md` (visão geral e ambientes), `authentication.md`, `checkout-flow.md` (diagrama de sequência em mermaid, ponta a ponta), `organizer-flow.md`, `solana-actions.md`, `webhooks.md`, `errors.md` (tabela de códigos), `onchain-program.md` (contas, instruções, erros, PDAs).
4. **Um teste garante a documentação:** toda rota tem `summary`, `description`, tag e pelo menos um exemplo de resposta.

### Testes do backend

- Unitários: cálculo de taxa e conversão; codificação das instruções Anchor (discriminators e borsh) conferida contra o IDL; payload BR Code e QR do mock; máquina de estados do pedido; conferência de hash da transação (aceita igual, rejeita alterada).
- API (httpx + SQLite em memória, Solana e Privy *mockados*): cada endpoint no caminho feliz e nos erros principais.
- Smoke na devnet (script manual): cria evento → compra → check-in contra o programa publicado.

## 5. Web (Next.js)

**Stack:** Next.js (App Router, TypeScript), Tailwind, `@privy-io/react-auth` (carteiras Solana embutidas), `@solana/web3.js` só para desserializar e assinar.

| Rota | Conteúdo |
|---|---|
| `/` | Landing (seção 6) |
| `/e/[slug]` | Checkout: card do evento → login Privy → QR Pix com contador → "Pagamento confirmado" → assinatura automática → ingresso com QR e link do explorer. Metadados Open Graph para a prévia no WhatsApp e no X |
| `/t/[pubkey]` | Página pública de verificação do ingresso |
| `/dashboard` | Organizador: lista de eventos, criar evento (formulário → assinar), vendas por evento, copiar link |
| `/dashboard/checkin/[eventId]` | Leitor de QR pela câmera → confirmação → assinar o check-in → "✓ Entrada liberada" ou "✗ Já usado" |

- O app (checkout e painel) fica em **pt-BR**.
- Estados de carregamento e de erro aparecem em todas as telas, com mensagens claras.

## 6. Landing page

**Referência:** estrutura do spacelift.io, com a paleta **invertida para branco e verde vivo** de cara tecnológica (texto em grafite, verde-neon como destaque, grade sutil de fundo). PT e EN com seletor; o idioma padrão vem do navegador.

**Seções:**
1. **Nav:** Como funciona, Para organizadores, Developers, GitHub e o botão "Criar evento".
2. **Hero:** título, subtítulo, dois botões ("Criar meu evento" e "Ver demo") e o mockup de celular.
3. **Faixa "Construído com":** Solana, Anchor, Privy e USDC, identificados como tecnologia, não como clientes.
4. **Problema → solução:** 3 cards.
5. **Como funciona:** 4 passos ilustrados.
6. **Para devs:** trecho de uma Action e link para os docs da API.
7. **Números com fonte:** Pix 2025 com R$ 35,3 trilhões e cerca de 180 milhões de usuários; golpes com cerca de R$ 29 bilhões.
8. **Lista de espera** (`POST /v1/waitlist`).
9. **Chamada final e rodapé.**

**Regras:**
- Nenhum depoimento ou logo de cliente inventado.
- Depoimentos só entram se forem reais.

**Identidade visual (Higgsfield):**
- `higgsfield-brandkit`: logo, paleta final e tipografia.
- `higgsfield-generate`: mockup do hero, 4 ilustrações dos passos e a imagem Open Graph.
- Os arquivos ficam em `web/public/brand/`.

## 7. Configuração e deploy

- **Contas do usuário:** Privy (App ID e chave de verificação), Neon (`DATABASE_URL`), Vercel (dois projetos: `web` e `backend`) e GitHub (repositório público, MIT).
- **Variáveis do backend:** `DATABASE_URL`, `SOLANA_RPC_URL`, `PROGRAM_ID`, `SERVICE_KEYPAIR` (base58; fee payer, autoridade do mock de USDC e admin), `MOCK_USDC_MINT`, `PRIVY_APP_ID`, `PRIVY_APP_SECRET`, `PRIVY_VERIFICATION_KEY`, `MOCK_PIX_AUTOPAY_SECONDS`, `MOCK_BRL_PER_USD`, `ENV`, `CORS_ORIGINS`, `PUBLIC_WEB_URL`.
- **Variáveis da web:** `NEXT_PUBLIC_PRIVY_APP_ID`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SOLANA_CLUSTER`.
- **Scripts:** `scripts/bootstrap_devnet.py` cria o mock de USDC, inicializa o `Config` e financia a carteira de serviço via airdrop.
- **Plano B de hospedagem do backend:** Railway.

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Ferramentas Solana/Anchor quebrarem a instalação | Instalar no primeiro dia; versão fixada no `Anchor.toml` |
| A Privy não assinar transação com assinatura parcial | Validar logo no início com um protótipo de assinatura; fallback: a Privy assina a mensagem e o backend monta a transação |
| Faucet da devnet limitar o SOL | Airdrop em várias contas, faucet web e manter saldo de reserva |
| Limites do Python na Vercel (tamanho, cold start) | Deixar a rota `/health` aquecida antes da gravação; plano B Railway |
| Prazo | A ordem do plano prioriza o fluxo de ponta a ponta. Landing, check-in e Actions vêm depois do fluxo principal funcionando |

## 9. Cronograma

| Dia | Entrega |
|---|---|
| **07/out** | Spec e plano; ferramentas instaladas; scaffold dos 3 projetos; contas criadas |
| **08/out** | Programa e testes, deploy na devnet; bootstrap; base do backend (modelos, auth, eventos) |
| **09/out** | Pedidos, Pix simulado, on-ramp simulado, envio; checkout web com Privy, **fluxo de ponta a ponta** |
| **10/out** | Painel, check-in, Actions, documentação da API, landing com a identidade do Higgsfield, deploy |
| **11/out** | Acabamento, compras de teste reais, README, gravação do pitch e do vídeo técnico |
| **12/out** | Folga e submissão; Trilha Brasil no Superteam Earn |

## 10. Ajustes feitos no plano de implementação (08/out)

Quando esta seção diverge das anteriores, ela prevalece.

- **Pasta do programa:** `onchain/` (workspace Anchor), em vez de `programs/` na raiz, para não misturar com a web.
- **Testes do programa:** `anchor test` com TypeScript/mocha, o padrão do Anchor, em vez de LiteSVM. É mais confiável instalar no prazo.
- **Banco:** as tabelas são criadas no primeiro acesso (`create_all`), sem Alembic. No MVP não há migrações.
- **Carteira do usuário:** não consultamos a API da Privy para conferir carteiras vinculadas. A posse é provada pela assinatura on-chain do próprio usuário na transação.
- **Check-in:** a transação é vinculada por um `checkin_token` (HMAC do hash da mensagem), sem gravar estado no banco.
- **Códigos de erro:** entra `TX_STALE` (compra concorrente pegou o mesmo número de ingresso; o cliente só busca a transação de novo). Sai `EVENT_NOT_LIVE` (rascunho é `NOT_FOUND`). Entra o estado de pedido `funding`, que impede o mint em dobro.
- **Webhook simulado:** cabeçalho `X-Pix-Signature` = HMAC-SHA256 do corpo com `PIX_WEBHOOK_SECRET`.
- **CORS:** `*`. A API usa Bearer token, sem cookies, e as Solana Actions exigem isso. A variável `CORS_ORIGINS` sai.
- **Ambiente publicado:** `ENV=demo`. Mantém o sandbox de Pix e o faucet de mock USDC do Blink na devnet. `production` desliga os dois.
- **Imagem Open Graph:** gerada por código (`/opengraph-image`), também usada como ícone das Actions. O Higgsfield cuida de logo, hero e ilustrações.
