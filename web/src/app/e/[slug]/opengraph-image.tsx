import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { api, type EventPublic } from "@/lib/api";
import { formatBRL, formatDate } from "@/lib/format";

export const alt = "Ingresso no Pix Actions";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Per-event link preview (WhatsApp, X, Instagram): event, date, price and the brand. */
export default async function EventOpengraphImage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const event = await api<EventPublic>(`/v1/events/${encodeURIComponent(slug)}`).catch(() => null);
  const mark = await readFile(join(process.cwd(), "public/brand/mark-256.png"));
  const markSrc = `data:image/png;base64,${mark.toString("base64")}`;
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between",
          padding: 72, background: "#FFFFFF",
          backgroundImage:
            "linear-gradient(to right, rgba(11,18,21,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(11,18,21,0.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={markSrc} width={72} height={72} alt="" />
          <div style={{ display: "flex", fontSize: 40, fontWeight: 800, color: "#0B1215" }}>
            Pix&nbsp;<span style={{ color: "#00873E" }}>Actions</span>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", fontSize: 76, fontWeight: 800, color: "#0B1215", lineHeight: 1.05 }}>
            {event?.title ?? "Ingresso"}
          </div>
          {event && (
            <div style={{ display: "flex", fontSize: 34, color: "#5B6770" }}>
              {formatDate(event.starts_at)}
              {event.venue ? ` · ${event.venue}` : ""}
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", fontSize: 64, fontWeight: 800, color: "#0B1215" }}>
            {event ? formatBRL(event.price_brl_cents) : ""}
          </div>
          <div style={{ display: "flex", background: "#00E676", color: "#0B1215", fontSize: 34, fontWeight: 800, padding: "18px 34px", borderRadius: 20 }}>
            Pague com Pix
          </div>
        </div>
      </div>
    ),
    size,
  );
}
