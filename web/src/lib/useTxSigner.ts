"use client";
import { useSignTransaction, useWallets } from "@privy-io/react-auth/solana";
import { useCallback } from "react";
import { b64ToBytes, bytesToB64 } from "./b64";

/** Signs API-issued transactions with the user's Privy embedded Solana wallet. */
export function useTxSigner() {
  const { wallets, ready } = useWallets();
  const { signTransaction } = useSignTransaction();
  const wallet = wallets[0];
  const sign = useCallback(
    async (txB64: string) => {
      if (!wallet) throw new Error("Carteira ainda não está pronta");
      const { signedTransaction } = await signTransaction({ transaction: b64ToBytes(txB64), wallet });
      return bytesToB64(signedTransaction);
    },
    [wallet, signTransaction],
  );
  return { ready: ready && !!wallet, address: wallet?.address ?? null, sign };
}
