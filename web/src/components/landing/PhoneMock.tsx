export function PhoneMock() {
  return (
    <div className="relative mx-auto w-72">
      <div className="glow rounded-[2.5rem] border-[10px] border-ink bg-white p-5 shadow-2xl">
        <div className="mb-4 h-1.5 w-16 rounded-full bg-line mx-auto" />
        <div className="text-xs text-muted">Meetup Solana SP</div>
        <div className="text-2xl font-extrabold">R$ 20,00</div>
        <div className="my-4 grid aspect-square grid-cols-7 gap-1 rounded-xl border border-line p-3">
          {Array.from({ length: 49 }, (_, i) => (
            <span key={i} className={`rounded-sm ${(i * 7 + (i % 5)) % 3 === 0 ? "bg-ink" : "bg-transparent"}`} />
          ))}
        </div>
        <div className="rounded-xl bg-neon py-3 text-center text-sm font-bold">✓ Pix recebido</div>
      </div>
      <div className="absolute -right-10 bottom-8 rotate-6 rounded-2xl border border-line bg-white p-4 shadow-xl">
        <div className="text-[10px] font-semibold text-neon-ink">INGRESSO ON-CHAIN</div>
        <div className="font-mono text-xs">#0042 · devnet</div>
      </div>
    </div>
  );
}
