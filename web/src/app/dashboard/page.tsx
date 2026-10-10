"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { Alert, AppShell, Card, Spinner } from "@/components/ui";
import { messageFor, type EventOut } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useAuthedApi } from "@/lib/useAuthedApi";

export default function DashboardPage() {
  return (
    <AppShell>
      <AuthGate title="Painel do organizador">
        <EventList />
      </AuthGate>
    </AppShell>
  );
}

function EventList() {
  const call = useAuthedApi();
  const [events, setEvents] = useState<EventOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    call<EventOut[]>("/v1/me/events").then(setEvents).catch((e) => setError(messageFor(e)));
  }, [call]);
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Seus eventos</h1>
        <Link href="/dashboard/new" className="rounded-xl bg-brand px-4 py-2 text-sm font-bold text-ink">+ Novo evento</Link>
      </div>
      {error && <Alert>{error}</Alert>}
      {!events && !error && <Spinner label="Carregando eventos…" />}
      {events?.length === 0 && <Card className="text-center text-muted">Nenhum evento ainda. Crie o primeiro!</Card>}
      {events?.map((ev) => (
        <Link key={ev.id} href={`/dashboard/events/${ev.id}`} className="block">
          <Card className="flex items-center justify-between transition hover:border-ink">
            <div>
              <div className="font-semibold">{ev.title}</div>
              <div className="text-sm text-muted">{formatDate(ev.starts_at)} · {ev.venue}</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-sm">{ev.sold}/{ev.capacity}</div>
              <div className={`text-xs ${ev.status === "live" ? "text-brand-ink" : "text-muted"}`}>
                {ev.status === "live" ? "no ar" : "rascunho"}
              </div>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
