"""Which documents go into the portal, in navigation order. Ids use letters, digits and hyphens only."""
REGISTRY = [
    # (id, section, nav label, repo path)
    ("hub", "Start", "Documentation hub", "docs/README.md"),

    ("ug-readme", "User guide", "Overview", "docs/user-guide/README.md"),
    ("ug-01", "User guide", "1. Getting started", "docs/user-guide/01-getting-started.md"),
    ("ug-02", "User guide", "2. Requests", "docs/user-guide/02-requests.md"),
    ("ug-03", "User guide", "3. Quote a job", "docs/user-guide/03-quote-a-job.md"),
    ("ug-04", "User guide", "4. Suppliers, Setup, Activity", "docs/user-guide/04-suppliers-setup-activity.md"),
    ("ug-05", "User guide", "5. What the app will not do", "docs/user-guide/05-safety-rules.md"),
    ("ug-06", "User guide", "6. Glossary", "docs/user-guide/06-glossary.md"),
    ("ug-07", "User guide", "7. Troubleshooting", "docs/user-guide/07-troubleshooting.md"),

    ("tg-readme", "Technical guide", "Overview and defects", "docs/technical/README.md"),
    ("tg-01", "Technical guide", "1. System overview", "docs/technical/01-system-overview.md"),
    ("tg-02", "Technical guide", "2. Request lifecycle", "docs/technical/02-request-lifecycle.md"),
    ("tg-03", "Technical guide", "3. Data model", "docs/technical/03-data-model.md"),
    ("tg-04", "Technical guide", "4. API reference", "docs/technical/04-api-reference.md"),
    ("tg-05", "Technical guide", "5. The quote engine", "docs/technical/05-quote-engine.md"),
    ("tg-06", "Technical guide", "6. Security and trust", "docs/technical/06-security-and-trust.md"),
    ("tg-07", "Technical guide", "7. Configuration", "docs/technical/07-configuration.md"),
    ("tg-08", "Technical guide", "8. Deployment and operations", "docs/technical/08-deployment-and-operations.md"),
    ("tg-09", "Technical guide", "9. Testing and evaluation", "docs/technical/09-testing-and-evals.md"),
    ("tg-10", "Technical guide", "10. Extending the system", "docs/technical/10-extending.md"),
    ("tg-11", "Technical guide", "11. Diagram index", "docs/technical/11-diagram-index.md"),

    ("ar-readme", "Architecture", "Architecture design", "docs/architecture/README.md"),
    ("ar-modules", "Architecture", "Current modules", "docs/architecture/current-modules.md"),
    ("ar-activity", "Architecture", "Activity diagrams (32)", "docs/architecture/activity-diagrams.md"),
    ("ar-gaps", "Architecture", "Known gaps", "docs/architecture/known-gaps.md"),

    ("master", "Product", "MASTER summary", "docs/MASTER.md"),
]
