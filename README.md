# Buy-side RFQ platform

A person describes a part or a job. The system helps identify it, prices it from the price files the person uploads, asks the person's own suppliers for the prices that are missing, and compares the replies. **A person approves every message that is sent and every order.**

**Status:** a working build on synthetic data. Nothing sends real email (a recording transport stands in for mail), nothing delivers approval links, and `ENV=production` is refused on purpose until six listed gaps are closed. **Product-market fit is unproven**: no buyer or supplier has been interviewed, and nothing in this repository is a marketing claim or legal, tax or financial advice.

## Documentation

Start at the [documentation hub](docs/README.md).

| For | Read |
|---|---|
| People who use the app | [User guide](docs/user-guide/README.md), with screenshots |
| Engineers who build, run or review it | [Technical guide](docs/technical/README.md), including every diagram ([diagram index](docs/technical/11-diagram-index.md)) |
| Architecture decisions and known gaps | [Architecture](docs/architecture/README.md), [known gaps](docs/architecture/known-gaps.md) |
| The whole picture in one file | [MASTER](docs/MASTER.md) |

## Run it

```text
make setup                  # Python virtual environment with the dev extras
make demo-api               # the in-memory API on :8000 with synthetic data; prints a development token per role
cd apps/web && npm ci
APP_ENV=local NEXT_PUBLIC_API_MOCK=1 npm run dev -- -p 3100     # the web app with an in-browser mock, no backend needed
make check                  # lint, tests and evaluations (offline; no network, no real language model, no real email)
```

Other ways to run it (against a real PostgreSQL, on one VPS, on a free-tier VM) are in [deployment and operations](docs/technical/08-deployment-and-operations.md).

## Layout

`packages/aiplat` (manifest, call context, tools, deployment profiles) · `packages/aidb` (models, row-level security, migrations) · `packages/components/*` (sixteen shared components) · `apps/{api,worker,web}` · `employees/{purchasing,refurb}` · `profiles/` (market profiles and data) · `evals/` · `deploy/` · `scripts/` · `tests/`. The seven hard rules and the working rules for agents are in [`CLAUDE.md`](CLAUDE.md); the product spec is [`docs/product/04-product-spec.md`](docs/product/04-product-spec.md).
