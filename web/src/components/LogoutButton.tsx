"use client";
import { usePrivy } from "@privy-io/react-auth";

// No e-mail on screen on purpose: these pages get recorded and shared.
export function LogoutButton() {
  const { ready, authenticated, logout } = usePrivy();
  if (!ready || !authenticated) return null;
  return (
    <button
      onClick={() => logout().then(() => window.location.reload())}
      className="rounded-full border border-line bg-white px-3 py-1 text-xs font-semibold text-ink transition hover:border-ink"
    >
      Sair
    </button>
  );
}
