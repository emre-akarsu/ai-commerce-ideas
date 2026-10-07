"use client";
// "Prepare for approval" for the Price books RFQ dialog (API mode only). It asks the API to prepare the
// messages for the saved quote. The API only holds them; a person approves each exact text on the Requests
// screen before anything is sent. A refusal (409) is shown verbatim and is never a success.
import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/ui";
import { baseUrl, currentToken } from "@/lib/api";
import { explainRfqError, type ErrorView } from "@/lib/quote/price-file-result";
import { prepareRfqDrafts, summariseDrafts, type DraftSummary, type RfqMode } from "@/lib/quote/rfq-drafts-client";

export interface RfqPrepareProps {
  quoteId: string | null;
  mode: RfqMode;
  /** How many messages the preview above shows for this mode. */
  messageCount: number;
  names: ReadonlyMap<string, string>;
}

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`;

export function RfqPrepare({ quoteId, mode, messageCount, names }: RfqPrepareProps) {
  const [busy, setBusy] = useState(false);
  const [waiting, setWaiting] = useState<DraftSummary[] | null>(null);
  const [error, setError] = useState<ErrorView | null>(null);

  const blocked = quoteId === null ? "Prepare is off until there is a saved quote for this customer and job. Open the Quote screen for this job, then come back here."
    : messageCount === 0 ? "There is nothing to prepare: every line already has a firm price."
    : null;
  const canPrepare = !busy && blocked === null && quoteId !== null;

  async function prepare() {
    if (!canPrepare || quoteId === null) return;
    setBusy(true); setError(null); setWaiting(null);
    try {
      const drafts = await prepareRfqDrafts({ baseUrl: baseUrl(), token: await currentToken(), quoteId, mode });
      setWaiting(summariseDrafts(drafts, names));
    } catch (err) {
      setError(explainRfqError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3" data-rfq-prepare>
      {blocked && <p className="rounded-md bg-sunken p-2 text-sm text-mute" data-rfq-blocked>{blocked}</p>}
      <Button type="button" onClick={prepare} disabled={!canPrepare} data-act="prepare-rfqs" className="w-full whitespace-normal text-left sm:w-auto">
        {busy ? "Preparing..." : `Prepare for approval: nothing is sent until a person approves the exact text`}
      </Button>
      {!blocked && !busy && waiting === null && error === null && (
        <p className="text-xs text-mute" data-rfq-count>{plural(messageCount, "message", "messages")} will be prepared. Nothing is sent by this step.</p>
      )}

      {error && (
        <div role="alert" className="rounded-md border border-bad p-3 text-sm" data-rfq-refusal>
          <p className="font-semibold">{error.explanation}</p>
          <p className="mt-1 break-words text-xs text-mute">
            Server said{error.status !== null ? ` (HTTP ${error.status}${error.code ? `, ${error.code}` : ""})` : ""}: <span className="text-ink">{error.verbatim}</span>
          </p>
        </div>
      )}

      {waiting !== null && (
        <section role="status" aria-label="Waiting for approval" className="rounded-md border border-line p-3 text-sm" data-rfq-waiting>
          {waiting.length === 0 ? (
            <p>The server prepared no messages. Nothing was sent.</p>
          ) : (
            <>
              <p className="font-semibold">{plural(waiting.length, "message is", "messages are")} waiting for approval. Nothing has been sent.</p>
              <ul className="mt-2 list-disc space-y-1 pl-5" data-rfq-waiting-list>
                {waiting.map((w) => (
                  <li key={w.rfqId} data-rfq-waiting-item={w.merchantId}>{w.label}: {plural(w.lines, "line", "lines")}</li>
                ))}
              </ul>
            </>
          )}
          <p className="mt-2">
            <Link href="/requests" className="font-semibold text-accent underline">Open Requests to read and approve the exact text</Link>
          </p>
        </section>
      )}
    </div>
  );
}
