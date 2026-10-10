"use client";
import { useEffect, useState } from "react";
import { copy, type Lang } from "@/i18n/landing";
import { PhoneMock } from "./PhoneMock";
import { BuiltWith, Devs, FinalCta, Footer, Hero, Nav, Numbers, Problems, Steps } from "./sections";
import { WaitlistForm } from "./WaitlistForm";

const KEY = "pixactions.lang";

export function Landing() {
  const [lang, setLang] = useState<Lang>("pt");
  useEffect(() => {
    // Deferred so the server-rendered "pt" hydrates first, then the viewer's language applies.
    const t = setTimeout(() => {
      let saved: string | null = null;
      try {
        saved = localStorage.getItem(KEY);
      } catch {}
      setLang(saved === "pt" || saved === "en" ? saved : navigator.language.toLowerCase().startsWith("pt") ? "pt" : "en");
    }, 0);
    return () => clearTimeout(t);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  }, [lang]);

  function change(next: Lang) {
    setLang(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {}
  }

  const t = copy[lang];
  return (
    <div className="bg-paper text-ink">
      <Nav t={t} lang={lang} onLang={change} />
      <main>
        <Hero t={t} visual={<PhoneMock />} />
        <BuiltWith t={t} />
        <Problems t={t} />
        <Steps t={t} />
        <Devs t={t} />
        <Numbers t={t} />
        <section id="waitlist" className="mx-auto max-w-6xl px-4 py-24">
          <WaitlistForm t={t} lang={lang} />
        </section>
        <FinalCta t={t} />
      </main>
      <Footer t={t} />
    </div>
  );
}
