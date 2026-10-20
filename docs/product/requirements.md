# EVision product requirements

**Status:** Active working specification  
**Owner:** EVision product and engineering team  
**Audience:** Product, frontend, backend, data, QA, and academic reviewers  
**Last reviewed:** 2026-10-20

## 1. Product summary

EVision helps an EV driver choose a charging station using more than its current map status. It combines short-term occupancy forecasts, uncertainty, queue estimation, distance, price, and a labelled carbon scenario to explain the available trade-offs.

The product is a decision-support prototype. It is not a live booking, payment, navigation, or charger-control platform.

## 2. Outcomes

1. Give drivers three understandable choices: fastest, balanced, and lowest-carbon.
2. Make expected queue and cost visible instead of hiding them inside one score.
3. Show confidence and assumptions beside any forecast or carbon estimate.
4. Evaluate decisions through historical replay and regret, not forecast accuracy alone.
5. Keep the implementation reproducible and ready for a future backend.

## 3. Users and use cases

| User | Need | Product surface |
|---|---|---|
| EV driver | Select a station likely to work on arrival | Dashboard and station detail |
| Reviewer/researcher | Understand whether the method improves decisions | Evaluation and methodology |
| Network operator | Find over- and under-utilised capacity | Insights |
| Fleet/planning team | Compare charging windows and station patterns | Compare and Insights |

## 4. Scope

### Included

- Station discovery and recommendation UI.
- Occupancy horizon controls for now, +1 hour, +2 hours, and +3 hours.
- Forecast-aware queue estimate and transparent recommendation cards.
- Station detail, strategy comparison, evaluation, insights, and methodology routes.
- Responsive desktop, tablet, and mobile layouts.
- Local mock data with typed service interfaces matching `/api/v1`.

### Excluded

- Charger hardware or firmware.
- Payments, reservations, user accounts, and private driver data.
- Guaranteed live availability or live queue observation.
- Utility-scale grid optimisation.
- Claims of a new forecasting architecture.

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Show nearby stations with availability and location context. | P0 |
| FR-02 | Let the user switch the occupancy horizon. | P0 |
| FR-03 | Present fastest, balanced, and lowest-carbon recommendations. | P0 |
| FR-04 | Explain wait, price, distance, carbon source, and confidence. | P0 |
| FR-05 | Support station detail with history, forecast, and nearby stations. | P1 |
| FR-06 | Compare decision strategies using the same scenario. | P1 |
| FR-07 | Show evaluation metrics and an honest limitations notice. | P1 |
| FR-08 | Support keyboard focus and responsive layouts. | P0 |

## 6. Trust and data policy

- Synthetic data must be labelled wherever it affects a decision.
- Carbon values must be labelled as scenario assumptions unless an observed provider is active.
- Forecast intervals must not be presented as certainty.
- The evaluation reveal is evaluation-only and must not be confused with a live result.
- Historical replay must freeze the decision before future truth is revealed.

## 7. Success criteria

The frontend release is ready when every route renders, navigation works, primary interactions are keyboard accessible, `npm run build` passes, and the UI remains usable at approximately 375px, 768px, and 1280px widths.

## 8. Change history

| Date | Change | Owner |
|---|---|---|
| 2026-10-20 | Consolidated product scope and frontend behavior into the canonical requirements document. | Engineering |
