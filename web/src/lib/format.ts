const BASE58 = "[1-9A-HJ-NP-Za-km-z]{32,44}";

export const formatBRL = (cents: number) =>
  (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export const formatDate = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "medium", timeStyle: "short", timeZone: "America/Sao_Paulo" });

export const shortAddr = (a: string) => `${a.slice(0, 4)}…${a.slice(-4)}`;

export function parseTicketFromQr(raw: string): string | null {
  const m = raw.trim().match(new RegExp(`^(?:https?://[^\\s]+/t/)?(${BASE58})/?$`));
  return m ? m[1] : null;
}
