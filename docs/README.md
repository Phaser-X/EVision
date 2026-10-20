# EVision documentation

This directory is the project documentation system of record. Documents are grouped by the decision they support rather than by the date they were created.

## Document map

| Area | Document | Audience | Purpose |
|---|---|---|---|
| Product | [requirements.md](product/requirements.md) | Product, engineering, reviewers | Scope, users, objectives, requirements, and non-goals |
| Architecture | [system-architecture.md](architecture/system-architecture.md) | Engineering | Runtime boundaries, data flow, frontend/API boundary, and deployment direction |
| Delivery | [implementation-plan.md](delivery/implementation-plan.md) | Engineering, project lead | Milestones, dependencies, exit criteria, and risks |
| Quality | [quality-guide.md](quality/quality-guide.md) | Engineering, QA | Verification strategy and release acceptance |
| Reference | [original documents](reference/) | Maintainers | Historical source material retained for traceability |

## Documentation rules

1. Product behavior belongs in `product/`.
2. Technical boundaries belong in `architecture/`.
3. Sequencing and ownership belong in `delivery/`.
4. Test evidence and release gates belong in `quality/`.
5. Historical drafts remain in `reference/` and are not current requirements.
