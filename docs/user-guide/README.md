# User guide

This guide is for the people who use the app: **requesters** who need a part, **buyers** who ask suppliers for quotes and compare the replies, and **admins** who look after suppliers and the account.

It describes what the screens do today. It does not describe plans.

> **Read this first.**
> - The screenshots come from the **demo build**. It shows made-up data (fictional suppliers, a fictional company, parts marked "synthetic") and a ribbon at the top that says *Demo data. Nothing is sent.* Your own deployment will look the same but show your data.
> - In every build so far, an approved message goes to a **recording transport**: the system records exactly what would have been sent, but no real email provider is connected yet. Production start-up is deliberately blocked until the remaining gaps are closed (see [known gaps](../architecture/known-gaps.md), item H2).
> - The web app has **no sign-in screen yet**. The deployment supplies the sign-in token, and the role in it decides what you can do.
> - Whether this saves a buyer time is not yet proven. Treat it as a pilot tool, and check its output.

## What the app does

You describe what you need. The app works out what part that is, asks you only the questions it cannot answer itself, and lists any assumptions it made. It then prepares one quote request per supplier you choose. **A person reads and approves each message before anything is sent.** Replies are read, checked and compared like for like. When you pick a quote, a purchase order draft is prepared for you to send yourself.

There are two ways in:

| Start here | When to use it | Pages |
|---|---|---|
| **Requests** (Home, then *New request*) | A part, or a few parts: "4 x 6205-2RS bearings for the packing line". | [Requests](02-requests.md) |
| **Quote a job** | A whole job that needs a materials list, such as a bathroom refit: you answer a few questions, check quantities, see what it costs from the suppliers' price files, then ask suppliers. | [Quote a job](03-quote-a-job.md) |

## Contents

1. [Getting started](01-getting-started.md): roles, the screen layout, keyboard shortcuts.
2. [Requests](02-requests.md): the six steps from a request to a purchase order draft, and what each status means.
3. [Quote a job](03-quote-a-job.md): Job, Prices, Quote, Compare and Ask suppliers.
4. [Suppliers, Setup and Activity](04-suppliers-setup-activity.md): verifying suppliers, going live, the kill switch and the audit trail.
5. [What the app will not do](05-safety-rules.md): the rules that cannot be switched off, in plain language.
6. [Glossary](06-glossary.md): the words the screens use.
7. [Troubleshooting](07-troubleshooting.md): what each refusal message means and what to do.

For how the system works inside, see the [technical documentation](../technical/README.md).
