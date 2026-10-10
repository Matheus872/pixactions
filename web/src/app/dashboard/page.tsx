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
      <AuthGate title="Painel de vendas">
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
        <h1 className="text-2xl font-bold">Suas ações</h1>
        <Link href="/dashboard/new" className="rounded-xl bg-brand px-4 py-2 text-sm font-bold text-white">+ Nova ação</Link>
      </div>
      {error && <Alert>{error}</Alert>}
      {!events && !error && <Spinner label="Carregando eventos…" />}
      {events?.length === 0 && <Card className="text-center text-muted">Nenhuma ação ainda. Crie a primeira!</Card>}
      {events?.map((ev) => (
        <Link key={ev.id} href={`/dashboard/events/${ev.id}`} className="block">
          <Card className="flex items-center justify-between transition hover:border-ink">
            <div>
              <div className="flex items-center gap-2 font-semibold">{ev.title}<span className="rounded-full bg-brand-soft px-2 py-0.5 font-mono text-[10px] font-medium text-brand-ink">ingresso</span></div>
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
