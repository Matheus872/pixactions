"use client";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { Alert, AppShell, Card, BrandButton } from "@/components/ui";
import { ApiError, messageFor, type EventDraft, type EventOut } from "@/lib/api";
import { useAuthedApi } from "@/lib/useAuthedApi";
import { useTxSigner } from "@/lib/useTxSigner";

export default function NewEventPage() {
  return (
    <AppShell>
      <AuthGate title="Crie sua ação">
        <NewEventForm />
      </AuthGate>
    </AppShell>
  );
}

const input = "w-full rounded-xl border border-line bg-white px-4 py-3 outline-none focus:border-ink";

function NewEventForm() {
  const call = useAuthedApi();
  const signer = useTxSigner();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function publish(eventId: string, firstTx: string) {
    let tx = firstTx;
    for (let attempt = 0; ; attempt++) {
      try {
        await call<EventOut>(`/v1/events/${eventId}/submit`, { method: "POST", body: { transaction: await signer.sign(tx) } });
        return;
      } catch (err) {
        if (err instanceof ApiError && err.code === "TX_EXPIRED" && attempt === 0) {
          tx = (await call<EventDraft>(`/v1/events/${eventId}/transaction`, { method: "POST" })).transaction;
          continue;
        }
        throw err;
      }
    }
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const f = new FormData(e.currentTarget);
    try {
      const draft = await call<EventDraft>("/v1/events", {
        method: "POST",
        body: {
          title: String(f.get("title")),
          description: String(f.get("description") ?? ""),
          venue: String(f.get("venue") ?? ""),
          starts_at: new Date(String(f.get("starts_at"))).toISOString(),
          price_brl_cents: Math.round(Number(String(f.get("price")).replace(",", ".")) * 100),
          capacity: Number(f.get("capacity")),
          wallet: signer.address,
        },
      });
      await publish(draft.event.id, draft.transaction);
      router.push(`/dashboard/events/${draft.event.id}`);
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={onSubmit} className="space-y-4">
        <h1 className="text-2xl font-bold">Nova ação</h1>
        <ActionTypePicker />
        <p className="text-sm text-muted">Ingresso: venda pelo link, ingresso on-chain na carteira de quem compra e check-in na porta.</p>
        <input name="title" required minLength={3} maxLength={80} placeholder="Nome do evento" className={input} />
        <textarea name="description" maxLength={1000} placeholder="Descrição (opcional)" className={input} />
        <input name="venue" maxLength={120} placeholder="Local" className={input} />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <input name="starts_at" type="datetime-local" required className={input} />
          <input name="price" required inputMode="decimal" placeholder="Preço (R$)" pattern="^\d+([.,]\d{1,2})?$" className={input} />
          <input name="capacity" type="number" min={1} max={10000} required placeholder="Lotação" className={input} />
        </div>
        {error && <Alert>{error}</Alert>}
        <BrandButton type="submit" disabled={busy} className="w-full">
          {busy ? "Registrando na Solana…" : "Criar e publicar"}
        </BrandButton>
        <p className="text-xs text-muted">O evento é registrado on-chain. Você assina com sua carteira e a gente paga as taxas da rede.</p>
      </form>
    </Card>
  );
}

const ACTION_TYPES = [
  { id: "ticket", label: "Ingresso", live: true },
  { id: "subscription", label: "Assinatura", live: false },
  { id: "token", label: "Token", live: false },
  { id: "donation", label: "Doação", live: false },
  { id: "digital", label: "Produto digital", live: false },
  { id: "any", label: "Qualquer Solana Action", live: false },
];

function ActionTypePicker() {
  return (
    <div role="radiogroup" aria-label="Tipo de ação" className="flex flex-wrap gap-2">
      {ACTION_TYPES.map((type) => (
        <button
          key={type.id}
          type="button"
          role="radio"
          aria-checked={type.live}
          disabled={!type.live}
          className={`rounded-full border px-3 py-1.5 text-sm ${type.live ? "border-brand bg-brand text-ink" : "cursor-not-allowed border-line text-muted"}`}
        >
          {type.label}
          {!type.live && <span className="ml-1 font-mono text-[10px]">em breve</span>}
        </button>
      ))}
    </div>
  );
}
