// A name from the label map, with its one-sentence tip behind an info button when it has one.
import type * as React from "react";
import { label, tip, type LabelKey } from "@/lib/labels";
import { InfoTip } from "./info-tip";

export function Term({ k, children }: { k: LabelKey; children?: React.ReactNode }) {
  const t = tip(k);
  return <span className="inline-flex items-center gap-1.5">{children ?? label(k)}{t && <InfoTip text={t} label={`About ${label(k).toLowerCase()}`} />}</span>;
}
