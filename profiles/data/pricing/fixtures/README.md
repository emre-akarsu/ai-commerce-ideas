# Pricing fixtures (SYNTHETIC / ILLUSTRATIVE)

Every file here is invented test data for `packages/components/pricing`. The merchants
(`merchant-alpha` ...), SKUs and prices are not real, not licensed cross-reference data, and must
never be presented as real. They carry the licence tag `synthetic-illustrative`.

- `merchant_prices.csv`: a merchant price file with ex-VAT prices, pack sizes, delivery terms and
  validity; includes a bad price row and a row with no pack size. Title and URL columns are present
  on purpose: the parser never reads them.
- `affiliate_feed.csv`: affiliate-style feed with inc-VAT and ex-VAT price columns.
- `hostile_records.csv`: prompt-injection text in titles and malformed numbers, currencies, ids.
- `search_results.json`: search-result style JSON (always loaded as `search_snapshot`).

The component handles data handed to it only (spec R7); these files are read by the tests and given
to the adapters as text.
