import { ImageResponse } from "next/og";

export const alt = "Pix Actions: pague com Pix, receba on-chain";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center",
          padding: 80, background: "#FFFFFF",
          backgroundImage:
            "linear-gradient(to right, rgba(11,18,21,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(11,18,21,0.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ width: 72, height: 72, borderRadius: 18, background: "#0B1215", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 32, height: 32, border: "5px solid #00E676", transform: "rotate(45deg)" }} />
          </div>
          <div style={{ fontSize: 52, fontWeight: 800, color: "#0B1215" }}>Pix Actions</div>
        </div>
        <div style={{ marginTop: 44, fontSize: 72, fontWeight: 800, color: "#0B1215", lineHeight: 1.05 }}>Pague com Pix,</div>
        <div style={{ fontSize: 72, fontWeight: 800, color: "#00873E", lineHeight: 1.05 }}>receba on-chain.</div>
        <div style={{ marginTop: 32, fontSize: 30, color: "#5B6770" }}>Ingressos na Solana para quem só tem Pix · sem carteira</div>
      </div>
    ),
    size,
  );
}
