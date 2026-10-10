"use client";
import { type FormEvent, useState } from "react";
import { api } from "@/lib/api";
import type { Lang, LandingCopy } from "@/i18n/landing";

type Role = keyof LandingCopy["waitlist"]["roles"];

export function WaitlistForm({ t, lang }: { t: LandingCopy; lang: Lang }) {
  const [role, setRole] = useState<Role>("organizer");
  const [state, setState] = useState<"idle" | "busy" | "success" | "error">("idle");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setState("busy");
    const email = String(new FormData(e.currentTarget).get("email"));
    try {
      await api<{ received: boolean }>("/v1/waitlist", { method: "POST", body: { email, role, lang } });
      setState("success");
    } catch {
      setState("error");
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-xl space-y-4 text-center">
      <h2 className="text-3xl font-bold">{t.waitlist.title}</h2>
      <p className="text-muted">{t.waitlist.body}</p>
      <div className="flex flex-wrap justify-center gap-2">
        {(Object.keys(t.waitlist.roles) as Role[]).map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRole(r)}
            className={`rounded-full border px-4 py-2 text-sm ${role === r ? "border-ink bg-ink text-white" : "border-line bg-white"}`}
          >
            {t.waitlist.roles[r]}
          </button>
        ))}
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input name="email" type="email" required placeholder={t.waitlist.email} className="flex-1 rounded-xl border border-line px-4 py-3" />
        <button disabled={state === "busy"} className="glow rounded-xl bg-brand px-6 py-3 font-bold text-ink disabled:opacity-60">
          {t.waitlist.submit}
        </button>
      </div>
      {state === "success" && <p className="text-brand-ink">{t.waitlist.success}</p>}
      {state === "error" && <p className="text-danger">{t.waitlist.error}</p>}
    </form>
  );
}
