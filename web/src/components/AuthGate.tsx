"use client";
import { usePrivy } from "@privy-io/react-auth";
import { useTxSigner } from "@/lib/useTxSigner";
import { Button, Card, Spinner } from "./ui";

export function AuthGate({ children, title = "Entre para continuar" }: { children: React.ReactNode; title?: string }) {
  const { ready, authenticated, login } = usePrivy();
  const signer = useTxSigner();
  if (!ready) return <Spinner label="Carregando…" />;
  if (!authenticated)
    return (
      <Card className="mx-auto max-w-md space-y-4 text-center">
        <h1 className="text-xl font-bold">{title}</h1>
        <p className="text-sm text-muted">Use seu e-mail ou celular. Sua carteira Solana é criada na hora, e só você controla.</p>
        <Button onClick={login} className="w-full">Entrar</Button>
      </Card>
    );
  if (!signer.ready) return <Spinner label="Preparando sua carteira…" />;
  return <>{children}</>;
}
