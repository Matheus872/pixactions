import { describe, expect, it } from "vitest";
import { formatBRL, parseTicketFromQr, shortAddr } from "./format";

const PK = "8sLbNZoA1cfnvMJLPfp98ZLAnFSYCFApfJKMbiXNLwxj";

describe("format", () => {
  it("formats BRL cents", () => {
    expect(formatBRL(2000)).toContain("20,00");
    expect(formatBRL(2000)).toContain("R$");
  });
  it("shortens addresses", () => {
    expect(shortAddr(PK)).toBe("8sLb…Lwxj");
  });
  it("parses ticket QR payloads", () => {
    expect(parseTicketFromQr(`https://pixactions.vercel.app/t/${PK}`)).toBe(PK);
    expect(parseTicketFromQr(`https://pixactions.vercel.app/t/${PK}/`)).toBe(PK);
    expect(parseTicketFromQr(PK)).toBe(PK);
    expect(parseTicketFromQr("https://evil.example/nothing")).toBeNull();
    expect(parseTicketFromQr("")).toBeNull();
  });
});
