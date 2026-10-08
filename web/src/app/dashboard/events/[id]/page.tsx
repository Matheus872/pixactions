"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { CopyButton } from "@/components/CopyButton";
import { Alert, AppShell, Button, Card, Spinner } from "@/components/ui";
import { messageFor, type EventDraft, type EventOut, type OrderSummary } from "@/lib/api";
import { formatBRL, formatDate, shortAddr } from "@/lib/format";
import { useAuthedApi } from "@/lib/useAuthedApi";
import { useTxSigner } from "@/lib/useTxSigner";

const STATUS_PT: Record<string, string> = {
  pending_payment: "aguardando Pix", paid: "pago", funding: "processando", funded: "processando",
  confirmed: "confirmado", failed: "falhou", expired: "expirado",
};

export default function EventAdminPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <AppShell>
      <AuthGate>
        <EventAdmin id={id} />
      </AuthGate>
    </AppShell>
  );
}

function EventAdmin({ id }: { id: string }) {
  const call = useAuthedApi();
  const signer = useTxSigner();
  const [event, setEvent] = useState<EventOut | null | undefined>(undefined);
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const ev = (await call<EventOut[]>("/v1/me/events")).find((e) => e.id === id) ?? null;
    setEvent(ev);
    if (ev) setOrders(await call<OrderSummary[]>(`/v1/events/${id}/orders`));
  }, [call, id]);

  useEffect(() => {
    const tick = (report: boolean) => load().catch((e) => report && setError(messageFor(e)));
    const first = setTimeout(() => tick(true), 0);
    const t = setInterval(() => tick(false), 5000);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [load]);

  async function publishDraft() {
    try {
      const { transaction } = await call<EventDraft>(`/v1/events/${id}/transaction`, { method: "POST" });
      await call(`/v1/events/${id}/submit`, { method: "POST", body: { transaction: await signer.sign(transaction) } });
      await load();
    } catch (e) {
      setError(messageFor(e));
    }
  }

  if (event === undefined) return <Spinner label="Carregando…" />;
  if (event === null) return <Alert>Evento não encontrado.</Alert>;
  const share = `https://wa.me/?text=${encodeURIComponent(`🎟️ ${event.title}: garanta seu ingresso com Pix em ${event.links.checkout_url}`)}`;
  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard" className="text-sm text-muted">← Seus eventos</Link>
        <h1 className="mt-2 text-2xl font-bold">{event.title}</h1>
        <p className="text-sm text-muted">{formatDate(event.starts_at)} · {event.venue}</p>
      </div>
      {error && <Alert>{error}</Alert>}
      {event.status === "draft" && (
        <Card className="flex items-center justify-between">
          <span>Este evento ainda não foi publicado on-chain.</span>
          <Button onClick={publishDraft}>Publicar agora</Button>
        </Card>
      )}
      <div className="grid grid-cols-2 gap-4">
        <Card><div className="text-sm text-muted">Vendidos</div><div className="font-mono text-3xl font-bold">{event.sold}/{event.capacity}</div></Card>
        <Card><div className="text-sm text-muted">Receita</div><div className="text-3xl font-bold">{formatBRL(event.sold * event.price_brl_cents)}</div></Card>
      </div>
      <Card className="space-y-3">
        <div className="text-sm font-semibold">Link de venda (Pix)</div>
        <div className="break-all font-mono text-sm">{event.links.checkout_url}</div>
        <div className="flex flex-wrap gap-2">
          <CopyButton text={event.links.checkout_url} />
          <a href={share} target="_blank" rel="noreferrer" className="rounded-xl bg-neon px-4 py-3 text-sm font-bold text-ink">Compartilhar no WhatsApp</a>
          <a href={event.links.blink_url} target="_blank" rel="noreferrer" className="rounded-xl border border-line px-4 py-3 text-sm font-semibold">Abrir como Blink</a>
          <Link href={`/dashboard/checkin/${event.id}`} className="rounded-xl bg-ink px-4 py-3 text-sm font-semibold text-white">Abrir check-in</Link>
        </div>
      </Card>
      <Card>
        <div className="mb-3 text-sm font-semibold">Pedidos</div>
        {orders.length === 0 ? (
          <p className="text-sm text-muted">Nenhum pedido ainda.</p>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t border-line">
                  <td className="py-2 font-mono">{shortAddr(o.buyer_wallet)}</td>
                  <td>{STATUS_PT[o.status] ?? o.status}</td>
                  <td className="text-right">
                    {o.ticket_pubkey ? <a className="text-neon-ink underline" href={`/t/${o.ticket_pubkey}`}>ingresso</a> : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
