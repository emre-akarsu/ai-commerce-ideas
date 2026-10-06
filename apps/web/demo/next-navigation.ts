import { routeOf, useRoute } from "./router";

export const usePathname = (): string => useRoute();
export const useRouter = () => ({
  push: (href: string) => { window.location.hash = routeOf(href); },
  replace: (href: string) => { window.location.replace(`#${routeOf(href)}`); },
  back: () => window.history.back(),
  prefetch: () => undefined,
});
export function useParams<T extends Record<string, string>>(): T {
  const route = useRoute();
  const m = route.match(/^\/requests\/([^/]+)$/) ?? route.match(/^\/approve\/([^/]+)$/);
  const key = route.startsWith("/approve/") ? "token" : "id";
  return (m ? { [key]: decodeURIComponent(m[1]) } : {}) as T;
}
