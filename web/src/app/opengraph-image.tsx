import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";

export const alt = "Pix Actions: qualquer ação na Solana, paga com Pix";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  const logo = await readFile(join(process.cwd(), "public/brand/logo.png"));
  const logoSrc = `data:image/png;base64,${logo.toString("base64")}`;
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center",
          alignItems: "center", gap: 36, background: "#FFFFFF",
          backgroundImage:
            "linear-gradient(to right, rgba(11,18,21,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(11,18,21,0.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={logoSrc} width={760} height={324} alt="" />
        <div style={{ display: "flex", fontSize: 40, fontWeight: 800, color: "#0B1215" }}>
          Qualquer ação na Solana,&nbsp;<span style={{ color: "#00873E" }}>paga com Pix.</span>
        </div>
      </div>
    ),
    size,
  );
}
