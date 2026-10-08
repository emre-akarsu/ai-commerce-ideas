// The one place the app's names live (docs/mvp/ux-audit/04-redesign-brief.md, section 3). A screen asks for a
// label by key, and shows the tip, when there is one, behind an info button, never as inline prose. One
// word per thing: Supplier (not merchant or vendor), Quote request (not RFQ), Rough price (not indicative).
// Pure data, no React: used by components, calculations and tests alike.

export interface LabelDef { label: string; tip?: string }

export const LABELS = {
  // ---- navigation
  home: { label: "Home" },
  quote_a_job: { label: "Quote a job" },
  requests: { label: "Requests" },
  suppliers: { label: "Suppliers" },
  setup: { label: "Setup" },
  activity: { label: "Activity", tip: "A dated record of every step on every request, kept so it can be checked later." },
  // ---- the journey (one word each, with the question the screen answers)
  stage_job: { label: "Job", tip: "What's the job?" },
  stage_prices: { label: "Prices", tip: "Who has prices?" },
  stage_quote: { label: "Quote", tip: "What will it cost?" },
  stage_compare: { label: "Compare", tip: "Best way to buy" },
  stage_ask: { label: "Ask suppliers", tip: "Send quote requests" },
  // ---- nouns
  supplier: { label: "Supplier" },
  supplier_prices: { label: "Supplier prices", tip: "Which suppliers have a current price for this job, and what is missing." },
  supplier_price: { label: "Supplier price", tip: "One supplier's price for one product, with the date it was seen and whether VAT is included." },
  materials_list: { label: "Materials list", tip: "A ready-made list of materials for one kind of job. You answer a few questions and check quantities." },
  job_type: { label: "Job type", tip: "The kind of work this quote covers, for example WC only or Full bathroom." },
  quote_request: { label: "Quote request", tip: "A message asking a supplier to price the listed parts. Nothing is sent until a person approves it." },
  part_description: { label: "Part description", tip: "What you need, in writing: size, type, rating and finish." },
  part_number: { label: "Part number", tip: "The manufacturer's part number." },
  product_code: { label: "Product code", tip: "The code this system uses for the product in its catalogue." },
  // ---- prices
  confirmed_price: { label: "Confirmed price", tip: "A confirmed price that counts in totals: from a price file you confirmed or a real supplier reply." },
  rough_price: { label: "Rough price", tip: "A rough guide from past invoices or shop listings. It is never added to a total and is not a quote." },
  no_price: { label: "No price yet", tip: "Lines no supplier currently has a usable price for." },
  needs_choice: { label: "Needs your choice", tip: "The system could not decide which product fits. Choose one, or none." },
  skipped: { label: "Skipped", tip: "Left out by you, or a quantity of zero." },
  no_match: { label: "No match", tip: "The system could not match this line to a product, so it has no price." },
  out_of_date: { label: "Out of date", tip: "Older than the allowed age, so it is shown but not used." },
  on_hold: { label: "On hold", tip: "Held back and not used because a check failed. A person must look at it." },
  includes_vat: { label: "Price includes VAT?", tip: "Say whether the price includes VAT. A price without this answer cannot be compared." },
  ex_vat: { label: "ex VAT" },
  inc_vat: { label: "inc VAT" },
  confirm_prices: { label: "Confirm", tip: "You confirm the file is valid and say whether VAT is included. Without this its prices stay rough." },
  delivered_cost: { label: "Delivered cost", tip: "The price per unit, including delivery to you." },
  waste_allowance: { label: "Waste allowance", tip: "An extra percentage added for waste and offcuts. Change it if you know better." },
  // ---- price source levels 0 to 4 (words, not numbers)
  source: { label: "Source", tip: "How the price was obtained, from on request to a contract feed." },
  source_0: { label: "On request" },
  source_1: { label: "Past invoices" },
  source_2: { label: "Price file" },
  source_3: { label: "Regular price file" },
  source_4: { label: "Contract feed" },
  // ---- finish and match
  finish: { label: "Finish", tip: "Budget, Standard or Premium. It sets the default product on each line." },
  finish_budget: { label: "Budget" },
  finish_standard: { label: "Standard" },
  finish_premium: { label: "Premium" },
  match: { label: "Match", tip: "How closely an offered part matches the one asked for." },
  match_a: { label: "Same part" },
  match_b: { label: "Equivalent", tip: "A documented equivalent. Accept it for this request only if it fits." },
  match_c: { label: "Possible", tip: "Matches by rule only, with no published source. Needs your say-so." },
  match_d: { label: "Needs an expert", tip: "An engineer must confirm the part fits before any price is used." },
  source_quality: { label: "Source quality", tip: "A to D: A is a rule or maker spec, B merchant data, C one retailer, D a forum or unverified source." },
  possible_match: { label: "Possible match", tip: "A product that might match this line. Choose one, or none." },
  we_assumed: { label: "We assumed", tip: "Values the system filled in without being told. Check each one." },
  // ---- ways to buy
  ways_to_buy: { label: "Ways to buy", tip: "Different ways of buying the same lines from a mix of suppliers." },
  supplier_mix: { label: "Supplier mix", tip: "One way of buying all the lines, split across suppliers." },
  kind_cheapest: { label: "Lowest total" },
  kind_fewest_deliveries: { label: "Fewest deliveries" },
  kind_fastest: { label: "Fastest" },
  kind_single_supplier: { label: "One supplier" },
  kind_preferred: { label: "Preferred suppliers" },
  kind_balanced: { label: "Best overall", tip: "Scored against the budget, date and delivery limit you gave. It is not a recommendation." },
  // ---- people and safety
  second_person: { label: "Second person", tip: "A second person, not the one who asked, who must approve before anything is sent or ordered." },
  asker: { label: "The person who asked", tip: "The person who raised the request." },
  do_not_contact: { label: "Do not contact", tip: "This supplier asked not to be contacted, or an admin has blocked contact. Only an admin can reverse it." },
  stop_sending: { label: "Stop all sending", tip: "One switch that stops every message from this account. Queued messages are refused." },
  warning: { label: "Warning", tip: "A problem found in a reply, such as no currency or an expired quote. Red ones block selection." },
  sender_check: { label: "Sender check", tip: "Checks that the reply really came from the supplier's own domain. A failed check holds the reply back." },
  tamper_check: { label: "Tamper check", tip: "A code that changes if any earlier entry is edited." },
  // ---- demo
  demo_data: { label: "Demo data", tip: "Made-up data for demonstration. Not real parts, prices, suppliers or customers. Nothing is sent." },
  not_a_quote: { label: "Not a supplier quote", tip: "A comparison of prices observed in the data sources, at the times shown. It is not an offer that can be accepted and not a reservation of stock. Nothing is sent or ordered." },
} as const satisfies Record<string, LabelDef>;

export type LabelKey = keyof typeof LABELS;

export const label = (key: LabelKey): string => LABELS[key].label;
export const tip = (key: LabelKey): string | undefined => (LABELS[key] as LabelDef).tip;

/** Price source level 0 to 4 as a word; anything else is "On request" (the least trusted). */
export function sourceWord(level: number): string {
  const key = `source_${level}` as LabelKey;
  return key in LABELS ? LABELS[key].label : LABELS.source_0.label;
}

const FINISH_KEYS: Record<string, LabelKey> = { budget: "finish_budget", most_used: "finish_standard", standard: "finish_standard", premium: "finish_premium" };
/** A finish setting by its stored value. Unknown values are shown as they are, tidied. */
export function finishWord(value: string): string {
  const key = FINISH_KEYS[value];
  return key ? LABELS[key].label : value.replace(/_/g, " ");
}

const MATCH_KEYS: Record<string, LabelKey> = { A: "match_a", B: "match_b", C: "match_c", D: "match_d" };
export function matchWord(tier: string): string {
  const key = MATCH_KEYS[tier.toUpperCase()];
  return key ? LABELS[key].label : tier;
}
