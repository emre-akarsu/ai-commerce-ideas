// Render checks for the Price books screens (server markup, no browser). They pin what a person sees:
// the VAT basis is unselected, the upload cannot be sent until it is complete, the RFQ action says
// nothing is sent, and mock mode is unchanged and makes no network call.
import { describe, it, expect, afterEach, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { PriceFileUpload } from "@/components/quote/price-file-upload";
import { RfqPrepare } from "@/components/quote/rfq-prepare";
import { PriceBooksApp, RfqDialog, UploadDialog } from "@/components/quote/price-books-app";
import { readBundle } from "@/lib/quote/bundle";
import { GENERATED } from "@/lib/quote/generated";
import { forgetQuote, rememberQuote } from "@/lib/quote/current-quote";

const MERCHANTS = [{ merchantId: "acme-supply", name: "Acme Supply" }];

/** Decodes the few entities React writes into text, so assertions read like the screen. */
function text(html: string): string {
  return html.replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}

function book() {
  const b = readBundle(GENERATED["demo-tenant-a/full"], "generated");
  if ("error" in b || !b.priceBook.ok) throw new Error("fixture did not read");
  return b.priceBook.book;
}

/** True when the tag carries the real disabled attribute (not the Tailwind "disabled:" class variant). */
function isDisabled(tag: string): boolean {
  return /\sdisabled=""/.test(tag);
}

/** The opening tag of the first element that carries the given attribute snippet. */
function tagWith(html: string, snippet: string): string {
  const i = html.indexOf(snippet);
  if (i < 0) return "";
  const start = html.lastIndexOf("<", i);
  return html.slice(start, html.indexOf(">", i) + 1);
}

afterEach(() => {
  forgetQuote();
  vi.unstubAllGlobals();
  delete process.env.NEXT_PUBLIC_API_MOCK;
});

describe("PriceFileUpload (API mode form)", () => {
  const html = () => text(renderToStaticMarkup(<PriceFileUpload merchants={MERCHANTS} onLoaded={async () => {}} />));

  it("leaves the VAT basis unselected: no radio is checked", () => {
    const out = html();
    expect(out).toContain('name="vat_basis"');
    expect(out).not.toMatch(/<input[^>]*type="radio"[^>]*checked/);
  });

  it("cannot be sent while the form is incomplete, and says what is still needed", () => {
    const out = html();
    expect(isDisabled(tagWith(out, 'data-act="upload-price-file"'))).toBe(true);
    expect(out).toContain("Still needed:");
    expect(out).toContain("VAT basis");
    expect(out).toContain("Merchant");
    expect(out).toContain("File");
  });

  it("states the attestation in plain words", () => {
    expect(html()).toContain("I confirm I may use this file for my own company's purchases.");
  });

  it("explains that without attestation and a validity date the prices are indicative only", () => {
    const out = html();
    expect(out).toContain("indicative only");
    expect(out).toContain("valid-until date");
    expect(out).toContain("never used as firm prices");
  });

  it("offers the merchant from the loaded price book", () => {
    expect(html()).toContain(">Acme Supply<");
  });

  it("uses CSV and Excel as the only file types offered", () => {
    expect(html()).toContain('accept=".csv,.xlsx,');
  });
});

describe("RfqPrepare (Request quotes action)", () => {
  const names = new Map([["acme-supply", "Acme Supply"]]);

  it("is disabled with an explanation when there is no saved quote yet", () => {
    const out = text(renderToStaticMarkup(<RfqPrepare quoteId={null} mode="per_supplier" messageCount={2} names={names} />));
    expect(isDisabled(tagWith(out, 'data-act="prepare-rfqs"'))).toBe(true);
    expect(out).toContain("Prepare is off until there is a saved quote");
  });

  it("says nothing is sent until a person approves the exact text", () => {
    const out = text(renderToStaticMarkup(<RfqPrepare quoteId="quote-1" mode="per_supplier" messageCount={2} names={names} />));
    expect(out).toContain("Prepare for approval: nothing is sent until a person approves the exact text");
    expect(isDisabled(tagWith(out, 'data-act="prepare-rfqs"'))).toBe(false);
    expect(out).toContain("2 messages will be prepared. Nothing is sent by this step.");
  });

  it("is disabled when there is nothing to prepare", () => {
    const out = text(renderToStaticMarkup(<RfqPrepare quoteId="quote-1" mode="per_item" messageCount={0} names={names} />));
    expect(isDisabled(tagWith(out, 'data-act="prepare-rfqs"'))).toBe(true);
    expect(out).toContain("nothing to prepare");
  });
});

describe("UploadDialog and RfqDialog modes", () => {
  it("upload: API mode shows the real form, mock mode keeps the static example", () => {
    const api = text(renderToStaticMarkup(<UploadDialog api merchants={MERCHANTS} onLoaded={async () => {}} onClose={() => {}} />));
    expect(api).toContain("data-upload-form");
    expect(api).not.toContain("Static example only");

    const mock = text(renderToStaticMarkup(<UploadDialog api={false} merchants={MERCHANTS} onLoaded={async () => {}} onClose={() => {}} />));
    expect(mock).toContain("Static example only. Nothing is uploaded here");
    expect(mock).not.toContain("data-upload-form");
  });

  it("rfq: API mode prepares for approval (disabled without a quote), mock mode keeps the demo button", () => {
    const api = text(renderToStaticMarkup(<RfqDialog book={book()} api tenant="demo-tenant-a" scope="bathroom_full" onClose={() => {}} />));
    expect(api).toContain("Quote requests for these gaps");
    expect(api).toContain("Nothing is sent from this screen");
    expect(isDisabled(tagWith(api, 'data-act="prepare-rfqs"'))).toBe(true);
    expect(api).not.toContain("data-demo-button");
    expect(api).not.toContain("Demo only");

    const mock = text(renderToStaticMarkup(<RfqDialog book={book()} api={false} tenant="demo-tenant-a" scope="bathroom_full" onClose={() => {}} />));
    expect(mock).toContain("Send RFQ for these gaps");
    expect(mock).toContain("data-demo-button");
    expect(mock).not.toContain("data-act=\"prepare-rfqs\"");
  });

  it("rfq: API mode enables the action once the quote for this tenant and scope is held", () => {
    rememberQuote("demo-tenant-a", "bathroom_full", "quote-1");
    const api = text(renderToStaticMarkup(<RfqDialog book={book()} api tenant="demo-tenant-a" scope="bathroom_full" onClose={() => {}} />));
    expect(isDisabled(tagWith(api, 'data-act="prepare-rfqs"'))).toBe(false);
  });
});

describe("PriceBooksApp in mock mode", () => {
  it("renders the demo book with the demo labels and makes no network call", () => {
    process.env.NEXT_PUBLIC_API_MOCK = "1";
    const fetchSpy = vi.fn(() => { throw new Error("network must not be used in mock mode"); });
    vi.stubGlobal("fetch", fetchSpy);
    const out = text(renderToStaticMarkup(<PriceBooksApp />));
    expect(out).toContain("data-summary");
    expect(out).toContain("Upload price file");
    expect(out).toContain("Send RFQ for these gaps");
    expect(out).toContain("Synthetic");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
