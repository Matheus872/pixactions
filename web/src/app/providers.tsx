"use client";
import { PrivyProvider } from "@privy-io/react-auth";
import { createSolanaRpc, createSolanaRpcSubscriptions } from "@solana/kit";
import { SOLANA_CHAIN, SOLANA_RPC_URL, SOLANA_WS_URL } from "@/lib/solana";

// Privy signs locally but needs an RPC for the chain it signs for (it defaults to mainnet otherwise).
const solanaRpcs = {
  [SOLANA_CHAIN]: {
    rpc: createSolanaRpc(SOLANA_RPC_URL),
    rpcSubscriptions: createSolanaRpcSubscriptions(SOLANA_WS_URL),
    blockExplorerUrl: "https://explorer.solana.com",
  },
};

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <PrivyProvider
      appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID!}
      config={{
        loginMethods: ["email"],
        appearance: { theme: "light", accentColor: "#00C853", walletChainType: "solana-only", logo: "/brand/logo.png" },
        embeddedWallets: { solana: { createOnLogin: "all-users" } },
        solana: { rpcs: solanaRpcs },
      }}
    >
      {children}
    </PrivyProvider>
  );
}
