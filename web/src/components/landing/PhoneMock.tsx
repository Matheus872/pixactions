import { QRCodeSVG } from "qrcode.react";

const SAMPLE_PIX = "00020101021226360014br.gov.bcb.pix0114sandbox@pixactions5204000053039865405" + "20.005802BR5919PIX ACTIONS SANDBOX6009SAO PAULO62070503***6304ABCD";

/** Code-drawn hero visual: the checkout as the buyer sees it, plus the onchain ticket and door check-in. */
export function PhoneMock() {
  return (
    <div className="relative mx-auto w-full max-w-sm py-8">
      <div aria-hidden className="absolute inset-x-6 inset-y-10 -z-10 rounded-full bg-neon/30 blur-3xl" />
      <div className="glow relative mx-auto w-72 rounded-[2.75rem] border-[10px] border-ink bg-white shadow-2xl">
        <div className="mx-auto mt-3 h-1.5 w-20 rounded-full bg-line" />
        <div className="space-y-4 p-5">
          <div className="flex items-center gap-2 font-mono text-[11px] text-muted">
            <img src="/brand/mark.svg" alt="" className="h-5 w-5" />
            pixactions.app/e/meetup-sp
          </div>
          <div>
            <div className="text-base font-bold leading-tight">Meetup Solana SP</div>
            <div className="text-xs text-muted">20 out · 19h · São Paulo</div>
          </div>
          <div className="rounded-2xl border border-line p-3">
            <QRCodeSVG value={SAMPLE_PIX} size={208} fgColor="#0B1215" className="h-auto w-full" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold">R$ 20,00</span>
            <span className="font-mono text-xs text-muted">≈ 3.64 USDC</span>
          </div>
          <div className="rounded-xl bg-neon py-3 text-center text-sm font-bold text-ink">✓ Pix recebido</div>
        </div>
      </div>
      <div className="absolute right-0 top-1 sm:-right-4 rotate-6 rounded-2xl border border-line bg-white px-4 py-3 shadow-xl">
        <div className="text-[10px] font-bold tracking-wider text-neon-ink">INGRESSO ON-CHAIN</div>
        <div className="font-mono text-xs">#0042 · Solana</div>
      </div>
      <div className="absolute left-0 bottom-1 sm:-left-4 -rotate-3 rounded-2xl bg-ink px-4 py-3 text-white shadow-xl">
        <div className="text-[10px] font-bold tracking-wider text-neon">CHECK-IN</div>
        <div className="font-mono text-xs">✓ entrada liberada</div>
      </div>
    </div>
  );
}
