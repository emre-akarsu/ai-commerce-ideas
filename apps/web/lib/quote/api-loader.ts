// Loads quote data (quote-draft-ui/1, price-books-ui/1, quote-options-ui/1) from the API.
// Uses the existing bundle format; readers tolerate extra keys. API errors are returned
// without rendering to the UI; failed or unreadable responses never become quotes.
import { readBundle, type Bundle } from "./bundle";
import { parseError } from "../api";

export type BundleLoadResult =
  | { kind: "ok"; bundle: Bundle }
  | { kind: "error"; error: string };

/**
 * Loads a quote and its related data (price book, options) from the API.
 * Returns the same bundle shape the screens already consume.
 * In case of any error, returns a clear error result.
 */
export async function loadBundleFromApi(
  baseUrl: string,
  tenantId: string,
  scopeId: string,
  token: string | null,
): Promise<BundleLoadResult> {
  try {
    // POST /v1/quotes to create/load a quote snapshot
    const quoteRes = await fetch(`${baseUrl}/v1/quotes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        scope_id: scopeId,
        kit: { answers: {}, measurements: {}, allowances: {}, choices: {}, lines: {} },
      }),
    });

    if (!quoteRes.ok) {
      const err = await parseError(quoteRes);
      return { kind: "error", error: `Failed to load quote: ${err.message}` };
    }

    const quoteData = (await quoteRes.json()) as { id: string; quote?: unknown };
    const quoteId = quoteData.id;

    // GET /v1/quotes/{id}/options
    const optionsRes = await fetch(`${baseUrl}/v1/quotes/${encodeURIComponent(quoteId)}/options`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!optionsRes.ok) {
      const err = await parseError(optionsRes);
      return { kind: "error", error: `Failed to load quote options: ${err.message}` };
    }

    const optionsData = await optionsRes.json();

    // GET /v1/price-books?quote_id=
    const priceBookRes = await fetch(
      `${baseUrl}/v1/price-books?quote_id=${encodeURIComponent(quoteId)}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );

    if (!priceBookRes.ok) {
      const err = await parseError(priceBookRes);
      return { kind: "error", error: `Failed to load price book: ${err.message}` };
    }

    const priceBookData = await priceBookRes.json();

    // Assemble into the bundle format
    const bundleRaw = {
      meta: {
        tenant_id: tenantId,
        scope_id: scopeId,
      },
      price_book: priceBookData,
      quote_first: quoteData.quote,
      quote_after_review: quoteData.quote,
      reviewer_decisions: [],
      quote_options: optionsData.options || null,
      options_inputs: optionsData.inputs || null,
    };

    // Read and validate using the existing reader (tolerant of extra keys)
    const bundle = readBundle(bundleRaw, "generated");
    if ("error" in bundle) {
      return { kind: "error", error: `Failed to read quote data: ${bundle.error}` };
    }

    return { kind: "ok", bundle };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return { kind: "error", error: `Failed to load quote: ${message}` };
  }
}

/**
 * Creates a memoized loader function for quote bundles.
 * Useful for React components that may call it multiple times.
 */
export function createApiQuoteLoader(baseUrl: string, token: string | null) {
  const cache = new Map<string, BundleLoadResult>();

  return async (tenantId: string, scopeId: string): Promise<BundleLoadResult> => {
    const key = `${tenantId}/${scopeId}`;
    if (cache.has(key)) {
      return cache.get(key)!;
    }

    const result = await loadBundleFromApi(baseUrl, tenantId, scopeId, token);
    cache.set(key, result);
    return result;
  };
}
