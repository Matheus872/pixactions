"use client";
import { usePrivy } from "@privy-io/react-auth";
import { QRCodeSVG } from "qrcode.react";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, messageFor, type EventPublic, type OrderOut } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { formatBRL, formatDate } from "@/lib/format";
import { useAuthedApi } from "@/lib/useAuthedApi";
import { useTxSigner } from "@/lib/useTxSigner";
import { CopyButton } from "./CopyButton";
import { Alert, Button, Card, BrandButton, Spinner } from "./ui";

type TicketRef = components["schemas"]["TicketRef"];

const ACTIVE = ["pending_payment", "paid", "funding", "funded"];
const SHOW_DEV = process.env.NEXT_PUBLIC_SHOW_DEV_TOOLS === "1";

export function Checkout({ event }: { event: EventPublic }) {
  const { authenticated, login } = usePrivy();
  const signer = useTxSigner();
  const call = useAuthedApi();
  const [wantsToBuy, setWantsToBuy] = useState(false);
  const [order, setOrder] = useState<OrderOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const attemptedTx = useRef<string | null>(null);
  // After an error that will not fix itself (rejected signature, program error) stop prompting the wallet.
  const [signPaused, setSignPaused] = useState(false);
  // Tickets this buyer already owns for the event (returning buyers must not buy again by accident).
  const [owned, setOwned] = useState<TicketRef[]>([]);

  useEffect(() => {
    if (!authenticated) return;
    call<TicketRef[]>(`/v1/me/tickets?event_slug=${encodeURIComponent(event.slug)}`).then(setOwned).catch(() => {});
  }, [authenticated, call, event.slug, order?.status]);

  // 1) Logged in with a wallet → open (or resume) the order.
  useEffect(() => {
    if (!wantsToBuy || order || !authenticated || !signer.ready || !signer.address) return;
    call<OrderOut>("/v1/orders", { method: "POST", body: { event_slug: event.slug, wallet: signer.address } })
      .then(setOrder)
      .catch((e) => {
        setError(messageFor(e));
        setWantsToBuy(false);
      });
  }, [wantsToBuy, order, authenticated, signer.ready, signer.address, call, event.slug]);

  // 2) Poll while the order is in flight.
  const orderId = order?.id;
  const status = order?.status;
  useEffect(() => {
    if (!orderId || !status || !ACTIVE.includes(status)) return;
    const timer = setInterval(() => {
      call<OrderOut>(`/v1/orders/${orderId}`)
        .then((o) => {
          setOrder(o);
          if (!signPaused) setError(null);
        })
        .catch((e) => setError(messageFor(e)));
    }, 2000);
    return () => clearInterval(timer);
  }, [orderId, status, call, signPaused]);

  // 3) Funded → sign once per issued transaction and submit.
  useEffect(() => {
    const tx = order?.transaction;
    if (!order || order.status !== "funded" || !tx || signPaused || attemptedTx.current === tx) return;
    attemptedTx.current = tx;
    (async () => {
      try {
        const signed = await signer.sign(tx);
        setOrder(await call<OrderOut>(`/v1/orders/${order.id}/submit`, { method: "POST", body: { transaction: signed } }));
        setError(null);
      } catch (e) {
        // TX_STALE / TX_EXPIRED: the next poll brings a fresh transaction, signed automatically.
        if (!(e instanceof ApiError && (e.code === "TX_STALE" || e.code === "TX_EXPIRED"))) {
          setError(messageFor(e));
          setSignPaused(true);
        }
      }
    })();
  }, [order, signer, call, signPaused]);

  function retrySigning() {
    setError(null);
    attemptedTx.current = null;
    setSignPaused(false);
  }

  function start() {
    setError(null);
    setOrder(null);
    attemptedTx.current = null;
    setSignPaused(false);
    setWantsToBuy(true);
    if (!authenticated) login();
  }

  const preparing = wantsToBuy && !order && !error;
  return (
    <div className="mx-auto max-w-md space-y-4">
      <EventCard event={event} />
      {error && (
        <Alert>
          {error}{" "}
          {order?.status === "funded" && (
            <button className="underline" onClick={retrySigning}>Tentar de novo</button>
          )}
        </Alert>
      )}
      {!order && owned.length > 0 && (
        <Card className="space-y-3">
          <div className="font-semibold">Você já tem {owned.length === 1 ? "1 ingresso" : `${owned.length} ingressos`} para este evento</div>
          <div className="flex flex-wrap gap-2">
            {owned.map((t, i) => (
              <a key={t.pubkey} href={t.url} className="rounded-xl border border-line px-4 py-2 text-sm font-semibold hover:border-ink">
                Ver ingresso{owned.length > 1 ? ` ${i + 1}` : ""}
              </a>
            ))}
          </div>
        </Card>
      )}
      {!order &&
        (event.sold_out ? (
          <Card className="text-center font-semibold">Esgotado</Card>
        ) : (
          <BrandButton className="w-full" onClick={start} disabled={preparing && authenticated}>
            {preparing && authenticated ? "Preparando seu Pix…" : owned.length > 0 ? `Comprar outro ingresso (${formatBRL(event.price_brl_cents)})` : `Pagar ${formatBRL(event.price_brl_cents)} com Pix`}
          </BrandButton>
        ))}
      {order?.status === "pending_payment" && order.pix && (
        <PixPanel order={order} onSimulate={SHOW_DEV ? () => api(`/v1/dev/orders/${order.id}/simulate-payment`, { method: "POST" }) : undefined} />
      )}
      {order && ["paid", "funding", "funded"].includes(order.status) && (
        <Card>
          <Spinner label={order.status === "funded" ? "Emitindo seu ingresso na Solana…" : "Pix recebido! Enviando para sua carteira…"} />
        </Card>
      )}
      {order?.status === "confirmed" && order.ticket && <TicketCard ticket={order.ticket} />}
      {order?.status === "expired" && (
        <Alert>
          O Pix expirou. <button className="underline" onClick={start}>Gerar outro</button>
        </Alert>
      )}
      {order?.status === "failed" && (
        <Alert>
          {order.error === "SOLD_OUT"
            ? "Os ingressos esgotaram antes da confirmação. O valor ficou na sua carteira."
            : "Não foi possível concluir a compra."}
        </Alert>
      )}
      <p className="text-center text-xs text-muted">Pix em sandbox · Ingresso registrado na Solana devnet</p>
    </div>
  );
}

function EventCard({ event }: { event: EventPublic }) {
  return (
    <Card className="space-y-3">
      {event.image_url && <img src={event.image_url} alt="" className="aspect-video w-full rounded-xl object-cover" />}
      <h1 className="text-2xl font-bold leading-tight">{event.title}</h1>
      <p className="text-sm text-muted">{formatDate(event.starts_at)}{event.venue ? ` · ${event.venue}` : ""}</p>
      {event.description && <p className="text-sm">{event.description}</p>}
      <div className="flex items-end justify-between border-t border-line pt-3">
        <div>
          <div className="text-3xl font-extrabold">{formatBRL(event.price_brl_cents)}</div>
          <div className="font-mono text-xs text-muted">≈ {event.price_token_display} USDC on-chain</div>
        </div>
        <div className="text-right text-sm text-muted">{event.sold_out ? "Esgotado" : `${event.remaining} restantes`}</div>
      </div>
    </Card>
  );
}

function PixPanel({ order, onSimulate }: { order: OrderOut; onSimulate?: () => Promise<unknown> }) {
  const pix = order.pix!;
  const [left, setLeft] = useState(() => Math.max(0, Date.parse(pix.expires_at) - Date.now()));
  useEffect(() => {
    const t = setInterval(() => setLeft(Math.max(0, Date.parse(pix.expires_at) - Date.now())), 1000);
    return () => clearInterval(t);
  }, [pix.expires_at]);
  const mm = String(Math.floor(left / 60000)).padStart(2, "0");
  const ss = String(Math.floor((left % 60000) / 1000)).padStart(2, "0");
  return (
    <Card className="space-y-4 text-center">
      <h2 className="text-lg font-bold">Pague com Pix</h2>
      <p className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-sm font-semibold text-danger">
        Demonstração: o pagamento é simulado e confirma sozinho. Não pague este código no app do banco.
      </p>
      <img src={`data:image/png;base64,${pix.qr_png_base64}`} alt="QR code Pix" className="mx-auto w-56 rounded-xl border border-line" />
      <div className="break-all rounded-xl bg-brand-soft p-3 font-mono text-xs">{pix.brcode}</div>
      <div className="flex justify-center gap-2">
        <CopyButton text={pix.brcode} label="Copiar código Pix" />
        {onSimulate && <Button variant="ghost" onClick={() => onSimulate()}>Simular pagamento</Button>}
      </div>
      <Spinner label={`Aguardando pagamento · expira em ${mm}:${ss}`} />
    </Card>
  );
}

function TicketCard({ ticket }: { ticket: NonNullable<OrderOut["ticket"]> }) {
  return (
    <Card className="glow space-y-4 text-center">
      <div className="text-sm font-semibold text-brand-ink">✓ Ingresso emitido na Solana</div>
      <QRCodeSVG value={ticket.url} size={220} className="mx-auto" />
      <p className="text-sm text-muted">Apresente este QR na entrada. Ele também fica disponível quando você voltar a este link logado com o mesmo e-mail.</p>
      <div className="flex justify-center gap-2">
        <a href={ticket.url} className="rounded-xl border border-line px-4 py-2 text-sm font-semibold">Página do ingresso</a>
        <a href={ticket.explorer_url} target="_blank" rel="noreferrer" className="rounded-xl border border-line px-4 py-2 text-sm font-semibold">Ver no Explorer</a>
      </div>
    </Card>
  );
}
