"use client";
import { usePrivy } from "@privy-io/react-auth";
import { useCallback } from "react";
import { api, type ApiOptions } from "./api";

export function useAuthedApi() {
  const { getAccessToken } = usePrivy();
  return useCallback(
    async <T,>(path: string, opts: Omit<ApiOptions, "token"> = {}) =>
      api<T>(path, { ...opts, token: await getAccessToken() }),
    [getAccessToken],
  );
}
