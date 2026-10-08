import Link from "next/link";
import type { Lang, LandingCopy } from "@/i18n/landing";

const API_DOCS = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`;
const GITHUB = process.env.NEXT_PUBLIC_GITHUB_URL ?? "https://github.com";
const DEMO = process.env.NEXT_PUBLIC_DEMO_EVENT_SLUG ? `/e/${process.env.NEXT_PUBLIC_DEMO_EVENT_SLUG}` : "#como-funciona";
const wrap = "mx-auto max-w-6xl px-4";

export function Nav({ t, lang, onLang }: { t: LandingCopy; lang: Lang; onLang: (l: Lang) => void }) {
  return (
    <header className="sticky top-0 z-20 border-b border-line/70 bg-white/80 backdrop-blur">
      <nav className={`${wrap} flex h-16 items-center justify-between`}>
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <img src="/brand/mark.svg" alt="" className="h-7 w-7" /> Pix Actions
        </Link>
        <div className="hidden items-center gap-6 text-sm text-muted md:flex">
          <a href="#como-funciona" className="hover:text-ink">{t.nav.how}</a>
          <a href="#devs" className="hover:text-ink">{t.nav.devs}</a>
          <a href={API_DOCS} className="hover:text-ink">{t.nav.docs}</a>
          <a href={GITHUB} className="hover:text-ink">GitHub</a>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-full border border-line p-0.5 font-mono text-xs">
            {(["pt", "en"] as const).map((l) => (
              <button key={l} onClick={() => onLang(l)} className={`rounded-full px-2.5 py-1 ${lang === l ? "bg-ink text-white" : "text-muted"}`}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <Link href="/dashboard" className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white">{t.nav.cta}</Link>
        </div>
      </nav>
    </header>
  );
}

export function Hero({ t, heroImage }: { t: LandingCopy; heroImage: React.ReactNode }) {
  return (
    <section className="bg-grid border-b border-line">
      <div className={`${wrap} grid items-center gap-12 py-20 md:grid-cols-2 md:py-28`}>
        <div className="space-y-6">
          <span className="inline-block rounded-full bg-neon-soft px-3 py-1 font-mono text-xs text-neon-ink">{t.hero.badge}</span>
          <h1 className="text-4xl font-extrabold leading-[1.05] tracking-tight md:text-6xl">
            {t.hero.title} <span className="text-neon-ink">{t.hero.accent}</span>
          </h1>
          <p className="max-w-xl text-lg text-muted">{t.hero.subtitle}</p>
          <div className="flex flex-wrap gap-3">
            <Link href="/dashboard" className="glow rounded-xl bg-neon px-6 py-4 font-bold text-ink">{t.hero.primary}</Link>
            <Link href={DEMO} className="rounded-xl border border-ink px-6 py-4 font-semibold">{t.hero.secondary}</Link>
          </div>
          <p className="font-mono text-xs text-muted">{t.hero.note}</p>
        </div>
        <div>{heroImage}</div>
      </div>
    </section>
  );
}

export function BuiltWith({ t }: { t: LandingCopy }) {
  return (
    <section className="border-b border-line">
      <div className={`${wrap} flex flex-wrap items-center justify-center gap-x-10 gap-y-3 py-8 font-mono text-sm text-muted`}>
        <span className="uppercase tracking-widest">{t.builtWith}</span>
        {["Solana", "Anchor", "Privy", "USDC", "FastAPI", "Next.js"].map((x) => (
          <span key={x} className="font-semibold text-ink/70">{x}</span>
        ))}
      </div>
    </section>
  );
}

export function Problems({ t }: { t: LandingCopy }) {
  return (
    <section className={`${wrap} py-24`}>
      <h2 className="max-w-3xl text-3xl font-bold md:text-4xl">{t.problems.title}</h2>
      <p className="mt-4 max-w-3xl text-muted">{t.problems.subtitle}</p>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {t.problems.items.map((item, i) => (
          <div key={item.title} className="rounded-2xl border border-line p-6 transition hover:border-neon">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-neon-soft font-mono text-neon-ink">0{i + 1}</div>
            <h3 className="text-lg font-semibold">{item.title}</h3>
            <p className="mt-2 text-sm text-muted">{item.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Steps({ t, illustrated }: { t: LandingCopy; illustrated: boolean }) {
  return (
    <section id="como-funciona" className="bg-grid border-y border-line">
      <div className={`${wrap} py-24`}>
        <h2 className="text-3xl font-bold md:text-4xl">{t.steps.title}</h2>
        <p className="mt-4 text-muted">{t.steps.subtitle}</p>
        <ol className="mt-12 grid gap-6 md:grid-cols-4">
          {t.steps.items.map((s, i) => (
            <li key={s.title} className="rounded-2xl border border-line bg-white p-5">
              {illustrated ? (
                <img src={`/brand/step-${i + 1}.png`} alt="" className="mb-4 aspect-square w-full rounded-xl object-cover" />
              ) : (
                <div className="mb-4 font-mono text-5xl font-extrabold text-neon">{i + 1}</div>
              )}
              <h3 className="font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-muted">{s.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Devs({ t }: { t: LandingCopy }) {
  return (
    <section id="devs" className={`${wrap} grid items-center gap-12 py-24 md:grid-cols-2`}>
      <div>
        <h2 className="text-3xl font-bold md:text-4xl">{t.devs.title}</h2>
        <p className="mt-4 text-muted">{t.devs.body}</p>
        <div className="mt-6 flex gap-3">
          <a href={API_DOCS} className="rounded-xl bg-ink px-5 py-3 text-sm font-semibold text-white">{t.devs.docs}</a>
          <a href={GITHUB} className="rounded-xl border border-ink px-5 py-3 text-sm font-semibold">{t.devs.github}</a>
        </div>
      </div>
      <pre className="overflow-x-auto rounded-2xl bg-ink p-6 font-mono text-xs leading-relaxed text-white">
        <span className="text-neon">$</span> curl pixactions.app/actions/events/meetup-sp{"\n"}
        {`{
  "type": "action",
  "title": "Meetup Solana SP",
  "label": "Comprar ingresso · 3.64 USDC",
  "links": { "actions": [{
    "type": "transaction",
    "href": "/actions/events/meetup-sp"
  }]}
}`}
      </pre>
    </section>
  );
}

export function Numbers({ t }: { t: LandingCopy }) {
  return (
    <section className="border-y border-line bg-ink text-white">
      <div className={`${wrap} py-20`}>
        <h2 className="text-3xl font-bold">{t.numbers.title}</h2>
        <div className="mt-10 grid gap-8 md:grid-cols-3">
          {t.numbers.items.map((n) => (
            <div key={n.label}>
              <div className="font-mono text-5xl font-extrabold text-neon">{n.value}</div>
              <div className="mt-2 text-white/70">{n.label}</div>
            </div>
          ))}
        </div>
        <p className="mt-10 text-xs text-white/50">{t.numbers.sources}</p>
      </div>
    </section>
  );
}

export function FinalCta({ t }: { t: LandingCopy }) {
  return (
    <section className={`${wrap} py-24 text-center`}>
      <h2 className="mx-auto max-w-3xl text-3xl font-bold md:text-5xl">{t.final.title}</h2>
      <div className="mt-8 flex justify-center gap-3">
        <Link href="/dashboard" className="glow rounded-xl bg-neon px-6 py-4 font-bold text-ink">{t.hero.primary}</Link>
        <Link href={DEMO} className="rounded-xl border border-ink px-6 py-4 font-semibold">{t.hero.secondary}</Link>
      </div>
    </section>
  );
}

export function Footer({ t }: { t: LandingCopy }) {
  return (
    <footer className="border-t border-line">
      <div className={`${wrap} flex flex-col gap-4 py-10 text-sm text-muted md:flex-row md:items-center md:justify-between`}>
        <div className="flex items-center gap-2">
          <img src="/brand/mark.svg" alt="" className="h-6 w-6" /> <span className="text-ink">Pix Actions</span> · {t.footer.tagline}
        </div>
        <div className="flex flex-wrap gap-4">
          <span>{t.footer.built}</span>
          <span>{t.footer.license}</span>
          <span className="font-mono text-neon-ink">{t.footer.network}</span>
          <a href={GITHUB} className="hover:text-ink">GitHub</a>
          <a href={API_DOCS} className="hover:text-ink">API</a>
        </div>
      </div>
    </footer>
  );
}
