import { useEffect, useState } from "react";

export const routeOf = (href: string): string => {
  const p = href.split("#")[0] || "/";
  return p.startsWith("/") ? p : `/${p}`;
};
export const currentRoute = (): string => routeOf(window.location.hash.replace(/^#/, "") || "/");

export function useRoute(): string {
  const [r, setR] = useState(currentRoute());
  useEffect(() => {
    const on = () => setR(currentRoute());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return r;
}
