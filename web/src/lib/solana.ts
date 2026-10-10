const CLUSTER = process.env.NEXT_PUBLIC_SOLANA_CLUSTER === "mainnet" ? "mainnet" : "devnet";

/** Chain id in the Wallet Standard format used by Privy (`solana:devnet` | `solana:mainnet`). */
export const SOLANA_CHAIN = `solana:${CLUSTER}` as const;

export const SOLANA_RPC_URL =
  process.env.NEXT_PUBLIC_SOLANA_RPC_URL ??
  (CLUSTER === "mainnet" ? "https://api.mainnet-beta.solana.com" : "https://api.devnet.solana.com");

export const SOLANA_WS_URL = SOLANA_RPC_URL.replace(/^http/, "ws");
