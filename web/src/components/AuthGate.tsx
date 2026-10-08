"use client";
import { usePrivy } from "@privy-io/react-auth";
import { useTxSigner } from "@/lib/useTxSigner";
import { Card, NeonButton, Spinner } from "./ui";

const PERKS = ["Sem seed phrase nem extensão", "Carteira não custodial: só você controla", "Taxas da rede por nossa conta"];

export function AuthGate({ children, title = "Entre para continuar" }: { children: React.ReactNode; title?: string }) {
  const { ready, authenticated, login } = usePrivy();
  const signer = useTxSigner();
  if (!ready) return <Centered><Spinner label="Carregando…" /></Centered>;
  if (!authenticated)
    return (
      <Card className="mx-auto mt-10 max-w-md space-y-6 p-8 text-center shadow-xl shadow-ink/5">
        <img src="/brand/mark.svg" alt="" className="mx-auto h-12 w-12" />
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          <p className="text-sm text-muted">Entre com seu e-mail ou celular. Sua carteira Solana é criada na hora.</p>
        </div>
        <NeonButton onClick={login} className="w-full">Entrar com e-mail ou celular</NeonButton>
        <ul className="space-y-2 border-t border-line pt-5 text-left text-sm">
          {PERKS.map((perk) => (
            <li key={perk} className="flex items-center gap-3">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-neon-soft text-[11px] font-bold text-neon-ink">✓</span>
              {perk}
            </li>
          ))}
        </ul>
      </Card>
    );
  if (!signer.ready) return <Centered><Spinner label="Preparando sua carteira…" /></Centered>;
  return <>{children}</>;
}

function Centered({ children }: { children: React.ReactNode }) {
  return <div className="mt-16 flex justify-center">{children}</div>;
}
