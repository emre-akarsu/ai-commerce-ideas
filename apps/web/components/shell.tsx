"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MockBanner, Badge, Kbd } from "@/components/ui/ui";
import { Modal } from "@/components/modal";
import { useSession } from "@/components/session";
import { useProfile } from "@/lib/profile";
import { useNeedsYouCount } from "@/lib/inbox";
import { peek } from "@/lib/store";
import { can, humanise, type Capability, type Role } from "@/lib/flow";
import type { RequestView } from "@/lib/api";
import { cn } from "@/lib/utils";

interface NavItem { href: string; label: string; short: string; cap?: Capability; key: string }
const NAV: NavItem[] = [
  { href: "/", label: "Inbox", short: "Inbox", key: "i" },
  { href: "/requests", label: "Requests", short: "Requests", key: "r" },
  { href: "/vendors", label: "Suppliers", short: "Suppliers", key: "s" },
  { href: "/kits", label: "Job kits", short: "Kits", key: "t" },
  { href: "/price-books", label: "Price books", short: "Prices", key: "p" },
  { href: "/quote", label: "Quote", short: "Quote", key: "q" },
  { href: "/setup", label: "Setup", short: "Setup", cap: "view_setup", key: "u" },
  { href: "/audit", label: "Audit", short: "Audit", cap: "view_audit", key: "a" },
];
const isActive = (path: string, href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`));
const typing = (t: EventTarget | null): boolean => {
  const el = t as HTMLElement | null;
  return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT" || el.isContentEditable);
};

interface Cmd { id: string; label: string; hint?: string; run: () => void }

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { role, label, setRole } = useSession();
  const profile = useProfile();
  const needs = useNeedsYouCount();
  const [palette, setPalette] = useState(false);
  const [help, setHelp] = useState(false);
  const chord = useRef<{ g: boolean; t: ReturnType<typeof setTimeout> | null }>({ g: false, t: null });

  const go = useCallback((href: string) => { setPalette(false); router.push(href); }, [router]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((v) => !v); return; }
      if (e.ctrlKey || e.metaKey || e.altKey || typing(e.target) || document.querySelector('[role="dialog"]')) return;
      if (e.key === "/") { e.preventDefault(); setPalette(true); return; }
      if (e.key === "?") { e.preventDefault(); setHelp(true); return; }
      if (e.key === "n") { e.preventDefault(); go("/#new"); return; }
      if (chord.current.g) {
        chord.current.g = false; if (chord.current.t) clearTimeout(chord.current.t);
        const hit = NAV.find((n) => n.key === e.key);
        if (hit) { e.preventDefault(); go(hit.href); }
        return;
      }
      if (e.key === "g") { chord.current.g = true; chord.current.t = setTimeout(() => { chord.current.g = false; }, 1200); }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  // The approver arrives from an emailed link: a bare page with no navigation to other areas.
  if (path.startsWith("/approve/")) {
    return (
      <div className="min-h-screen">
        <MockBanner />
        <header className="border-b border-line bg-surface px-4 py-3"><p className="mx-auto max-w-xl text-sm font-semibold">Buy-side RFQ: approval</p></header>
        <main id="main" tabIndex={-1} className="mx-auto w-full max-w-xl px-4 py-6 outline-none">{children}</main>
      </div>
    );
  }
  return (
    <div className="min-h-screen md:grid md:grid-cols-[232px_minmax(0,1fr)]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">Skip to content</a>
      <aside className="sticky top-0 hidden h-screen flex-col border-r border-line bg-surface md:flex">
        <div className="px-4 py-4"><p className="text-sm font-semibold tracking-tight">Buy-side RFQ</p><p className="text-xs text-mute">Quotes from your own suppliers</p></div>
        <nav aria-label="Main" className="flex-1 space-y-0.5 px-2">
          {NAV.map((n) => {
            const gate = n.cap ? can(role, n.cap) : { ok: true as const };
            return (
              <Link key={n.href} href={n.href} aria-current={isActive(path, n.href) ? "page" : undefined}
                className={cn("flex min-h-target items-center justify-between rounded-md px-3 text-sm font-medium hover:bg-sunken", isActive(path, n.href) && "bg-accent-soft text-accent")}>
                <span>{n.label}</span>
                {n.href === "/" && needs !== null && needs > 0 && <Badge tone="blue">{needs}</Badge>}
                {!gate.ok && <span className="text-xs text-mute" title={gate.reason}>admin</span>}
              </Link>
            );
          })}
        </nav>
        <div className="space-y-2 border-t border-line p-3 text-xs text-mute">
          <p>Profile <span className="font-mono text-ink">{profile.id}@{profile.digest.slice(0, 8) || "default"}</span></p>
          <p>Press <Kbd>?</Kbd> for shortcuts</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <MockBanner />
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-line bg-surface/95 px-4 py-2 backdrop-blur">
          <p className="text-sm font-semibold md:hidden">Buy-side RFQ</p>
          <button onClick={() => setPalette(true)} className="ml-auto flex min-h-target items-center gap-2 rounded-md border border-strong bg-surface px-3 text-sm text-mute hover:bg-sunken md:ml-0 md:min-w-72" aria-label="Search or jump to anything">
            <span>Search or jump</span><span className="ml-auto hidden md:inline"><Kbd>Ctrl</Kbd> <Kbd>K</Kbd></span>
          </button>
          <div className="ml-auto hidden items-center gap-2 md:flex">
            {setRole ? (
              <label className="flex items-center gap-2 text-xs text-mute">Demo role
                <select value={role} onChange={(e) => setRole(e.target.value as Role)} className="min-h-target rounded-md border border-strong bg-surface px-2 text-sm text-ink">
                  <option value="requester">Requester</option><option value="buyer">Buyer</option><option value="admin">Admin</option>
                </select>
              </label>
            ) : <Badge tone="gray">{humanise(role)}{label ? ` · ${label}` : ""}</Badge>}
          </div>
        </header>
        <main id="main" tabIndex={-1} className="mx-auto w-full max-w-5xl flex-1 px-4 py-5 pb-28 outline-none md:px-6 md:pb-10">{children}</main>
      </div>

      <nav aria-label="Main (mobile)" className="fixed inset-x-0 bottom-0 z-30 flex overflow-x-auto border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] md:hidden">
        {NAV.map((n) => (
          <Link key={n.href} href={n.href} aria-current={isActive(path, n.href) ? "page" : undefined}
            className={cn("flex min-h-14 min-w-[4.5rem] flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium", isActive(path, n.href) ? "text-accent" : "text-mute")}>
            <span>{n.short}</span>
            {n.href === "/" && needs !== null && needs > 0 && <span className="rounded-full bg-accent px-1.5 text-[10px] text-accent-ink">{needs}</span>}
          </Link>
        ))}
      </nav>

      <Palette open={palette} onClose={() => setPalette(false)} go={go} role={role} />
      <ShortcutHelp open={help} onClose={() => setHelp(false)} />
    </div>
  );
}

function Palette({ open, onClose, go, role }: { open: boolean; onClose: () => void; go: (href: string) => void; role: Role }) {
  const [q, setQ] = useState("");
  const [i, setI] = useState(0);
  useEffect(() => { if (open) { setQ(""); setI(0); } }, [open]);
  const cmds = useMemo<Cmd[]>(() => {
    const out: Cmd[] = [{ id: "new", label: "New request", hint: "n", run: () => go("/#new") }];
    for (const n of NAV) {
      const g = n.cap ? can(role, n.cap) : { ok: true as const };
      out.push({ id: `go-${n.href}`, label: `Go to ${n.label}`, hint: `g ${n.key}`, run: () => go(n.href) });
      void g;
    }
    const reqs = (open ? peek<RequestView[]>("requests") : undefined) ?? [];
    for (const r of reqs.slice(0, 12)) out.push({ id: `rq-${r.id}`, label: `Open ${r.id}: ${humanise(r.family ?? "request")} x${r.quantity ?? "?"}`, hint: humanise(r.state.toLowerCase()), run: () => go(`/requests/${r.id}`) });
    return out;
  }, [go, role, open]);
  const shown = cmds.filter((c) => c.label.toLowerCase().includes(q.trim().toLowerCase()));
  useEffect(() => { setI(0); }, [q]);
  function onKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") { e.preventDefault(); setI((n) => Math.min(shown.length - 1, n + 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setI((n) => Math.max(0, n - 1)); }
    else if (e.key === "Enter" && shown[i]) { e.preventDefault(); shown[i].run(); }
  }
  return (
    <Modal open={open} onClose={onClose} label="Search or jump">
      <input data-autofocus value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={onKey} placeholder="Type to search requests and pages"
        aria-label="Search or jump" role="combobox" aria-expanded="true" aria-controls="palette-list" aria-activedescendant={shown[i] ? `pal-${shown[i].id}` : undefined}
        className="w-full border-b border-line bg-transparent px-4 py-3 text-base outline-none" />
      <ul id="palette-list" role="listbox" className="max-h-80 overflow-y-auto p-2">
        {shown.length === 0 && <li className="px-3 py-6 text-center text-sm text-mute">Nothing matches &ldquo;{q}&rdquo;.</li>}
        {shown.map((c, k) => (
          <li key={c.id} id={`pal-${c.id}`} role="option" aria-selected={k === i} onMouseEnter={() => setI(k)} onClick={() => c.run()}
            className={cn("flex min-h-target cursor-pointer items-center justify-between rounded-md px-3 text-sm", k === i && "bg-accent-soft text-accent")}>
            <span className="truncate">{c.label}</span>{c.hint && <span className="ml-3 shrink-0 text-xs text-mute">{c.hint}</span>}
          </li>
        ))}
      </ul>
    </Modal>
  );
}

function ShortcutHelp({ open, onClose }: { open: boolean; onClose: () => void }) {
  const rows: Array<[string, string]> = [
    ["Ctrl/Cmd K or /", "Search or jump"], ["n", "New request"], ["g then i / r / s / t / p / q / u / a", "Go to Inbox / Requests / Suppliers / Job kits / Price books / Quote / Setup / Audit"],
    ["j and k", "Move down and up a list"], ["Enter", "Open the focused item"], [".", "Focus the next-action button (it never presses it)"],
    ["Esc", "Close a dialog"], ["?", "This help"],
  ];
  return (
    <Modal open={open} onClose={onClose} label="Keyboard shortcuts">
      <div className="p-5">
        <h2 className="mb-3 text-base font-semibold">Keyboard shortcuts</h2>
        <dl className="space-y-2 text-sm">
          {rows.map(([k, d]) => <div key={k} className="flex justify-between gap-4"><dt><Kbd>{k}</Kbd></dt><dd className="text-right text-mute">{d}</dd></div>)}
        </dl>
        <p className="mt-4 text-xs text-mute">Sending and approving always need a deliberate click on the button. No shortcut presses it.</p>
        <button data-autofocus onClick={onClose} className="mt-4 min-h-target rounded-md border border-strong px-4 text-sm font-semibold hover:bg-sunken">Close</button>
      </div>
    </Modal>
  );
}

/** j / k move focus between `[data-nav-item]` elements inside the container; Enter then follows the focused link. */
export function useListNav(ref: React.RefObject<HTMLElement | null>): void {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.key !== "j" && e.key !== "k") || e.ctrlKey || e.metaKey || e.altKey || typing(e.target) || document.querySelector('[role="dialog"]')) return;
      const root = ref.current; if (!root) return;
      const items = [...root.querySelectorAll<HTMLElement>("[data-nav-item]")]; if (items.length === 0) return;
      const at = items.indexOf(document.activeElement as HTMLElement);
      const next = e.key === "j" ? Math.min(items.length - 1, at + 1) : Math.max(0, at <= 0 ? 0 : at - 1);
      e.preventDefault(); items[next].focus(); items[next].scrollIntoView({ block: "nearest" });
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [ref]);
}
