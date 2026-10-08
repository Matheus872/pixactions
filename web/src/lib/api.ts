import type { components } from "./api-types";

type S = components["schemas"];
export type EventOut = S["EventOut"];
export type EventPublic = S["EventPublic"];
export type EventDraft = S["EventDraft"];
export type OrderOut = S["OrderOut"];
export type OrderSummary = S["OrderSummary"];
export type TicketOut = S["TicketOut"];
export type CheckinTx = S["CheckinTx"];

const API_URL =
  typeof window === "undefined"
    ? process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export type ApiOptions = { method?: "GET" | "POST"; body?: unknown; token?: string | null };

export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: opts.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(opts.token ? { Authorization: `Bearer ${opts.token}` } : {}),
    },
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data?.error?.code ?? "UNKNOWN", data?.error?.message ?? res.statusText);
  return data as T;
}

const MESSAGES: Record<string, string> = {
  UNAUTHORIZED: "Sua sessão expirou. Entre de novo.",
  NOT_FOUND: "Não encontrado.",
  SOLD_OUT: "Ingressos esgotados.",
  ORDER_NOT_FUNDED: "O pagamento ainda não foi confirmado.",
  TX_MISMATCH: "A transação não confere. Tente de novo.",
  TX_EXPIRED: "A transação expirou. Tente de novo.",
  TX_STALE: "Alguém comprou ao mesmo tempo. Tentando de novo…",
  ALREADY_CHECKED_IN: "Ingresso já utilizado.",
  RPC_ERROR: "A rede Solana está instável. Tente em instantes.",
};

export function messageFor(err: unknown): string {
  if (err instanceof ApiError) return MESSAGES[err.code] ?? err.message;
  return err instanceof Error ? err.message : "Algo deu errado.";
}
