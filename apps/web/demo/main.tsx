import { createRoot } from "react-dom/client";
import "../app/globals.css";
import { AppShell } from "@/components/shell";
import { SessionProvider } from "@/components/session";
import { ToastProvider } from "@/components/toast";
import Inbox from "@/app/page";
import Requests from "@/app/requests/page";
import RequestDetail from "@/app/requests/[id]/page";
import Vendors from "@/app/vendors/page";
import Setup from "@/app/setup/page";
import Audit from "@/app/audit/page";
import Approve from "@/app/approve/[token]/page";
import { useRoute } from "./router";

function Page() {
  const r = useRoute();
  if (r.startsWith("/requests/")) return <RequestDetail key={r} />;
  if (r.startsWith("/approve/")) return <Approve key={r} />;
  if (r === "/requests") return <Requests />;
  if (r === "/vendors") return <Vendors />;
  if (r === "/setup") return <Setup />;
  if (r === "/audit") return <Audit />;
  return <Inbox />;
}

createRoot(document.getElementById("root")!).render(
  <SessionProvider><ToastProvider><AppShell><Page /></AppShell></ToastProvider></SessionProvider>,
);
