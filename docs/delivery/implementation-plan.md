# EVision implementation plan

**Status:** Active delivery plan  
**Delivery model:** Small vertical slices with a build gate after each slice.

## 1. Workstreams

| Workstream | Output | Current state |
|---|---|---|
| Product definition | Requirements, assumptions, non-goals | Documented |
| Frontend foundation | Vite, React, TypeScript, routing, design tokens | Implemented |
| Landing experience | Responsive EVision product introduction | Implemented |
| Recommendation experience | Dashboard, map surface, cards, drawer, reveal | Implemented with mock data |
| Supporting pages | Station, compare, evaluation, insights, about | Implemented with mock data |
| API integration | Replace mock services with `/api/v1` | Next integration step |
| Quality and release | Build, accessibility, responsive, smoke checks | Ongoing |

## 2. Delivery sequence

### Milestone 1 — Repository and documentation baseline

- Keep root-level entry points minimal.
- Establish product, architecture, delivery, and quality documents.
- Preserve source documents in `docs/reference/`.

**Exit gate:** a new contributor can locate the product scope, architecture, plan, and quality expectations in under two minutes.

### Milestone 2 — Frontend foundation

- Maintain strict TypeScript compilation.
- Keep routes stable and navigation usable.
- Keep public media paths deterministic.

**Exit gate:** `npm run build` succeeds.

### Milestone 3 — Product experience

- Validate landing-to-dashboard flow.
- Validate map horizon controls and station selection.
- Validate recommendation explanation and evaluation-only reveal.

**Exit gate:** all primary user journeys work without a backend.

### Milestone 4 — Backend replacement

- Introduce a typed API client.
- Replace mock service calls behind the same interface.
- Add loading, empty, error, and retry states.

**Exit gate:** UI behavior is unchanged when switching from mock to API data.

### Milestone 5 — Release hardening

- Test responsive widths and keyboard navigation.
- Verify synthetic-data and carbon-assumption labels.
- Run build, lint, and smoke checks.

**Exit gate:** the release checklist in [quality-guide.md](../quality/quality-guide.md) is complete.

## 3. Risks and mitigations

| Risk | Mitigation |
|---|---|
| External map or media unavailable | Keep a local fallback surface and static poster. |
| Backend contract changes | Isolate API mapping in one service layer. |
| Motion becomes distracting | Keep durations bounded and honor reduced motion. |
| Forecast assumptions misunderstood | Label synthetic, scenario, and evaluation-only states directly in the UI. |
| Generated files pollute commits | Ignore build output, dependencies, caches, and run artifacts. |

## 4. Definition of done

- Requirements and non-goals are reflected in the UI.
- All listed routes render without console errors.
- Core interactions are keyboard reachable.
- Responsive layouts work at mobile, tablet, and desktop widths.
- `npm run build` passes from a clean dependency install.
- No secrets or generated build output are committed.
- Documentation matches the delivered repository.
