# EVision quality and release guide

## 1. Automated checks

Run from `frontend/`:

```powershell
npm run build
```

The build must complete with strict TypeScript checks and no Vite errors.

## 2. Functional smoke checks

1. Open `/` and verify the landing page loads its hero media or poster fallback.
2. Use the Features/Open dashboard navigation.
3. On `/dashboard`, switch the occupancy horizon.
4. Select a station marker and a recommendation card.
5. Open and close the explanation drawer.
6. Open the evaluation-only reveal and verify its label.
7. Visit station detail, compare, evaluation, insights, and about routes.

## 3. Responsive checks

| Viewport | Expected behavior |
|---|---|
| 375px | Single-column layout, touch-friendly controls, bottom navigation |
| 768px | Compact layout with readable cards |
| 1280px | Sidebar, map, recommendations, and supporting panels visible together |

## 4. Accessibility checks

- Keyboard focus is visible on links, buttons, inputs, tabs, and cards.
- Interactive controls have readable labels or accessible text.
- Motion is reduced when the user enables `prefers-reduced-motion`.
- Information is not conveyed by color alone.
- Synthetic and assumed values are written as text, not only shown visually.

## 5. Release checklist

- [ ] Build passes.
- [ ] Routes render and navigation works.
- [ ] No broken media references.
- [ ] No console errors in the primary journey.
- [ ] Mobile, tablet, and desktop layouts reviewed.
- [ ] Mock/API boundary remains isolated.
- [ ] Documentation and repository tree are current.
