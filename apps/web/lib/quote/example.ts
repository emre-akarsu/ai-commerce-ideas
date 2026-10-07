// Static example shown by "Upload price file". It is NOT read from the customer's data and nothing here was uploaded.
export const IMPORT_EXAMPLE = {
  file: "example_trade_prices.csv (static example, not your file)",
  rows: 232, accepted: 212, quarantined: 20,
  reasons: [
    { code: "vat_basis_missing", count: 12, text: "Row has no VAT basis (ex VAT or inc VAT). Not used until you say which." },
    { code: "price_outlier", count: 4, text: "Price is about four times the median for the same product. Held for your check." },
    { code: "unit_not_convertible", count: 3, text: "Priced per 100 pieces but the pack size is not stated, so it cannot be compared." },
    { code: "expired_row", count: 1, text: "Row says it was valid until a date that has passed." },
  ],
  attest: ["The prices in this file are valid until the date you enter.", "You have said whether the prices are ex VAT or inc VAT.", "You are allowed to use this file in this way."],
};
