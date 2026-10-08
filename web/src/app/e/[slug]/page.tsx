import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Checkout } from "@/components/Checkout";
import { AppShell } from "@/components/ui";
import { api, type EventPublic } from "@/lib/api";
import { formatBRL, formatDate } from "@/lib/format";

type Params = { params: Promise<{ slug: string }> };

async function getEvent(slug: string): Promise<EventPublic | null> {
  try {
    return await api<EventPublic>(`/v1/events/${encodeURIComponent(slug)}`);
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const event = await getEvent((await params).slug);
  if (!event) return {};
  const description = `${formatBRL(event.price_brl_cents)} · ${formatDate(event.starts_at)} · Pague com Pix, receba seu ingresso na hora.`;
  return {
    title: `${event.title} · Pix Actions`,
    description,
    openGraph: { title: event.title, description, ...(event.image_url ? { images: [event.image_url] } : {}) },
  };
}

export default async function EventCheckoutPage({ params }: Params) {
  const event = await getEvent((await params).slug);
  if (!event) notFound();
  return (
    <AppShell>
      <Checkout event={event} />
    </AppShell>
  );
}
