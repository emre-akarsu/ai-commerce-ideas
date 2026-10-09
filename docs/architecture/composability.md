# Composable workflows and industry packs: design (proposal v0.1)

Status: **proposal** (ADR-012). Goal: build many versions of the same workflow for different industries with minimal configuration, and let many ideas plug into one platform as modules that can be wired together in a workflow, without ever weakening hard rules R1 to R12. Builds on `configurability.md` (ADR-011) and the pack manifest in `packages/aiplat/manifest.py`. No code in this repo implements it yet.

## 1. Where the repo is today

| Axis | Today | Gap |
|---|---|---|
| Jurisdiction | Deployment profiles resolve platform defaults, `base`, profile and tenant into one immutable `ResolvedProfile` with a digest and per-key provenance (`profiles/*.yaml`, `packages/aiplat/profile.py`) | none for this axis |
| Vertical | `employees/<pack>/employee.yaml` lists tools, workflow names, shared modules and limits | Workflow names carry only an approval mode and a schedule. The step graph is code: `employees/purchasing/graph.py` builds a LangGraph `StateGraph` by hand (intake, spec, candidates, draft_rfq, human_review) |
| Modules | Shared components under `packages/components/*`; packs list them by name | No typed capability contract, no manifest per module, no check that a composed workflow keeps the hard rules |
| Refurb | `employees/refurb` is plain Python with its own model, policy and parser | Cannot be wired with purchasing modules |

So a new industry today means new Python: a graph, tools and prompts. The aim is to make most new industries data, and make modules interchangeable behind contracts.

## 2. Layered model

| Layer | Contains | Changes how often | Owned by |
|---|---|---|---|
| 0 Kernel | Hard rules R1 to R12: send-service, approvals, hash-chained events through the workflow module, tenant isolation, profile resolver, `LLMProvider` | Rarely; each change has an ADR | Core team |
| 1 Capabilities | Typed contracts ("ports"): what a step does, not how | Rarely; versioned | Core team |
| 2 Modules | Implementations (adapters) of one or more capabilities, each with a `module.yaml` | Often | Idea or module authors |
| 3 Workflow templates | Industry-neutral declarative graph of steps that name capabilities | Occasionally | Platform |
| 4 Industry packs | Data: taxonomy, work-package templates, attribute tables, gate catalogue, question bank, prompts, synthetic seed, eval fixtures | Per vertical | Domain authors |
| 5 Profile and tenant | Jurisdiction and customer settings (existing) | Per market, per customer | Config |

A **deployment** is one choice from each of layers 3 to 5, validated together:

```yaml
# deployments/bathroom-london.yaml (illustrative)
workflow: quote_to_award@1
pack: bathroom-refurb@1
profile: uk
tenant: <tenant-id>
bindings: {}                  # empty = use the pack's defaults
features: { photo_takeoff: false }
```

```yaml
# deployments/mro-bearings-uk.yaml (illustrative)
workflow: quote_to_award@1    # same template
pack: mro-bearings@1          # different data
profile: uk
tenant: <tenant-id>
bindings: { Planner: intent-planner@1 }   # not used here; the pack's own intake is the default
```

Resolution extends the existing order: platform defaults, `base`, **pack defaults**, profile (and parents), tenant overrides, into one immutable `ResolvedComposition` with a digest and per-key provenance. Every audit event records `composition = <id>@<digest12>` next to the profile digest.

## 3. Capabilities and modules

A capability is a versioned contract with typed inputs and outputs, written as a Python `Protocol` plus Pydantic models in `packages/aiplat` (not in the frozen `core/domain.py` or `ports.py`). Money fields are `Decimal` with currency and UoM (R9). Examples drawn from the engine map and the three ideas:

| Capability | Provided by (idea) | Used by |
|---|---|---|
| `IntentParser` | Intent-driven planner | Any buying workflow that starts from an outcome |
| `PartIdentifier`, `EquivalenceResolver` | Idea 1 and Idea 4 (equivalence graph, also exposed as API or MCP) | Purchasing, electronics, MEP packs |
| `ScopePlanner`, `QuantityTakeoff`, `TierOptimiser` | Intent-driven planner | Refurb and other project-based packs |
| `GateEvaluator` | Intent-driven planner (gate catalogue in the pack) | Any workflow with regulated steps |
| `MandateCheck`, `RfqPacketBuilder`, `CounterpartyVerifier`, `FraudScreen` | Idea 5 (mandate and RFQ layer) | Every workflow that contacts a supplier |
| `QuoteExtractor`, `QuoteComparator` | Existing parser and comparison code | Every workflow that reads replies |

A module declares itself in `module.yaml`:

```yaml
id: scope-planner-llm
version: 1.2.0
provides: [ScopePlanner@1]
requires: { capabilities: [IntentParser@1], kernel: [events, tenant_repo] }
effects: pure                    # pure | read | write | external_read | send
llm: { role: planner, tools: [] }
reads_pack: [work_packages, questions, prompts]    # extension points, each with a schema the module owns
config_schema: schemas/scope_planner.json
evals: [evals/scope_planner/]    # frozen set; promotion gate applies
data_sources: []                 # licence records required for any source
```

## 4. Workflow templates

A template is a small, declarative graph. Steps name **capabilities**, never modules, so the implementation can be swapped by a binding (Strategy by data). The DSL has no expressions: branch conditions name predicates a module exports, so the language cannot grow into a second programming language.

```yaml
workflow: quote_to_award@1
steps:
  - { id: intake,   uses: IntentParser@1 }
  - { id: scope,    uses: ScopePlanner@1 }
  - { id: gates,    uses: GateEvaluator@1, on: { blocked: stop } }
  - { id: packets,  uses: RfqPacketBuilder@1 }
  - { id: approve,  uses: Approval@1, human: required }
  - { id: send,     uses: SendService@1 }          # kernel port
  - { id: parse,    uses: QuoteExtractor@1 }
  - { id: compare,  uses: QuoteComparator@1 }
  - { id: award,    uses: Approval@1, human: required }
```

A runner would compile the template to the existing LangGraph runtime; resumable loops need a checkpointer, and a Postgres one has not been built (the purchasing graph takes an injected checkpointer, and `build_graph` is imported only by a test). The purchasing graph stays as the reference until a template reproduces its behaviour in a test.

## 5. Industry packs

A pack is a directory of data validated by schemas that the bound modules own. It adds no Python unless it needs a new module.

```
packs/bathroom-refurb/
  pack.yaml            # id, version, default bindings, required capabilities, jurisdictions supported
  taxonomy.yaml        # categories, units, size bands
  work_packages.yaml   # scope template and decision variables
  gates.yaml           # gate catalogue and triggers (sources cited, reviewer named)
  questions.yaml       # question bank with cost-impact tags
  attributes.yaml      # critical attributes and comparators
  prompts/             # extractor and planner prompts, pinned
  seed/                # synthetic, labelled as synthetic
  evals/               # frozen gold set and hostile fixtures
```

Levels of effort for a new industry (the goal is that most are level 1; measure it by the lines of new Python per pack):

| Level | What changes | Example |
|---|---|---|
| 0 | Tenant config only | Different caps or copy |
| 1 | New pack, data only | A new trade with the same quote_to_award template |
| 2 | Pack plus one module behind an existing capability | A designation parser for a new part family |
| 3 | New capability contract | A step no existing contract covers; needs an ADR |

`docs/templates/new-deployment-checklist.md` gains a pack section: schemas validate, gold set frozen, licences recorded, gate rules reviewed by a named domain reviewer, conformance tests green.

## 6. Design patterns used

| Pattern | Where | Why |
|---|---|---|
| Ports and adapters (hexagonal) | Capabilities and modules | Swap implementations; test with fakes |
| Strategy by data | Workflow step bound to a module through a binding | Industry variants without branches in code |
| Plugin registry with manifests | `module.yaml` discovered at start-up | Ideas plug in without touching the runner |
| Template method | Workflow template fixes the order; modules fill steps | Same safety order in every industry |
| Policy as data and the specification pattern | Gate catalogue, mandate rules, caps | Reviewable by non-engineers; fail closed |
| Composition root | One resolver builds the `ResolvedComposition` | One place to validate and record |
| Anti-corruption layer | Every external API or supplier format behind a capability | Vendor terms change; the core does not |
| Event sourcing (existing) | Hash-chained events | Reproducible, auditable runs |
| Capability-based security | Tenant-scoped tokens; send-service as sole mail reader | The model never holds credentials or tenant IDs |

## 7. Safety: the hard rules stay non-configurable

Packs, bindings and tenants can change data and choose modules. They cannot add a key that overrides R1 to R12 (no such keys exist). Two layers enforce this:

1. **Composition linter** (runs in CI and at start-up; a failure blocks the deployment):
   - C1 every path to a step with `effects: send` passes an `Approval` step and goes through the `SendService` port;
   - C2 a step with tools never consumes vendor-origin data;
   - C3 data typed `untrusted` passes the grounding check before it reaches a critical field;
   - C4 money in a port is `Decimal` with currency and UoM;
   - C5 modules reach data only through tenant-scoped repositories;
   - C6 every required capability is bound and versions are compatible;
   - C7 pack data validates against module schemas and contains no reserved key;
   - C8 every data source has a licence record and a permitted use;
   - C9 each module has an eval suite and the pack has a frozen gold set before a production stage.
2. **Runtime enforcement** repeats C1 to C3 (send-service verifies the Approval; taint types stop untrusted data), so a linter bug cannot send mail.

## 8. Plugging the three ideas and later ones

| Idea | Contributes | Plugs in as |
|---|---|---|
| Idea 1 MRO purchasing agent | Intake, part identification, RFQ drafting, quote parsing, comparison | Modules behind `PartIdentifier`, `QuoteExtractor`, `QuoteComparator`; `mro-bearings` and similar packs |
| Idea 4 equivalence graph | Evidence-backed equivalence with tiers | `EquivalenceResolver`, also served as an API or MCP tool to other deployments; licensing flags decide what it may store |
| Idea 5 mandate and RFQ layer | Mandate, policy engine, schemas, counterparty verification, fraud screen | `MandateCheck`, `RfqPacketBuilder`, `CounterpartyVerifier`, `FraudScreen`; required by every outbound workflow |
| Intent-driven planner | Intake from outcomes, scope, BOM, tiers, gates | `IntentParser`, `ScopePlanner`, `QuantityTakeoff`, `TierOptimiser`, `GateEvaluator`; first used by `bathroom-refurb` |
| A future idea | Any new step | A module and, if needed, a pack; a new capability only at level 3 |

## 9. Testing and promotion

- **Contract tests:** one shared suite per capability; every module must pass it, so a swap is safe.
- **Pack conformance:** like `tests/profiles`, run over every pack (schemas, reserved keys, licence records, no real data).
- **Linter tests:** a hostile composition (a send step with no approval, a tool step fed vendor text) must be refused.
- **Golden flows:** one end-to-end run per template and pack with the scripted `FakeLLM`; no network.
- **Promotion:** a module or pack moves from draft to production only on its frozen eval set and the existing Wilson upper-bound convention.

## 10. Migration path (smallest steps first)

1. Define capability Protocols and `module.yaml` loading in `packages/aiplat`; register the existing refurb parser and comparison as the first modules.
2. Write the composition resolver and linter with tests (C1 to C9), starting with C1 to C4.
3. Add the workflow template runner that compiles to LangGraph; reproduce the purchasing graph as a template and compare behaviour.
4. Extract `bathroom-refurb` as the first data-only pack; add a second pack (for example `mro-bearings`) to prove level 1.
5. Move jurisdiction values that the refurb pack hard-codes (for example `VAT_RATE`) into the profile.

Rule of three: extract an abstraction only after two concrete uses exist. Purchasing and refurb are the two; the third pack validates the contracts before they are frozen.

## 11. Risks

- **Over-abstraction.** Contracts frozen too early. Mitigation: version them and revise after the second and third pack.
- **Configuration sprawl.** Many files that nobody understands. Mitigation: schemas with defaults, `validate` command, a resolved-composition view with provenance.
- **A DSL that becomes a language.** Mitigation: no expressions, named predicates only.
- **Plug-in supply chain.** Third-party modules could read tenant data. Mitigation: internal modules only until a signing and review process exists.
- **Packs carrying unreviewed regulated content** (gates, legal wording). Mitigation: each gate rule names a source and a reviewer; the linter blocks production use without one.
- **Hard to say how much this saves.** The saving per new industry is unmeasured; track new lines of Python per pack from the second pack on.
