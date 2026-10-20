# EVision — Product & Technical Specification (`specs.md`)

> **Audience: an AI coding agent that will build this whole project.**
> Read order: `specs.md` (WHAT) → `architecture.md` (HOW it is structured) → `plan.md` (IN WHAT ORDER, with checklists).
> This file is the **source of truth for behaviour**. If another file disagrees, this file wins; record the conflict in `docs/assumptions.md`.

---

## 0. Quick orientation

| Item | Value |
|---|---|
| Project | **EVision** — Intelligent Decision Support for EV Charging |
| Context | Mini project, 5th-semester BE CSE, Siddaganga Institute of Technology, Tumakuru (AY 2026-27 ODD). Guide: Dr Kiran Kumar T M |
| One-line pitch | Forecast short-term charging-station occupancy **with uncertainty**, turn it into an explainable wait time using an **M/M/c queue**, combine with distance, price and a carbon signal, and show the driver **FASTEST / BALANCED / GREENEST** options — then **prove with a leakage-free historical replay** whether this beats simpler strategies. |
| Deliverable | A **full, deployable, software-only system**: data pipeline + models + decision engine + replay evaluator + REST API + web dashboard + Docker deployment + docs. No hardware, no private data. |
| Primary dataset | **UrbanEV** (Shenzhen, hourly, 1 Sep 2022 – 28 Feb 2023) |
| Extension dataset | **CHARGED** (6 cities, hourly, 1 Apr – 30 Sep 2023) — cross-city groundwork |
| Language/stack | Python 3.11 + FastAPI + SQLite · React + TypeScript + Leaflet · Docker |

### 0.1 Honest framing (must be preserved everywhere in code, UI and docs)

The project **does not claim** that forecasting, station recommendation, preference ranking, multi-objective optimisation or carbon-aware charging are new. Its contribution is **decision-level**:

1. A reproducible experiment testing whether *uncertain future-demand information* improves charging **decisions** (measured by **decision regret**), not just forecast error.
2. A transparent decision layer: ML estimates only one number (arrival/occupancy → λ); a **deterministic M/M/c formula** turns it into wait time; trade-offs are shown, not collapsed into one opaque score.
3. A strict **historical-replay protocol** that prevents look-ahead leakage.
4. Groundwork for testing whether the benefit holds in other cities (CHARGED).

Either outcome of the experiment ("uncertainty-aware helps" / "does not help") is a valid result. **Never tune the system to make the proposed method win.** Report honestly, including high-variance-period results and failures.

### 0.2 Glossary

| Term | Meaning |
|---|---|
| Station | The dataset's spatial unit with chargers. In UrbanEV's public files this may be aggregated per traffic zone — the adapter must treat whatever the unit is as a "station" (see §2, A1). |
| Capacity `c` | Number of charging piles at the station. |
| Occupancy `o` | Number of piles in use (hourly value from data). Occupancy rate = `o / c`. |
| Decision time `t` | End of hour-bucket `t`. Only data in buckets `≤ t` is visible (plus published price schedule, see §5.1). |
| Horizon `h` | Forecast target is hour-bucket `t + h`, `h ∈ {1,2,3}`. |
| Delay `d` | Driver chooses to leave `d` hours later (time-shift option), `d ∈ {0,1,2}`. |
| τ (tau) | Mean service (session) time in hours; `μ = 1/τ`. |
| λ (lambda) | Arrival rate (sessions/hour) implied by forecast occupancy. |
| M/M/c | Queue with Poisson arrivals, exponential service, `c` servers. Used via the Erlang-C formula. |
| Regret | `C(chosen) − C(best option in hindsight)`, ≥ 0. |
| Generalised cost `C` | One interpretable money-equivalent number combining time, price, carbon. Used for **evaluation and BALANCED**, never hides the individual terms. |
| Pareto-efficient | Option not beaten on all of (time, money, carbon) by another option. |

---

## 1. Goals and non-goals

### 1.1 Goals (map to the 8 objectives in the project report)

| # | Objective (from report §5) | Where specified |
|---|---|---|
| O1 | Reproducible software-only pipeline on open data | §4.1, §10, §12 |
| O2 | Short-term occupancy forecasting: historical-average & persistence → XGBoost → optional LSTM | §4.2 |
| O3 | Forecast uncertainty (quantile regression / ensemble / conformal) | §4.3 |
| O4 | Transparent multi-objective decision engine → FASTEST / BALANCED / GREENEST | §4.4, §4.5, §5 |
| O5 | Historical-replay evaluation, no look-ahead leakage | §4.6, §9 |
| O6 | Decision-level test (regret) vs nearest, cheapest, current-availability baselines, esp. high-variance periods | §9 |
| O7 | Interactive web dashboard/map | §7 |
| O8 | Groundwork for cross-city generalisation (CHARGED) and richer methods | §4.9, §4.10 |

### 1.2 Non-goals (do **not** build; list them on the Methodology page)

- Not charger hardware or firmware. Not a live commercial navigation / charging-network app.
- Not a generic "EV charging prediction using LSTM" project; forecasting is one component.
- Not a utility-grade power-grid optimiser.
- No new forecasting architecture. GNN/Transformer/domain-adaptation are **stretch / major-project** items (documented in the roadmap, not implemented).
- No user accounts, payments, real bookings, or private driver data.

---

## 2. Source reconciliation and working assumptions

The inputs were a PDF report and a PPTX synopsis. Where they differ, decisions are fixed here. Copy this table to `docs/assumptions.md` and extend it as you discover facts.

| ID | Assumption / decision | Reason |
|---|---|---|
| A1 | **Verify the real UrbanEV file layout in Phase 1.** The report says "1,362 stations"; the public release may be organised by traffic **zone** (matrices of time × zone for occupancy, volume, duration, prices, plus adjacency, distance and station-info files). The adapter maps whatever the spatial unit is to the canonical `station_id`. Document the real layout in `docs/data.md`. | Report text vs. real files may differ. Do not hard-code assumptions. |
| A2 | UrbanEV is treated as **single-city (Shenzhen)** for the mini project. Cross-city only via CHARGED (O8). | PDF says so; the PPTX's "multi-city" wording is imprecise. |
| A3 | The **PPTX adds the M/M/c deterministic layer**; the PDF does not mention it. **Include it** — it is the mechanism that converts a forecast into wait time. | It strengthens explainability and matches the synopsis. |
| A4 | Realised ("true") wait time is **not observed** in public data. It is computed by applying the **same M/M/c formula to the true occupancy** of the arrival hour. This is a modelling assumption and must be stated on the Evaluation page and in the report. | No session-queue logs available. |
| A5 | Grid carbon intensity is a **labelled scenario assumption** (not observed) unless a real provider is configured. Every API response and UI element showing carbon must carry `carbon_source: "scenario" | "observed"`. | Report §6.4; avoid presenting assumed numbers as measurements. |
| A6 | Electricity + service **price schedules for future hours are treated as known at decision time** (published tariffs). **Weather and occupancy for future hours are NOT known.** | Prevents leakage while keeping tariffs realistic. |
| A7 | Currency defaults to CNY (`¥`) because UrbanEV is Shenzhen; configurable (`CURRENCY`). | Dataset origin. |
| A8 | The "team" listed on the cover page repeats one name; do not hard-code team names anywhere in code. Put team metadata only in `README.md`/About page, filled via config. | Source data inconsistent. |
| A9 | All numeric defaults in §6 (value of time, carbon price, grid intensity profile, energy per session) are **assumptions**, exposed in config and in the UI, with sensitivity analysis in the evaluation. | Honesty / reproducibility. |

---

## 3. Users and use-cases

| Persona | Need | Feature |
|---|---|---|
| Everyday EV driver | Pick a station that will still be free on arrival | Recommend page, three labelled options, explanations |
| Examiner / researcher | See whether the approach beats baselines, reproduce numbers | Evaluation page, `make reproduce`, saved run artifacts |
| Network operator (applications slide) | Find chronically over/under-used stations | Insights page |
| Fleet / ride-share scheduler, urban planner (applications slide) | Coordinate charging windows; see where stations are needed | Documented as applications + Insights (utilisation heat map); multi-vehicle scheduling is stretch |

---

## 4. Functional requirements

Priority: **P0** = must ship, **P1** = should ship (project is still "complete" for the report with all P0+P1), **P2** = optional/stretch, behind a flag.

### 4.1 Data (FR-D)

| ID | Pri | Requirement |
|---|---|---|
| FR-D1 | P0 | `scripts/download_data.py` fetches UrbanEV from its public sources (Dryad dataset DOI `10.5061/dryad.np5hqc04z`; GitHub `IntelligentSystemsLab/UrbanEV` for code/preprocessing examples). If the network/download fails (Dryad may require a browser), print exact manual instructions and the expected target folder `data/raw/urbanev/`. |
| FR-D2 | P0 | `UrbanEVAdapter` converts raw files → **canonical schema** (§5.1): `stations.parquet`, `observations.parquet`, `adjacency.parquet`, `distances.parquet`, `weather.parquet`. Validates timestamps (hourly, monotonic, no duplicates), missing values, ID consistency, coordinate sanity. Writes a **data-quality report** (`artifacts/data_quality.json` + markdown). |
| FR-D3 | P0 | Missing-value policy: short gaps (≤3 h) forward-filled for occupancy, longer gaps left as NaN and masked out of training/evaluation; stations with > 20 % missing dropped and listed in the quality report. |
| FR-D4 | P0 | `SyntheticAdapter` generates a realistic synthetic city (stations, daily/weekly demand pattern, weather effect, noise, saturation, price schedule) with the same canonical schema, seeded. Used for tests, CI, and as automatic fallback so the whole system **runs end-to-end without the real data**. UI must show a visible "SYNTHETIC DATA" badge when active. |
| FR-D5 | P0 | **Chronological split** train 70 % / validation 15 % / test 15 % by time (never random). Split boundaries stored in `artifacts/split.json`. |
| FR-D6 | P1 | Station-level static features: capacity, lat/lon, neighbours (from adjacency), POI info if present in the dataset, mean price. |
| FR-D7 | P1 | `CHARGEDAdapter` (see §4.9). |

### 4.2 Forecasting (FR-F)

| ID | Pri | Requirement |
|---|---|---|
| FR-F1 | P0 | **Target**: occupancy **rate** `o/c` ∈ [0,1] at bucket `t+h`, horizons `h ∈ {1,2,3}` (direct strategy: one model per horizon). Convert to piles by `× c` where needed. |
| FR-F2 | P0 | **Baselines**: (a) *Persistence*: `ŷ(t+h) = y(t)`. (b) *Historical average*: mean occupancy rate for the same station × hour-of-week computed from the **training period only** (and expanding window during replay using only data ≤ t). |
| FR-F3 | P0 | **XGBoost** global model (all stations in one model, `station static features` as inputs) per horizon. Features (all computed from data ≤ t unless stated): hour-of-day (and sin/cos), day-of-week, weekend flag, holiday flag (optional), lags `{1,2,3,6,12,24,168}` of occupancy rate, rolling mean `{3,6,24}`, short-term trend (`y(t) − y(t−3)`), rolling std 24 h, **weather at t** (temperature, precipitation, etc. as available; *no future weather*), **price at t+h** (known tariff, A6), capacity, lat/lon, mean neighbour occupancy at `t` (adjacency), `price_service` etc. |
| FR-F4 | P0 | Metrics on validation and test: MAE, RMSE, MAPE/sMAPE (with epsilon guard for near-zero), R² (supplementary). Per horizon, overall and by station-capacity bucket and by hour-of-day. |
| FR-F5 | P0 | **Feature ablation**: train/evaluate with feature groups {time, weather, price, spatial} removed one at a time and "time-only". Output a table to `artifacts/reports/ablation_forecast.csv` and show it in the UI. |
| FR-F6 | P2 | **LSTM** (PyTorch, CPU-friendly, small) as optional sequence model for comparison. Installed only with the `lstm` extra; code path guarded so base install works without torch. |
| FR-F7 | P0 | Model registry: each trained model saved with `config hash`, data hash, split boundaries, metrics, training date, library versions, in `artifacts/models/<name>/<horizon>/`. API reports the active model versions. |

### 4.3 Uncertainty (FR-U)

| ID | Pri | Requirement |
|---|---|---|
| FR-U1 | P0 | **Quantile XGBoost** with quantiles `{0.1, 0.5, 0.9}` per horizon (`objective="reg:quantileerror"`, XGBoost ≥ 2.0). Enforce non-crossing quantiles (sort) and clip to [0,1]. |
| FR-U2 | P0 | **Split conformalised quantile regression (CQR)** calibration on the **validation** set to give an 80 % interval with a finite-sample correction. Calibrated interval is the one served by API/UI; the raw one is kept for comparison. |
| FR-U3 | P1 | **Ensemble alternative**: K=5 XGBoost models (different seeds/subsamples); spread → interval. Selected by `uncertainty.method: quantile | conformal | ensemble`. |
| FR-U4 | P0 | Uncertainty metrics: **empirical coverage** (target ≈ 80 %), **mean interval width**, pinball loss, coverage by hour-of-day and by occupancy level; reliability plot data. |
| FR-U5 | P0 | **Confidence score** per forecast = `1 − clip(q90 − q10, 0, 1)`, exposed with a label: `high ≥ 0.75`, `medium 0.5–0.75`, `low < 0.5`. |

### 4.4 Queueing layer (FR-Q) — *deterministic, explainable*

| ID | Pri | Requirement |
|---|---|---|
| FR-Q1 | P0 | Implement **M/M/c Erlang-C expected waiting time in queue** (formulas in §5.3) with numerically stable computation (Erlang-B recursion). |
| FR-Q2 | P0 | ML contributes **only** the occupancy → arrival-rate estimate `λ̂ = o·μ`. The same inputs always give the same output (pure function, no randomness). |
| FR-Q3 | P0 | Service time `τ` per station estimated from training data as `τ = session_energy_kwh / avg_power_kw`, where `avg_power_kw` = station median of `volume_kwh / duration_h` when both exist (clipped to `[0.25, 3.0]` h); otherwise default `τ = 1.0 h`. |
| FR-Q4 | P0 | Saturation/censoring guard: occupancy is capped at capacity, so offered load `a = min(o, rho_max·c)` (`rho_max = 0.98`), and wait is capped at `w_max = 60 min`. Flag `saturated: true` when the cap is hit. |
| FR-Q5 | P0 | Wait **interval**: compute `W(q10)`, `W(q50)`, `W(q90)` by pushing each forecast quantile through the same formula. |
| FR-Q6 | P0 | Unit tests against known values (M/M/1 closed form when `c=1`; `W=0` when `o=0`; monotonic in `o`; monotonic decreasing in `c` for fixed `ρ`). |

### 4.5 Decision / recommendation engine (FR-R)

| ID | Pri | Requirement |
|---|---|---|
| FR-R1 | P0 | **Candidate generation**: for an origin, take the `top_k` (20) nearest stations within `radius_km` (5) × delays `{0,1,2}` h. Drop candidates whose required horizon `ceil((delay + travel)/1h) > 3`. |
| FR-R2 | P0 | Per candidate compute: `travel_km`, `travel_min`, `delay_min`, forecast `(q10,q50,q90)` at the required horizon, `wait_min` (point + interval), `price_total`, `carbon_kg`, `total_time_min`, `generalised_cost`, confidence. Formulas in §5. |
| FR-R3 | P0 | **Uncertainty-aware wait**: use risk-adjusted occupancy `o_eff = q50 + κ·(q90 − q50)` with `κ = risk_kappa` (default 0.5, user-adjustable 0–1). `κ=0` reproduces the point-forecast strategy. |
| FR-R4 | P0 | **Pareto filter** on minimisation of `(total_time_min, price_total, carbon_kg)`. Deterministic tie-breaks (value, then `station_id`, then delay). |
| FR-R5 | P0 | **Labels** among Pareto-efficient candidates: **FASTEST** = min `total_time_min`; **GREENEST** = min `carbon_kg` (ties → lower time); **BALANCED** = min generalised cost `C`. The same candidate may win several labels — the response still returns all three keys and a `distinct_count`. |
| FR-R6 | P0 | **Explanation** for each option: term-by-term cost contributions, forecast band, M/M/c intermediates (`c, τ, λ, ρ, P_wait`), saturation flag, comparison against the nearest station (Δtime, Δcost, Δcarbon), and a templated natural-language sentence. No LLM calls. |
| FR-R7 | P0 | Returns the **full Pareto front** (≤ 30 points) for the trade-off chart, plus up to 50 dominated candidates for context. |
| FR-R8 | P0 | User preferences accepted per request: `energy_kwh`, `radius_km`, `max_delay_h`, `risk_kappa`, `value_of_time_per_h`, `carbon_price_per_kg`, `carbon_scenario`. |
| FR-R9 | P1 | `strategy` switch (`uncertainty_aware | point_forecast | current_availability | historical_average | nearest | cheapest`) so the UI Compare page can show what each baseline would choose. |
| FR-R10 | P1 | Carbon provider interface with `ScenarioCarbonProvider` (default) and `ElectricityMapsCarbonProvider` (P2, needs `ELECTRICITYMAPS_TOKEN`, disabled by default, never required). |
| FR-R11 | P2 | Optional road-network distance/time via OSMnx + NetworkX (`routing.provider: haversine | osmnx`), with graph cached on disk. Default `haversine × detour_factor`. |

### 4.6 Replay evaluation (FR-E)

| ID | Pri | Requirement |
|---|---|---|
| FR-E1 | P0 | **Historical-replay simulator** per §9: at each decision time `t` in the **test period**, strategies see only a `HistoryView` limited to `≤ t`; the true future is revealed only after the choice is frozen. A **leakage guard** raises if a strategy touches data beyond `t`. |
| FR-E2 | P0 | Strategies: `nearest`, `cheapest`, `current_availability`, `historical_average`, `point_forecast`, `uncertainty_aware` (proposed) + `oracle` (hindsight best, regret = 0, reference only). |
| FR-E3 | P0 | Metrics: mean/median/P90 **regret**, average realised wait, travel distance, charging cost, carbon estimate, **station-load imbalance**, **recommendation failure rate** (overall and in the **high-uncertainty** subset). Definitions in §9.3. |
| FR-E4 | P0 | **Statistical rigour**: paired bootstrap 95 % CI of regret differences vs each baseline (fixed seed), win/tie/loss rates. |
| FR-E5 | P0 | **Sensitivity**: results across `risk_kappa ∈ {0, .25, .5, .75, 1}`, value-of-time, carbon scenarios; and **station-only vs station+time** settings (§9.2). |
| FR-E6 | P0 | Outputs persisted: `artifacts/runs/<run_id>/{config.json, metrics.json, decisions.parquet, figures/*.png, report.md}` and mirrored into SQLite for the API. |
| FR-E7 | P0 | **Reproducibility**: one command (`make reproduce`) re-creates every number from raw data with fixed seeds; run twice → identical metrics. |

### 4.7 API (FR-A) — see §6 for the contract

| ID | Pri | Requirement |
|---|---|---|
| FR-A1 | P0 | FastAPI app with OpenAPI docs at `/docs`, versioned prefix `/api/v1`. All inputs validated (Pydantic v2). Consistent error shape. |
| FR-A2 | P0 | Endpoints in §6 implemented and contract-tested. |
| FR-A3 | P0 | Responses include `data_source` (`urbanev | charged | synthetic`), `as_of`, `model_version`, `carbon_source`. |

### 4.8 Dashboard (FR-UI) — see §7

| ID | Pri | Requirement |
|---|---|---|
| FR-UI1 | P0 | Pages: Recommend (main), Station detail, Compare strategies, Evaluation, Insights, Methodology/About. |
| FR-UI2 | P0 | Interactive **Leaflet map** with stations coloured by forecast occupancy; click to open station detail; origin picker (click map / drag pin). |
| FR-UI3 | P0 | **Time Machine** control (simulated "now" inside the held-out test period) + "Reveal what actually happened" button (shows true occupancy/wait vs forecast band). |
| FR-UI4 | P0 | **Forecast band chart**: recent history + forecast with q10–q90 band + confidence badge. |
| FR-UI5 | P0 | **Recommendation cards** (FASTEST/BALANCED/GREENEST) with explanation drawer. |
| FR-UI6 | P0 | **Trade-off chart**: time vs money scatter, carbon as colour/size, Pareto front highlighted, click-to-select option. |
| FR-UI7 | P0 | **Preferences panel** (§4.5 FR-R8 parameters) with sensible defaults and a reset button. |
| FR-UI8 | P0 | Frontend visual design derived from the team's **inspiration images** (§7.1). |
| FR-UI9 | P1 | Responsive (desktop + tablet + phone), dark/light, keyboard accessible, WCAG AA contrast. |

### 4.9 Cross-city groundwork (FR-X) — major-project extension, **implement what the data allows**

| ID | Pri | Requirement |
|---|---|---|
| FR-X1 | P1 | `CHARGEDAdapter` for the Zenodo archive (record `15763454`) → same canonical schema, one dataset id per city (Amsterdam, Johannesburg, Los Angeles, Melbourne, São Paulo, Shenzhen). Inspect the real layout first; document in `docs/data.md`. |
| FR-X2 | P1 | `scripts/run_cross_city.py`: train on one city (default Shenzhen/UrbanEV or CHARGED-Shenzhen), evaluate **zero-shot** on each other city using the same replay protocol; report forecast metrics, coverage, and regret vs baselines per city. |
| FR-X3 | P1 | Evaluation page has a "Cross-city" tab (empty-state message if CHARGED not downloaded). |
| FR-X4 | P2 | Documented roadmap only (no code): GNN/Transformer, domain adaptation, conformal calibration under shift, grid-aware optimisation, live station APIs. |

### 4.10 Insights & applications (FR-I)

| ID | Pri | Requirement |
|---|---|---|
| FR-I1 | P1 | Operator Insights: per-station utilisation over a selectable window, ranking of **chronically over-used** (mean occupancy rate > 0.8 at peak, high saturation share) and **under-used** stations, hour × weekday heat map, "load balance" index (Gini of utilisation). |
| FR-I2 | P2 | Fleet scheduling demo: given N vehicles, assign charging windows to minimise total regret (greedy, documented as stretch). |

### 4.11 Operations (FR-OPS)

| ID | Pri | Requirement |
|---|---|---|
| FR-OPS1 | P0 | `docker compose up` brings up backend + frontend (nginx) with persisted `artifacts/` volume. |
| FR-OPS2 | P0 | `make bootstrap` = download (or synthetic fallback) → prepare → train → calibrate → evaluate → seed DB. Idempotent. |
| FR-OPS3 | P0 | Health endpoint, structured logs, `.env.example`, no secrets in repo. |
| FR-OPS4 | P1 | GitHub Actions CI: lint, type-check, unit tests (synthetic data), frontend build + tests, Docker build. |
| FR-OPS5 | P1 | Deploy guide for a single VM and for a PaaS (Render/Railway/Fly), including how to ship the `artifacts/` bundle. |

---

## 5. Domain model and formulas (authoritative)

### 5.1 Canonical data schema

`stations.parquet`: `station_id (str), name (str|null), lat, lon, capacity (int ≥1), dataset (str), city (str), mean_price (float|null), extra… `

`observations.parquet` (long, hourly): `ts (UTC datetime, hour bucket start), station_id, occupancy (float, piles busy), occupancy_rate (=occupancy/capacity, clipped [0,1]), volume_kwh (nullable), duration_h (nullable), e_price, s_price (nullable; currency/kWh)`

`weather.parquet`: `ts, temperature, precipitation, humidity, wind, … (whatever exists; one row per ts, or per ts × weather_station then mapped to station)`

`adjacency.parquet`: `station_id, neighbour_id`; `distances.parquet` (optional): `station_id, neighbour_id, km`.

Leakage rule summary (also enforced in code):
- Occupancy/volume/duration/weather: **only buckets ≤ t**.
- Price/tariff (e_price, s_price): future buckets allowed (A6).
- Historical-average baseline & any normalisation statistics: computed from data ≤ t (during replay) or the training period (for static reporting).

### 5.2 Geometry and time

```
travel_km   = haversine(origin, station) * detour_factor            # default 1.3
travel_min  = travel_km / speed_kmh * 60                            # default 30 km/h
delay_min   = 60 * d,  d ∈ {0,1,2}
required_h  = ceil((delay_min + travel_min) / 60)   # must be in {1,2,3}, else drop candidate
```

### 5.3 M/M/c waiting time (Erlang C)

```
Inputs:  c (piles), τ (hours, mean session), o (forecast occupied piles)
μ  = 1/τ
a  = min(o, rho_max * c)          # offered load in Erlangs; λ = a·μ  (so λ̂ = o·μ)
ρ  = a / c                        # < 1 guaranteed by rho_max
Erlang-B recursion:  B_0 = 1;  B_k = a·B_{k-1} / (k + a·B_{k-1})   for k = 1..c
Erlang-C:            P_wait = B_c / (1 − ρ·(1 − B_c))
Expected wait:       W_q [hours] = P_wait / (μ·(c − a)) = P_wait · τ / (c − a)
wait_min = min(60·W_q, w_max)     # w_max = 60
```
Sanity checks for tests (M/M/1 when `c=1`, `W_q = ρ·τ/(1−ρ)`):
- `c=1, τ=1 h, a=0.2` → `W_q = 0.2/0.8 = 0.25 h = 15 min`.
- `c=1, τ=1 h, a=0.5` → `W_q = 1 h = 60 min` (exactly at the cap).
- `a=0` → `wait_min = 0`.

### 5.4 Forecast → wait for a candidate

```
(q10, q50, q90) = calibrated forecast occupancy RATE at horizon required_h for the station
o_k   = q_k * c                               # piles
o_eff = (q50 + κ·(q90 − q50)) * c             # risk-adjusted (uncertainty-aware strategy)
wait_min      = MMc(c, τ, o_eff)
wait_interval = [MMc(c,τ,o_10), MMc(c,τ,o_90)]
```
Strategy mapping: `point_forecast` uses `q50` from the **mean (squared-error) XGBoost**; `current_availability` uses `y(t)·c`; `historical_average` uses hour-of-week mean; `uncertainty_aware` uses `o_eff`.

### 5.5 Price, energy, carbon

```
price_total  = energy_kwh * (e_price + s_price)[station, hour of arrival+wait ≈ hour of arrival]   # known tariff
travel_kwh   = travel_km * consumption_kwh_per_km                                              # default 0.18
carbon_kg    = (energy_kwh + travel_kwh) * intensity_g_per_kwh(hour_of_charging) / 1000
charge_hour  = hour of (t + delay + travel + wait)
charge_time_min (info only) = 60 * energy_kwh / avg_power_kw[station]
```
Carbon scenarios (config, **placeholders to be documented as assumptions**, not measurements):
- `flat`: one constant intensity (e.g. 550 gCO₂/kWh).
- `tou_profile` (default): 24-value hourly profile (lower midday, higher evening); ship as `configs/carbon_profiles.yaml`.
- `low` / `high`: ±25 % of `flat` for sensitivity.

### 5.6 Objectives and generalised cost

```
total_time_min = delay_min + travel_min + wait_min        # "time until charging starts"
C = VOT * (total_time_min / 60) + price_total + carbon_price * carbon_kg
    VOT default 30 currency/hour, carbon_price default 0.5 currency/kg   (assumptions A9)
```
Pareto objectives (all minimised): `(total_time_min, price_total, carbon_kg)`.

### 5.7 Confidence

`confidence_score = 1 − clip(q90 − q10, 0, 1)` → label high / medium / low (thresholds in FR-U5).

---

## 6. API contract (`/api/v1`)

All times ISO-8601 UTC. Errors: `{"error": {"code": "string", "message": "string", "details": {...}}}` with HTTP 4xx/5xx.

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness + data/model readiness |
| `GET /meta` | Dataset id, city, `data_source`, time ranges (`train`, `val`, `test`), horizons, model versions, config defaults, currency, carbon scenarios, bounding box |
| `GET /stations?as_of=` | All stations with static info, **current** occupancy rate, **h=1 forecast** (q10/q50/q90), confidence. Must respond < 800 ms for ~1.4k stations |
| `GET /stations/{id}` | Static info + utilisation stats |
| `GET /stations/{id}/forecast?as_of=&hours_back=48` | History (observed ≤ as_of), forecast for `h=1..3` with raw + calibrated bands, confidence |
| `GET /stations/{id}/reveal?as_of=` | **After-the-fact** truth for `as_of+1..3h` (for the Time Machine "reveal"); also realised wait proxy |
| `POST /recommend` | Main decision endpoint (body below) |
| `POST /recommend/compare` | Same body; returns what **each strategy** would choose + realised outcome (reveal) for each |
| `GET /evaluation/runs` | List experiment runs |
| `GET /evaluation/runs/{run_id}` | Summary metrics, config, strategies table, CIs |
| `GET /evaluation/runs/{run_id}/regret` | Regret distribution (histogram bins + quantiles) per strategy |
| `GET /evaluation/runs/{run_id}/uncertainty` | Coverage, width, reliability data, high-uncertainty-subset results |
| `GET /evaluation/runs/{run_id}/ablation` | Forecast + decision ablation tables |
| `GET /evaluation/runs/{run_id}/sensitivity` | κ / VOT / carbon-scenario sweeps |
| `GET /evaluation/cross-city` | Cross-city results or `{"available": false}` |
| `GET /insights/utilisation?from=&to=` | Station ranking + hour×weekday heat map + load-balance index |
| `GET /queueing/explain?c=&tau=&occupancy=` | Step-by-step M/M/c values (for the "How is wait computed?" drawer) |

`POST /recommend` request:
```json
{
  "origin": {"lat": 22.5431, "lon": 114.0579},
  "as_of": "2023-02-10T17:00:00Z",
  "energy_kwh": 20,
  "radius_km": 5,
  "max_delay_h": 2,
  "risk_kappa": 0.5,
  "value_of_time_per_h": 30,
  "carbon_price_per_kg": 0.5,
  "carbon_scenario": "tou_profile",
  "strategy": "uncertainty_aware"
}
```
Response (shape; fields must exist, values illustrative):
```json
{
  "as_of": "2023-02-10T17:00:00Z",
  "data_source": "urbanev",
  "model_version": "xgb-2026-10-20-abc123",
  "carbon_source": "scenario",
  "options": {
    "FASTEST":  {"candidate_id": "S123@0", "station_id": "S123", "delay_min": 0, "travel_km": 1.8, "travel_min": 3.6,
                 "forecast": {"horizon_h": 1, "q10": 0.40, "q50": 0.55, "q90": 0.78, "confidence": 0.62, "confidence_label": "medium"},
                 "wait_min": 6.2, "wait_interval_min": [1.1, 14.0], "total_time_min": 9.8,
                 "price_total": 24.4, "carbon_kg": 3.9, "generalised_cost": 55.9,
                 "queue": {"c": 8, "tau_h": 0.9, "lambda_per_h": 5.5, "rho": 0.69, "p_wait": 0.31, "saturated": false},
                 "cost_terms": {"time": 4.9, "price": 24.4, "carbon": 1.95},
                 "vs_nearest": {"d_time_min": -2.0, "d_price": -1.1, "d_carbon_kg": 0.0},
                 "explanation": "…templated sentence…"},
    "BALANCED": { "…": "same shape" },
    "GREENEST": { "…": "same shape" }
  },
  "distinct_count": 2,
  "pareto_front": [ { "candidate_id": "…", "total_time_min": 0, "price_total": 0, "carbon_kg": 0 } ],
  "dominated": [ { "…": "…" } ],
  "params_used": { "…": "echo of effective parameters" }
}
```
Validation: `as_of` must lie in a period with ≥ 168 h of history and (for reveal/replay) inside the dataset; `origin` inside bounding box + 10 km margin; `energy_kwh ∈ [1,150]`; `risk_kappa ∈ [0,1]`; `radius_km ∈ [0.5, 15]`; `max_delay_h ∈ {0,1,2}`. Return 422 with details otherwise; return 200 with empty options and `reason: "no_candidates"` if nothing qualifies.

---

## 7. UI specification

### 7.1 Design reference process (**mandatory first step of frontend work**)

The team will place inspiration images in `design/inspiration/` (png/jpg/webp).
1. **Open and study every image** (use image-viewing capability). Write observations to `docs/design-notes.md`: layout structure, palette, typography, spacing, card/chip styles, map styling, chart styling, iconography, motion.
2. Translate into **design tokens** in `frontend/src/styles/tokens.css` (CSS variables) and Tailwind theme mapping. Components must only use tokens, never hard-coded hex values.
3. Reproduce the *look and layout language*, not pixel-copy copyrighted assets. Use open-licensed icons (Lucide) and fonts (Google Fonts, self-hosted via `@fontsource`).
4. **If the folder is empty**, do not block: use the fallback theme (§7.2) and add a visible TODO in `docs/design-notes.md`; the tokens make re-skinning cheap.
5. Ask the maintainers nothing; decide, document, proceed.

### 7.2 Fallback theme
Map-centric app, dark default with light option, deep navy surfaces, one accent for "recommended", three semantic option colours: FASTEST = amber, BALANCED = blue, GREENEST = green; occupancy scale green → yellow → red; rounded cards, subtle shadows; Inter font.

### 7.3 Pages and behaviour

**A. Recommend (`/`)** — default page
- Left/overlay panel: Time Machine, Preferences (collapsible), results.
- Map: station markers coloured by **forecast occupancy at +1 h** (toggle: current / +1h / +2h / +3h), size by capacity; draggable origin pin; click map to set origin; radius circle.
- Three **Option cards** (FASTEST/BALANCED/GREENEST) each showing: station, ETA, wait with interval, price, carbon (with "assumed" badge), confidence badge, "Why?" button. Selecting a card highlights the route line and marker.
- **Explanation drawer**: cost term breakdown bar, forecast band mini-chart, M/M/c steps (c, τ, λ, ρ, P_wait, W), "vs nearest" deltas, assumptions list.
- **Trade-off chart**: time (x) vs price (y), carbon as colour, Pareto front connected, selected option ringed.
- **Reveal button**: after a recommendation, show what actually happened at the arrival hour (true occupancy, realised wait proxy, realised regret vs hindsight-best) and label it "evaluation only — not available at decision time".
- Empty/loading/error states for every panel; skeleton loaders.

**B. Station detail (`/station/:id`)** — static info, 48 h history + forecast band for h=1..3, calibration badge, hour×weekday utilisation heat map, nearby stations.

**C. Compare (`/compare`)** — pick origin + time; table/cards of what each strategy chooses (nearest, cheapest, current-availability, historical-average, point-forecast, uncertainty-aware, oracle) with realised outcomes after reveal; highlights regret.

**D. Evaluation (`/evaluation`)** — tabs: *Overview* (strategy table, regret bars with CI, win/tie/loss), *Uncertainty* (coverage, width, reliability plot, high-variance subset), *Ablation*, *Sensitivity*, *Forecast metrics*, *Cross-city*, *Reproduce* (run id, config hash, commands). A prominent "what this does and does not show" box.

**E. Insights (`/insights`)** — over/under-used station rankings, heat map, load-balance index, applications blurb (personal navigation, fleet scheduling, operator insights, urban planning).

**F. Methodology (`/about`)** — pipeline diagram, M/M/c explanation, leakage protocol, assumptions (A1–A9), limitations, non-goals, literature-positioning table, team/guide (from config), SDG mapping (7, 11, 13, secondary 12) with "how demonstrated" metrics.

### 7.4 Frontend quality bar
React 18 + TypeScript strict, Vite, Tailwind, `react-leaflet`, Recharts, TanStack Query, React Router. Typed API client generated from OpenAPI. Unit tests for utils/components (Vitest + Testing Library), one Playwright smoke test (load page → set origin → get 3 options). Lighthouse performance ≥ 80 on desktop build. No console errors.

---

## 8. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | `POST /recommend` p95 < 1.5 s (precomputed forecast store, local); `/stations` < 800 ms; replay of the full test period completes < 30 min on a laptop CPU (vectorised NumPy). |
| Reproducibility | Global seed (42) for NumPy/XGBoost/Python; pinned dependency versions (`uv.lock` or `requirements.lock`); data and config hashes stored with each artifact; same command → same metrics. |
| Simplicity | **Prefer simple, readable, minimal code over clever abstractions.** Small functions, explicit names, no metaprogramming, no unnecessary design patterns. Comments explain *why*, not *what*. |
| Testing | pytest ≥ 80 % coverage on `decision/`, `evaluation/`, `forecasting/` core; contract tests for every endpoint; leakage tests (§9.4). |
| Quality gates | `ruff` + `mypy` (or `pyright`) clean; ESLint + `tsc --noEmit` clean. |
| Security | Input validation, CORS allow-list from env, rate limit on POST endpoints (simple in-memory), no secrets committed, dependency audit in CI, non-root containers. |
| Accessibility | Semantic HTML, focus order, ARIA on custom controls, colour not the only signal (patterns/labels for occupancy). |
| Observability | JSON logs with request id; `/health` details (data loaded, models loaded, DB reachable). |
| Portability | Runs on Linux/macOS/Windows (WSL) with Python 3.11 and Node 20; CPU only; ≤ 8 GB RAM for the full UrbanEV workflow (use `float32`, parquet). |
| Docs | `README.md` (quickstart), `docs/data.md`, `docs/assumptions.md`, `docs/design-notes.md`, `docs/deployment.md`, `docs/results.md` (auto-generated summary). |

---

## 9. Evaluation specification

### 9.1 Protocol (historical replay)
```
for t in decision_times(test period, 06:00–23:00 local, hourly):
    view = HistoryView(data, t)                         # only buckets <= t (+ tariff schedule)
    for origin in origins(t, n=20, seed fixed):         # sampled near random stations (+ jitter ≤ 1.5 km)
        cands = generate_candidates(origin, view)       # same set for every strategy
        for strategy in strategies:
            choice = strategy.choose(origin, cands, view)      # frozen here
        reveal truth at arrival hour; compute realised outcomes + C_realised for ALL candidates
        regret(strategy) = C_realised(choice) − min_c C_realised(c)
```
Realised wait (A4): `MMc(c, τ, o_true)` with `o_true = true occupancy at arrival hour`; realised price from the tariff; realised carbon from the same scenario.

### 9.2 Settings
- **Setting A (primary): station-only** — delay fixed at 0 for every strategy.
- **Setting B: station + time** — delays `{0,1,2}` allowed for the cost-based strategies (`current_availability`, `historical_average`, `point_forecast`, `uncertainty_aware`); `nearest`/`cheapest` stay at delay 0.
Report both.

### 9.3 Metric definitions
- **Regret**: per decision as above; report mean, median, P90, and share of zero-regret decisions.
- **Average realised wait / distance / cost / carbon** of chosen options.
- **Station-load imbalance**: for each decision hour, count recommendations per station, divide by capacity, take the **standard deviation** across stations; average over hours (lower = more balanced). Also Gini.
- **Recommendation failure**: chosen option has realised wait > 10 min **or** regret > 1 × VOT-hour-equivalent (`regret > VOT*0.25`, i.e. > 15 min worth of time). Both thresholds configurable.
- **High-uncertainty subset**: decisions where the chosen candidate's forecast interval width is in the top quartile (computed from `uncertainty_aware` forecasts, reused for all strategies for a fair subset). Report all metrics separately for this subset.
- **Forecast metrics**: MAE, RMSE, sMAPE, R² per horizon/model; **uncertainty**: coverage, width, pinball.

### 9.4 Mandatory leakage tests
1. Mutating all data after `t` must not change any strategy's choice at `t`.
2. `HistoryView` raises `LeakageError` when asked for bucket `> t`.
3. Feature builder test: feature row for time `t` is identical when computed on `data[:t]` vs the full dataset.
4. Train/val/test indices strictly increasing in time with no overlap (and a ≥ 168 h warm-up gap handled).
5. Conformal calibration uses validation only; test never touches calibration.

### 9.5 Required outputs
Strategy table with CIs; regret histogram; regret by hour-of-day; high-uncertainty vs normal comparison; coverage reliability plot; ablation table; κ sensitivity; both settings; honest `report.md` containing a "Findings" section **written from the numbers produced** (templated by code, then reviewed), including a plain statement of whether the proposed strategy won.

---

## 10. Datasets

| Dataset | Use | Notes |
|---|---|---|
| **UrbanEV** (Scientific Data 2025) | Primary | Hourly (5-min version exists); occupancy, duration, volume, e-price, service price, weather, adjacency, inter-zone distance, coordinates, POI. Report: 1,682 stations / 24,798 piles collected; 1,362 stations / 17,532 piles retained; 1 Sep 2022 – 28 Feb 2023. |
| **CHARGED** (Scientific Data 2025) | Cross-city extension | ≈12,000 chargers, 6 cities, hourly, 1 Apr – 30 Sep 2023. |
| OpenStreetMap | Optional routing | Via OSMnx. |
| Electricity Maps | Optional carbon source | Disabled by default; needs token; never required. |

Never commit raw data. `.gitignore` `data/` and `artifacts/` (except small fixtures in `tests/fixtures/`). Record dataset licences/citations in `docs/data.md`.

---

## 11. Configuration surface

All defaults in `configs/default.yaml`; env overrides via `EVISION_*`. Dataclass/Pydantic-validated at load.

```yaml
data:        {dataset: urbanev, fallback_to_synthetic: true, resample: "1h", max_missing_frac: 0.2, ffill_limit_h: 3}
split:       {train: 0.70, val: 0.15, test: 0.15}
forecast:    {horizons: [1,2,3], lags: [1,2,3,6,12,24,168], rolling: [3,6,24], min_history_h: 168, seed: 42}
uncertainty: {method: conformal, quantiles: [0.1,0.5,0.9], alpha: 0.2, ensemble_k: 5}
queue:       {rho_max: 0.98, w_max_min: 60, tau_clip_h: [0.25, 3.0], default_tau_h: 1.0}
decision:    {radius_km: 5, top_k: 20, delays_h: [0,1,2], speed_kmh: 30, detour_factor: 1.3,
              consumption_kwh_per_km: 0.18, default_energy_kwh: 20, value_of_time_per_h: 30,
              carbon_price_per_kg: 0.5, risk_kappa: 0.5, carbon_scenario: tou_profile}
routing:     {provider: haversine}
evaluation:  {origins_per_hour: 20, hours: [6, 23], seed: 42, high_uncertainty_quantile: 0.75,
              failure_wait_min: 10, bootstrap_n: 2000, setting: [A, B]}
app:         {currency: "¥", cors_origins: ["http://localhost:5173"], mode: replay}
```

---

## 12. Definition of Done (project-level)

The project is **done** when **all P0 and P1** items are implemented and:

1. `docker compose up` on a clean machine (after `make bootstrap` or with the shipped artifact bundle / synthetic fallback) serves the dashboard and API with no manual steps beyond env copying.
2. A user can: set an origin → pick a simulated time → receive FASTEST/BALANCED/GREENEST with explanations, forecast bands and the trade-off chart → reveal the truth.
3. `make reproduce` regenerates all evaluation artifacts; two runs yield identical metrics; the Evaluation page renders them.
4. Every leakage test in §9.4 passes; all unit/contract tests pass; CI green.
5. All pages in §7.3 exist, follow the design tokens derived from `design/inspiration/`, and have no console errors.
6. Docs exist and are accurate: README quickstart, data, assumptions, deployment, results, methodology.
7. The report's honest-framing statements (§0.1) and scope exclusions (§1.2) appear in the UI Methodology page and `docs/results.md`.

### 12.1 Traceability matrix

| Report objective | Requirements | Verified by |
|---|---|---|
| O1 pipeline | FR-D*, FR-OPS2 | `make bootstrap` + data tests |
| O2 forecasting | FR-F* | forecast metrics + ablation report |
| O3 uncertainty | FR-U* | coverage/width report, calibration test |
| O4 decision engine | FR-Q*, FR-R* | unit tests + API contract tests |
| O5 replay / no leakage | FR-E1, §9.4 | leakage test suite |
| O6 decision-level test | FR-E2–E5 | evaluation run + CIs |
| O7 dashboard | FR-UI* | Playwright smoke + manual checklist |
| O8 groundwork | FR-X* | cross-city script/tab (or documented empty state) |
