"use client";
import { Scanner } from "@yudiel/react-qr-scanner";
import Link from "next/link";
import { useParams } from "next/navigation";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { AppShell, Button, Card, Spinner } from "@/components/ui";
import { ApiError, messageFor, type CheckinTx, type EventOut, type TicketOut } from "@/lib/api";
import { parseTicketFromQr } from "@/lib/format";
import { useAuthedApi } from "@/lib/useAuthedApi";
import { useTxSigner } from "@/lib/useTxSigner";

type Result = { kind: "ok" | "used" | "error"; text: string } | null;

export default function CheckinPage() {
  const { eventId } = useParams<{ eventId: string }>();
  return (
    <AppShell>
      <AuthGate title="Check-in">
        <CheckinScanner eventId={eventId} />
      </AuthGate>
    </AppShell>
  );
}

function CheckinScanner({ eventId }: { eventId: string }) {
  const call = useAuthedApi();
  const signer = useTxSigner();
  const [event, setEvent] = useState<EventOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result>(null);
  const last = useRef<string | null>(null);

  useEffect(() => {
    call<EventOut[]>("/v1/me/events").then((evs) => setEvent(evs.find((e) => e.id === eventId) ?? null));
  }, [call, eventId]);

  async function handle(raw: string) {
    const pubkey = parseTicketFromQr(raw);
    if (!pubkey || busy || pubkey === last.current) return;
    last.current = pubkey;
    setBusy(true);
    setResult(null);
    try {
      const ticket = await call<TicketOut>(`/v1/tickets/${pubkey}`);
      if (event && ticket.event?.slug !== event.slug) {
        setResult({ kind: "error", text: "Ingresso de outro evento" });
        return;
      }
      if (ticket.checked_in) {
        setResult({ kind: "used", text: "Ingresso já utilizado" });
        return;
      }
      const issued = await call<CheckinTx>(`/v1/tickets/${pubkey}/checkin`, { method: "POST" });
      await call<TicketOut>(`/v1/tickets/${pubkey}/checkin/submit`, {
        method: "POST",
        body: { transaction: await signer.sign(issued.transaction), checkin_token: issued.checkin_token },
      });
      setResult({ kind: "ok", text: `Entrada liberada · ingresso #${ticket.serial + 1}` });
    } catch (e) {
      setResult(
        e instanceof ApiError && e.code === "ALREADY_CHECKED_IN"
          ? { kind: "used", text: "Ingresso já utilizado" }
          : { kind: "error", text: messageFor(e) },
      );
    } finally {
      setBusy(false);
    }
  }

  function onManual(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    last.current = null;
    handle(String(new FormData(e.currentTarget).get("code") ?? ""));
  }

  const color = result?.kind === "ok" ? "bg-neon text-ink" : result?.kind === "used" ? "bg-line text-ink" : "bg-danger text-white";
  return (
    <div className="mx-auto max-w-md space-y-4">
      <Link href={`/dashboard/events/${eventId}`} className="text-sm text-muted">← {event?.title ?? "Evento"}</Link>
      <Card className="overflow-hidden p-0">
        <Scanner onScan={(codes) => codes[0] && handle(codes[0].rawValue)} paused={busy} />
      </Card>
      {busy && <Spinner label="Validando na Solana…" />}
      {result && <div className={`rounded-2xl p-6 text-center text-2xl font-extrabold ${color}`}>{result.kind === "ok" ? "✓ " : "✗ "}{result.text}</div>}
      <Button variant="ghost" className="w-full" onClick={() => { last.current = null; setResult(null); }}>Próximo</Button>
      <form onSubmit={onManual} className="flex gap-2">
        <input name="code" placeholder="Colar link ou código do ingresso" className="flex-1 rounded-xl border border-line px-3 py-2 text-sm" />
        <Button type="submit" variant="ghost">Validar</Button>
      </form>
    </div>
  );
}
