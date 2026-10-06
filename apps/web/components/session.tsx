"use client";
// Who is using the app. In mock mode the role is a switcher so every role's view can be seen; otherwise the
// role is read from the bearer token for DISPLAY only. The server decides what is actually allowed.
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { currentToken, isMock } from "@/lib/api";
import { mockGetRole, mockSetRole } from "@/lib/mock";
import { clearCache } from "@/lib/store";
import type { Role } from "@/lib/flow";

interface Sess { role: Role; label: string; setRole: ((r: Role) => void) | null }
const Ctx = createContext<Sess>({ role: "requester", label: "", setRole: null });
export const useSession = (): Sess => useContext(Ctx);

function roleFromToken(tok: string | null): { role: Role; label: string } | null {
  if (!tok) return null;
  try {
    const part = tok.split(".")[1]; if (!part) return null;
    const j = JSON.parse(atob(part.replace(/-/g, "+").replace(/_/g, "/"))) as { sub?: string; app_metadata?: { role?: string } };
    const r = j.app_metadata?.role;
    if (r === "requester" || r === "buyer" || r === "admin") return { role: r, label: String(j.sub ?? "").slice(0, 24) };
  } catch { /* not a decodable token: fall through */ }
  return null;
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const mock = isMock();
  const [role, setRoleState] = useState<Role>(mock ? mockGetRole() : "requester");
  const [label, setLabel] = useState(mock ? "Demo user (synthetic)" : "");
  useEffect(() => {
    if (mock) return;
    currentToken().then((t) => { const r = roleFromToken(t); if (r) { setRoleState(r.role); setLabel(r.label); } });
  }, [mock]);
  const value = useMemo<Sess>(() => ({ role, label, setRole: mock ? (r) => { mockSetRole(r); clearCache(); setRoleState(r); } : null }), [role, label, mock]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
