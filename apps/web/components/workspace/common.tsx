"use client";
import { useState } from "react";
import { type AttrSource, type RequestDetail } from "@/lib/api";
import { errMsg } from "@/lib/store";
import { refusalHelp } from "@/lib/flow";
import { ApiError } from "@/lib/errors";
import { Badge, type Tone } from "@/components/ui/ui";
import { useToast } from "@/components/toast";

/** onDone: the step finished its job, so move to whatever is next. */
export interface StepProps { det: RequestDetail; onDone: () => void }

/** Runs one write: busy flag, plain-language error plus a suggested fix, success toast. Never optimistic. */
export function useAct() {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [help, setHelp] = useState<string>("");
  async function run<T>(fn: () => Promise<T>, okText?: string): Promise<T | undefined> {
    setBusy(true); setError(null); setHelp("");
    try {
      const out = await fn();
      if (okText) toast.push("ok", okText);
      return out;
    } catch (x) {
      const m = errMsg(x);
      setError(m); setHelp(refusalHelp(m));
      if (x instanceof ApiError && x.status >= 500) toast.push("error", "The server had a problem. Nothing was changed.");
      return undefined;
    } finally { setBusy(false); }
  }
  return { busy, error, help, run, clear: () => { setError(null); setHelp(""); } };
}

const SRC: Record<AttrSource, { text: string; tone: Tone }> = {
  user_input: { text: "You said", tone: "green" }, manufacturer_table: { text: "Published table", tone: "green" }, standard: { text: "Standard", tone: "green" },
  po_history: { text: "Past order", tone: "green" }, nameplate_ocr: { text: "Read from photo", tone: "blue" }, rule: { text: "Rule", tone: "gray" },
  model_inference: { text: "Inferred: confirm", tone: "amber" },
};
export function SourceBadge({ source }: { source: AttrSource }) { const s = SRC[source] ?? { text: source, tone: "gray" as Tone }; return <Badge tone={s.tone}>{s.text}</Badge>; }
