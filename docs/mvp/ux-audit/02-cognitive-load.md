# 02 Cognitive load: what each screen puts in front of the reader

Counts were read from the page's DOM at the moment each screenshot was taken. Source: the mock demo built from the apps/web source as last changed in commit `9c5e554` (no uncommitted changes under apps/web). Repository HEAD when captured: `5ee9a60`. Captured 2026-10-08T00:05:08.553Z by `docs/mvp/ux-audit/tools/capture.mjs`. Screenshots: `docs/mvp/screenshots/audit/` (36 files). All data is the synthetic, illustrative seed, labelled as such on screen.

Each row is one screen state. A higher number means more to take in at once. These are counts, not a score. The method note explains each column and what it cannot show.

## Desktop, 1280 × 800 (light, plus 4 dark rows)

| Screen | Visible words | Controls | Headings (h1-h4) | Pills | Numbers in first viewport | Distinct text colours | Distinct background colours | Max nesting depth | Page scrolls sideways | Controls outside main |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| [Job kits: scope step (choose a job)](../screenshots/audit/audit-kits-scope-desktop-light.png) | 404 | 12 | 3 | 13 | 1 | 4 | 4 | 9 | no | 15 |
| [Job kits: questions step (bathroom full, default answers)](../screenshots/audit/audit-kits-questions-desktop-light.png) | 346 | 17 | 2 | 7 | 7 | 4 | 6 | 10 | no | 15 |
| [Job kits: measure step](../screenshots/audit/audit-kits-measure-desktop-light.png) | 153 | 17 | 3 | 3 | 10 | 4 | 5 | 10 | no | 15 |
| [Job kits: review step (defaults filled in)](../screenshots/audit/audit-kits-review-desktop-light.png) | 704 | 93 | 6 | 65 | 8 | 4 | 7 | 13 | no | 15 |
| [Job kits: review step (defaults filled in) (dark)](../screenshots/audit/audit-kits-review-desktop-dark.png) | 704 | 93 | 6 | 65 | 8 | 4 | 7 | 13 | no | 15 |
| [Job kits: summary step](../screenshots/audit/audit-kits-summary-desktop-light.png) | 1,589 | 15 | 25 | 2 | 23 | 4 | 7 | 12 | no | 15 |
| [Price books (default customer A)](../screenshots/audit/audit-price-books-desktop-light.png) | 1,019 | 17 | 8 | 10 | 30 | 6 | 5 | 8 | no | 15 |
| [Price books (default customer A) (dark)](../screenshots/audit/audit-price-books-desktop-dark.png) | 1,019 | 17 | 8 | 10 | 30 | 6 | 5 | 8 | no | 15 |
| [Price books: Request price file dialog (customer B)](../screenshots/audit/audit-price-books-request-desktop-light.png) | 1,284 | 24 | 9 | 10 | 20 | 7 | 8 | 8 | no | 15 |
| [Price books: Upload price file dialog](../screenshots/audit/audit-price-books-upload-desktop-light.png) | 1,219 | 23 | 12 | 14 | 25 | 7 | 8 | 8 | no | 15 |
| [Price books: Request quotes dialog, Send RFQ for these gaps (customer B)](../screenshots/audit/audit-price-books-rfq-desktop-light.png) | 1,149 | 31 | 9 | 10 | 23 | 7 | 8 | 8 | no | 15 |
| [Quote: first quote (default customer A, bathroom full)](../screenshots/audit/audit-quote-desktop-light.png) | 4,255 | 87 | 21 | 38 | 5 | 7 | 11 | 10 | no | 15 |
| [Quote: first quote (default customer A, bathroom full) (dark)](../screenshots/audit/audit-quote-desktop-dark.png) | 4,255 | 87 | 21 | 38 | 5 | 7 | 11 | 10 | no | 15 |
| [Quote: scrolled to Options](../screenshots/audit/audit-quote-options-desktop-light.png) | 4,255 | 87 | 21 | 38 | 38 | 7 | 11 | 10 | no | 15 |
| [Inbox (#/)](../screenshots/audit/audit-inbox-desktop-light.png) | 207 | 12 | 8 | 8 | 18 | 5 | 5 | 8 | no | 10 |
| [Inbox (#/) (dark)](../screenshots/audit/audit-inbox-desktop-dark.png) | 207 | 12 | 8 | 8 | 18 | 5 | 5 | 8 | no | 10 |
| [Requests (#/requests)](../screenshots/audit/audit-requests-desktop-light.png) | 152 | 12 | 1 | 9 | 24 | 5 | 4 | 7 | no | 10 |
| [Suppliers (#/vendors)](../screenshots/audit/audit-suppliers-desktop-light.png) | 149 | 13 | 1 | 7 | 13 | 6 | 5 | 7 | no | 10 |
| [Setup (#/setup)](../screenshots/audit/audit-setup-desktop-light.png) | 181 | 2 | 4 | 8 | 2 | 6 | 6 | 7 | no | 10 |
| [Audit trail (#/audit)](../screenshots/audit/audit-audit-desktop-light.png) | 94 | 3 | 1 | 1 | 34 | 3 | 3 | 6 | no | 10 |

## Mobile, 390 × 844 (light)

| Screen | Visible words | Controls | Headings (h1-h4) | Pills | Numbers in first viewport | Distinct text colours | Distinct background colours | Max nesting depth | Page scrolls sideways | Controls outside main |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| [Job kits: scope step (choose a job)](../screenshots/audit/audit-kits-scope-mobile-light.png) | 404 | 12 | 3 | 13 | 1 | 4 | 4 | 9 | no | 14 |
| [Job kits: questions step (bathroom full, default answers)](../screenshots/audit/audit-kits-questions-mobile-light.png) | 346 | 17 | 2 | 7 | 7 | 4 | 6 | 10 | no | 14 |
| [Job kits: measure step](../screenshots/audit/audit-kits-measure-mobile-light.png) | 153 | 17 | 3 | 3 | 10 | 4 | 5 | 10 | no | 14 |
| [Job kits: review step (defaults filled in)](../screenshots/audit/audit-kits-review-mobile-light.png) | 704 | 93 | 6 | 65 | 5 | 4 | 7 | 13 | no | 14 |
| [Job kits: summary step](../screenshots/audit/audit-kits-summary-mobile-light.png) | 1,589 | 15 | 25 | 2 | 16 | 4 | 7 | 12 | no | 14 |
| [Price books (default customer A)](../screenshots/audit/audit-price-books-mobile-light.png) | 1,019 | 17 | 8 | 10 | 4 | 6 | 5 | 8 | no | 14 |
| [Price books: Request price file dialog (customer B)](../screenshots/audit/audit-price-books-request-mobile-light.png) | 1,284 | 24 | 9 | 10 | 7 | 7 | 8 | 8 | no | 14 |
| [Price books: Upload price file dialog](../screenshots/audit/audit-price-books-upload-mobile-light.png) | 1,219 | 23 | 12 | 14 | 12 | 7 | 8 | 8 | no | 14 |
| [Price books: Request quotes dialog, Send RFQ for these gaps (customer B)](../screenshots/audit/audit-price-books-rfq-mobile-light.png) | 1,149 | 31 | 9 | 10 | 10 | 7 | 8 | 8 | no | 14 |
| [Quote: first quote (default customer A, bathroom full)](../screenshots/audit/audit-quote-mobile-light.png) | 4,255 | 87 | 21 | 38 | 0 | 7 | 11 | 10 | no | 14 |
| [Quote: scrolled to Options](../screenshots/audit/audit-quote-options-mobile-light.png) | 4,255 | 87 | 21 | 38 | 11 | 7 | 11 | 10 | no | 14 |
| [Inbox (#/)](../screenshots/audit/audit-inbox-mobile-light.png) | 207 | 12 | 8 | 8 | 12 | 5 | 5 | 8 | no | 9 |
| [Requests (#/requests)](../screenshots/audit/audit-requests-mobile-light.png) | 152 | 12 | 1 | 9 | 24 | 5 | 4 | 7 | no | 9 |
| [Suppliers (#/vendors)](../screenshots/audit/audit-suppliers-mobile-light.png) | 149 | 13 | 1 | 7 | 7 | 6 | 5 | 7 | no | 9 |
| [Setup (#/setup)](../screenshots/audit/audit-setup-mobile-light.png) | 181 | 2 | 4 | 8 | 2 | 6 | 6 | 7 | no | 9 |
| [Audit trail (#/audit)](../screenshots/audit/audit-audit-mobile-light.png) | 94 | 3 | 1 | 1 | 18 | 3 | 3 | 6 | no | 9 |

## Highest load (top 5 screens per measure)

Ranked over every captured row above, desktop and mobile, light and dark. Ties keep table order.

- **Visible words:** Quote: first quote (default customer A, bathroom full), desktop light: 4,255; Quote: scrolled to Options, desktop light: 4,255; Quote: first quote (default customer A, bathroom full), mobile light: 4,255; Quote: scrolled to Options, mobile light: 4,255; Quote: first quote (default customer A, bathroom full) (dark), desktop dark: 4,255
- **Controls:** Job kits: review step (defaults filled in), desktop light: 93; Job kits: review step (defaults filled in), mobile light: 93; Job kits: review step (defaults filled in) (dark), desktop dark: 93; Quote: first quote (default customer A, bathroom full), desktop light: 87; Quote: scrolled to Options, desktop light: 87
- **Headings:** Job kits: summary step, desktop light: 25; Job kits: summary step, mobile light: 25; Quote: first quote (default customer A, bathroom full), desktop light: 21; Quote: scrolled to Options, desktop light: 21; Quote: first quote (default customer A, bathroom full), mobile light: 21
- **Pills:** Job kits: review step (defaults filled in), desktop light: 65; Job kits: review step (defaults filled in), mobile light: 65; Job kits: review step (defaults filled in) (dark), desktop dark: 65; Quote: first quote (default customer A, bathroom full), desktop light: 38; Quote: scrolled to Options, desktop light: 38
- **Numbers in first viewport:** Quote: scrolled to Options, desktop light: 38; Audit trail (#/audit), desktop light: 34; Price books (default customer A), desktop light: 30; Price books (default customer A) (dark), desktop dark: 30; Price books: Upload price file dialog, desktop light: 25
- **Distinct text colours:** Price books: Request price file dialog (customer B), desktop light: 7; Price books: Upload price file dialog, desktop light: 7; Price books: Request quotes dialog, Send RFQ for these gaps (customer B), desktop light: 7; Quote: first quote (default customer A, bathroom full), desktop light: 7; Quote: scrolled to Options, desktop light: 7
- **Distinct background colours:** Quote: first quote (default customer A, bathroom full), desktop light: 11; Quote: scrolled to Options, desktop light: 11; Quote: first quote (default customer A, bathroom full), mobile light: 11; Quote: scrolled to Options, mobile light: 11; Quote: first quote (default customer A, bathroom full) (dark), desktop dark: 11
- **Max nesting depth:** Job kits: review step (defaults filled in), desktop light: 13; Job kits: review step (defaults filled in), mobile light: 13; Job kits: review step (defaults filled in) (dark), desktop dark: 13; Job kits: summary step, desktop light: 12; Job kits: summary step, mobile light: 12
- **Page scrolls sideways:** none of the 36 captured screens.

## Failures and notes

None. All 36 planned screenshots were taken and every dialog opened.

Dialog boxes on their own (the table counts include the dimmed page behind them):

- Price books: Request price file dialog (customer B), desktop light: the dialog box alone has 239 words and 2 controls.
- Price books: Upload price file dialog, desktop light: the dialog box alone has 174 words and 1 control.
- Price books: Request quotes dialog, Send RFQ for these gaps (customer B), desktop light: the dialog box alone has 104 words and 9 controls.
- Price books: Request price file dialog (customer B), mobile light: the dialog box alone has 239 words and 2 controls.
- Price books: Upload price file dialog, mobile light: the dialog box alone has 174 words and 1 control.
- Price books: Request quotes dialog, Send RFQ for these gaps (customer B), mobile light: the dialog box alone has 104 words and 9 controls.

Outside main, the sidebar or tab bar and top bar are shared by every screen, and the journey track appears on the journey screens. On the Inbox they hold 10 controls on desktop and 9 controls on mobile, with roughly 50 and 30 words (approximate).

Browser console during the run: no errors or warnings.

## Method note

- **What was run.** The mock demo built from `apps/web` (`npx vite build -c demo/vite.config.mjs`, then `node demo/inline.mjs`) and served from `apps/web/demo-dist` on `http://127.0.0.1:3300`. Nothing called a live API, a model or a mail server. The app's storage is cleared before each screen so the defaults show.
- **Viewports and theme.** Desktop 1280 × 800 and mobile 390 × 844 CSS pixels at pixel ratio 1, in the light theme. Dark theme on desktop only, for the rows marked (dark): Job kits review, Price books, Quote and Inbox.
- **Mobile width.** The demo page has no viewport tag. Without one, phone emulation lays the page out at 980 px and shrinks it, so the capture adds `width=device-width, initial-scale=1` on load. The Next.js build of the product sets the same default. Desktop is not affected.
- **Journeys.** Job kits: the bathroom full scope with default answers, stepping scope, questions, measure, review, then summary. Price books: customer A first, then customer B for the three dialogs, because customer A has no gaps and no missing merchants. Quote: customer A, bathroom full, the first quote, then scrolled to Options. The other five screens open from their routes.
- **Scroll position.** Screens open at the top. Job kits steps after the first put the step heading at the top, as the app does when a step changes. Quote Options puts its heading just under the sticky header.
- **Waiting.** Each count is taken after the loading placeholders are gone, after a short pause for the page to settle, and after any scroll has finished (about 0.75 s in all).
- **Dialogs.** A dialog renders inside the main element, so the main counts include the dimmed page behind it. The dialog box on its own is listed under Failures and notes.
- **Visible and countable.** Visible means rendered and at least 2 px square. Content inside a closed section (for example a collapsed review section) is not visible until it is opened, so it is not counted. Disabled controls are left out. Counts cover the whole main element, including content below the fold; only the numbers column is limited to the first screen.
- **Visible words.** Words in the rendered text of the main element.
- **Controls.** Visible buttons, links with an address, inputs, selects, text areas and summaries. A visually hidden radio or checkbox counts as the label or card around it, so one choice card is one control.
- **Headings.** Visible h1 to h4 elements.
- **Pills.** Visible elements with `rounded-full` in their class that contain text. Empty round decoration is left out.
- **Numbers in first viewport.** Tokens containing a digit, in text that is on screen within the first window height at the moment of capture. Text clipped by a scrolling box is not counted. For an unscrolled screen this is the first screen height of the page.
- **Distinct text colours and background colours.** Distinct computed colour values among visible elements. Text colour counts only elements that hold their own text. Fully transparent backgrounds are left out.
- **Max nesting depth.** The deepest visible element, counted in element levels below the main element.
- **Page scrolls sideways.** The page is wider than the window.
- **Controls outside main.** Controls in the sidebar or tab bar, the top bar and the journey track. These are shared by every screen, so they are shown in their own column.
- **Highest load.** Ranks every captured row by each count. Ties keep table order.
- **Planned and captured.** 36 screenshots were planned (16 light for each viewport, plus 4 dark). 36 were written.
- **Limits.** These are structure counts from one build on one day. They say how much is on the screen, not how hard it is to understand or whether it is right. A long, familiar list can be easier to use than a short, new form. No threshold or pass mark was applied.
