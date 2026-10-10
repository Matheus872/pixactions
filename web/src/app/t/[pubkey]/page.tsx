import { notFound } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { AppShell, Card } from "@/components/ui";
import { api, type TicketOut } from "@/lib/api";
import { formatDate, shortAddr } from "@/lib/format";

export default async function TicketPage({ params }: { params: Promise<{ pubkey: string }> }) {
  const { pubkey } = await params;
  const ticket = await api<TicketOut>(`/v1/tickets/${encodeURIComponent(pubkey)}`).catch(() => null);
  if (!ticket) notFound();
  return (
    <AppShell>
      <Card className="mx-auto max-w-md space-y-4 text-center">
        <div className={`rounded-xl py-3 text-lg font-extrabold ${ticket.checked_in ? "bg-line text-muted" : "bg-brand text-ink"}`}>
          {ticket.checked_in ? "Ingresso já utilizado" : "✓ Ingresso válido"}
        </div>
        {ticket.event && (
          <div>
            <h1 className="text-xl font-bold">{ticket.event.title}</h1>
            <p className="text-sm text-muted">{formatDate(ticket.event.starts_at)} · {ticket.event.venue}</p>
          </div>
        )}
        <QRCodeSVG value={ticket.url} size={200} className="mx-auto" />
        <dl className="grid grid-cols-2 gap-2 text-left text-sm">
          <dt className="text-muted">Ingresso</dt><dd className="font-mono">#{ticket.serial + 1}</dd>
          <dt className="text-muted">Dono</dt><dd className="font-mono">{shortAddr(ticket.owner)}</dd>
        </dl>
        <a href={ticket.explorer_url} target="_blank" rel="noreferrer" className="text-sm font-semibold text-brand-ink underline">
          Verificar na Solana Explorer
        </a>
      </Card>
    </AppShell>
  );
}
