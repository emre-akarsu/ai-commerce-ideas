# Getting started

## The screen

![Home: the "Needs you" list](img/01-home.png)

- **Left rail:** *Home*, *Quote a job*, *Requests*, *Suppliers*, *Setup*, *Activity*. The number beside *Home* is how many requests are waiting on you. On a phone the rail becomes a tab bar.
- **Top bar:** *Search or jump* (press `Ctrl K`, or `Cmd K` on a Mac) opens a command palette. In the demo build there is also a **Demo role** switcher so you can see the app as each role.
- **Ribbon:** in the demo build a banner reads *Demo data. Nothing is sent.* The *(i)* beside it explains what demo data is.
- **Home** lists the open requests that have a next step, each with the one thing to do next. It does not list a request that has ended, a request whose purchase order draft already exists (*PO drafted*), or a request in *Needs engineering review* with no critical assumption waiting to be confirmed. Find those under **Requests**. Home loads at most 40 open requests. The list is ordered by what is waiting: questions to answer, assumptions to confirm, messages to approve, a quote to select, suppliers to choose, a purchase order to create, and last the requests that are waiting on someone else. Within each group a request marked **Machine down** comes first, then the earliest *needed by* date (a request with no date comes last). The four tiles (*Questions*, *Choose*, *Approve*, *Waiting*) count where requests are; selecting a tile filters the list, and selecting it again clears the filter.

The app uses light or dark mode to match your device, and works on a phone.

## Roles

Your role comes from the sign-in token the app sends (the `role` in the token's `app_metadata`). The web app has no sign-in screen of its own yet, and nothing in it asks for a token. A development build sends a development token that is set in the app's environment. A production build sends no token, so the server answers every request with *authentication required* until a way to supply one is added (a known gap, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)). The demo build needs no token and has a role switcher instead. The server, not the screen, decides what you may do. There are three roles, and each includes everything below it.

A requester sees only the requests they raised. Buyers and admins see every request in the company.

| Role | What you can do |
|---|---|
| **Requester** | Start a request, answer its questions, confirm or reject the assumptions the app made, see the comparison of replies, work through a materials list (*Quote a job*), and read quotes, ways to buy, price books and the list of price files. |
| **Buyer** (includes requester) | Choose suppliers and prepare messages, **approve and send each message**, paste in a reply received another way, select a quote, create the purchase order draft, edit a supplier's commercial details, import suppliers from a CSV file, suppress a supplier, upload price files, build a quote, record match decisions, draft quote requests for missing prices, and save job templates. Also open an approval link and decide on it, if you are one of the named approvers. |
| **Admin** (includes buyer) | **Add** a supplier, **verify** a supplier, allow contact again after a suppression, see *Setup* and *Activity*, record that the account is live, and use the **kill switch**. The server also lets an admin read a summary of review events, but the web app has no screen for it. |

If a control is switched off for your role, the screen says why next to it, for example *Needs the buyer role or higher; you are signed in as requester.* In the rail, *Setup* and *Activity* show **Admin only** when you are not an admin.

![A requester on the supplier step in the demo build: the NEXT bar says which role is needed](img/28-requester-role.png)

The demo build shows a requester the supplier list. A connected server does not: it refuses a requester that list (*insufficient role*), and the step shows that message instead.

> **Note.** The **Add supplier** button is enabled for buyers in the current web app, but the server only lets an admin add a supplier. If a buyer presses it, the request is refused.

### Who may approve a quote

A quote needs an approval before an order when any of these is true: the part offered is not an identical part (a substitute), the total is above the approval threshold in your deployment profile, the day's committed total is over the daily limit, or the quote carries a flag such as *VAT basis not stated*, *Currency unclear*, *Freight not stated*, *Not stated as new* or *Entered by hand*. The approval goes to a named approver. **The approver must be someone other than the person who asked** when the total is above the approval threshold, when the day's total is over the daily limit, or when the quote carries one of those flags. If there is no such approver, selecting the quote is refused after the request has already moved to *Quote selected*, and the request is then stuck (see [Waiting for the approver](02-requests.md#waiting-for-the-approver)).

## Keyboard shortcuts

Press `?` anywhere to see the list.

![The shortcuts help](img/25-shortcuts.png)

| Keys | Does |
|---|---|
| `Ctrl/Cmd K` or `/` | Search or jump |
| `n` | New request |
| `g` then `i`, `t`, `p`, `q`, `r`, `s`, `u` or `a` | Go to Home, Job, Prices, Quote, Requests, Suppliers, Setup, Activity |
| `j` and `k` | Move down and up a list |
| `Enter` | Open the focused item |
| `.` | On a request, move focus to the button in the NEXT bar. It does nothing on other screens, and there is no button when you are already on the step the bar names. It never presses the button for you. |

![The command palette](img/24-command-palette.png)

## Dark mode and phones

The app follows your device's light or dark setting and works at phone width. On a phone the left rail becomes a bar along the bottom, and tables scroll sideways inside their own box rather than moving the whole page.

![The comparison in dark mode](img/29-dark-compare.png)

| Home on a phone | Approving a message on a phone |
|---|---|
| ![Home at phone width](img/30-mobile-home.png) | ![The approve step at phone width](img/31-mobile-approve.png) |

## Your first request, in one minute

1. On **Home**, press **New request** (or `n`).
2. Type what you need, for example `6205-2RS bearings for the packing line`, and fill in **Quantity** and, if you know it, **Needed by**. No message can be prepared for a request without a quantity, and a phrase such as `4 x 6205-2RS` is not read as a quantity (see [Start a request](02-requests.md#1-start-a-request)).
3. Press **Start request** (or `Ctrl+Enter`). You land on the request, which asks at most two questions.
4. Follow the **NEXT** bar at the bottom of the request. It says what to do next. A request with nothing left to do in the app, such as one in *Needs engineering review* with nothing left to confirm, has no NEXT bar (see [What each status means](02-requests.md#what-each-status-means)).

The full walk-through is in [Requests](02-requests.md).
