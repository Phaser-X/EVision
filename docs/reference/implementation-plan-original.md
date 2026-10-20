# EVision — Build Plan (`plan.md`)

> For the AI agent that will build the project. Read `specs.md` (WHAT) and `architecture.md` (HOW) first. This file says **IN WHAT ORDER**, with checkable tasks, acceptance criteria and verification commands.
> Work phase by phase. Tick boxes (`[x]`) in this file as you finish tasks and commit after every task. Never skip a phase's **Exit gate**.

---

## 0. Operating rules for the agent

1. **Read order**: `specs.md` → `architecture.md` → this file. Re-read the relevant spec section before each task (IDs like `FR-R3` refer to `specs.md`).
2. **Do not ask the user questions.** If something is ambiguous or data differs from the docs, make the most reasonable choice, then record it in `docs/assumptions.md` (what, why, date). Keep going.
3. **Simple, minimal code.** Small functions, explicit names, no clever abstractions. If a solution needs a paragraph to explain, simplify it.
4. **Honesty rules** (`specs.md §0.1`): never tune to make the proposed method win; report negative results; label carbon as an assumption; label synthetic data.
5. **No leakage**: every feature/strategy uses data ≤ t (tariffs excepted). Write the leakage tests early (Phase 2) and keep them green.
6. **Tests with code**: each module ships with its unit tests in the same task. Do not leave testing to the end.
7. **Reproducibility**: seed 42, pinned deps, config in `configs/default.yaml`, no magic numbers in code.
8. **Real data may be unavailable** (download blocked, licence click-through, huge). Use the `SyntheticAdapter` so every phase can be verified; the real-data path must still be implemented and tested on a small fixture slice.
9. **Commits**: one logical commit per task, message `phase-N/task-ID: summary`. Keep `main` runnable.
10. **Frontend design source**: images in `design/inspiration/`. View them **before** writing any UI code (Phase 8).
11. **Definition of done** is `specs.md §12`. Before finishing, run the final checklist (§15 of this file).
12. **If you hit a blocker** (library issue, API change): choose a workaround, write a 3-line ADR in `docs/decisions.md`, continue. Never leave the repo in a broken state.

### Progress tracker

| Phase | Title | Status |
|---|---|---|
| 0 | Bootstrap repo & tooling | [ ] |
| 1 | Data: adapters, quality, split | [ ] |
| 2 | Features + leakage tests | [ ] |
| 3 | Baselines + XGBoost forecasting | [ ] |
| 4 | Uncertainty (quantile + CQR) | [ ] |
| 5 | Decision engine | [ ] |
| 6 | Replay evaluator + reports | [ ] |
| 7 | Backend API + DB | [ ] |
| 8 | Frontend dashboard | [ ] |
| 9 | Optional extras (LSTM, ensemble, OSMnx, Electricity Maps) | [ ] |
| 10 | CHARGED + cross-city | [ ] |
| 11 | Insights | [ ] |
| 12 | Docker, CI, deployment | [ ] |
| 13 | Hardening, docs, final QA | [ ] |

Suggested order of dependency: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 12 → (9, 10, 11 in any order, but before 13) → 13.
Phases 5 (decision engine) can start in parallel with 3–4 using synthetic forecasts if you work in separate branches; otherwise stay sequential.

---

## Phase 0 — Bootstrap repo & tooling

**Goal:** empty-but-runnable skeleton with lint/test/CI wiring.

- [ ] **0.1** Create the repo layout from `architecture.md §2` (empty packages with `__init__.py`, `README.md`, `.gitignore` incl. `data/`, `artifacts/`, `node_modules/`, `.env`).
- [ ] **0.2** `pyproject.toml` (package `evision`, Python ≥ 3.11, extras `lstm`, `osm`, `dev`), lock file, `ruff`/`mypy`/`pytest` config. Dependencies: pandas, numpy, pyarrow, geopandas, scikit-learn, xgboost>=2.0, fastapi, uvicorn, pydantic>=2, sqlalchemy>=2, typer, pyyaml, matplotlib, plotly, httpx, tqdm.
- [ ] **0.3** `evision/config.py`: load `configs/default.yaml` + `EVISION_*` env overrides into a typed `Settings`. Write `configs/default.yaml` and `configs/carbon_profiles.yaml` exactly from `specs.md §11` and `§5.5` (carbon values = placeholder assumptions, commented as such).
- [ ] **0.4** `evision/cli.py` (Typer) with stub commands: `download`, `prepare`, `train`, `precompute`, `evaluate`, `cross-city`, `seed-db`, `reproduce`.
- [ ] **0.5** `Makefile` targets: `setup`, `lint`, `test`, `bootstrap`, `reproduce`, `serve`, `bundle`, `docker-up`, `frontend-dev`.
- [ ] **0.6** Seed utility `seed_everything(42)`; hashing util for configs/data files.
- [ ] **0.7** `AGENTS.md` (≤ 15 lines): pointer to the three docs + rules 2–6 above.
- [ ] **0.8** Copy `specs.md`, `architecture.md`, `plan.md` into `docs/spec/`.
- [ ] **0.9** Initial CI workflow running `ruff` + `pytest` (one trivial test).

**Exit gate:** `make setup && make lint && make test` pass on a clean clone.

---

## Phase 1 — Data: adapters, quality, split (FR-D*)

**Goal:** canonical parquet files for the active dataset + a leak-safe split.

- [ ] **1.1** `data/schema.py`: canonical column names, dtypes, validators (`validate_stations`, `validate_observations`).
- [ ] **1.2** `data/adapters/base.py`: `DatasetAdapter` with `load() -> CanonicalData` (stations, observations, weather, adjacency, distances).
- [ ] **1.3** `data/adapters/synthetic.py` (**build first**): N stations (default 60, configurable up to 1,400), 120 days hourly; demand = daily double-peak + weekend factor + station-specific scale + weather effect + AR(1) noise; capacity 2–20; saturation (occupancy ≤ capacity); TOU prices; adjacency by k-nearest; volume/duration consistent with a chosen avg power; seeded.
- [ ] **1.4** `scripts/download_data.py` + `cli download`: try Dryad / GitHub for UrbanEV (FR-D1), save to `data/raw/urbanev/`; on failure print exact manual steps; never crash the pipeline (fall back per config).
- [ ] **1.5** **Inspect the real UrbanEV files** (if present): list files, shapes, column names, time range, units. Write findings to `docs/data.md` (this resolves assumption **A1**). Then implement `UrbanEVAdapter` to map the real layout → canonical schema (time × zone matrices → long format; capacity from station info; coordinates; adjacency; distances; weather).
- [ ] **1.6** `data/quality.py`: gap handling (FR-D3), drop stations > 20 % missing, produce `artifacts/data_quality.json` + markdown summary.
- [ ] **1.7** `data/split.py`: chronological 70/15/15 → `artifacts/split.json` (index + timestamps).
- [ ] **1.8** `data/store.py` (`DataStore`, dense arrays, `.npz` cache) and `data/history.py` (`HistoryView`, `LeakageError`).
- [ ] **1.9** Estimate per-station `avg_power_kw` and `tau_h` from the **training period only** (FR-Q3) → saved into `stations.parquet`.
- [ ] **1.10** `cli prepare` runs adapter → quality → split → store; idempotent (skips if hashes match).
- [ ] **1.11** Tests: schema validation, adapter output on the fixture, missing-value policy, split monotonicity, `HistoryView` raising `LeakageError`, tau clipping.
- [ ] **1.12** Optional `notebooks/01_eda.ipynb` (daily/weekly patterns, saturation share, price schedule).

**Exit gate:** `python -m evision.cli prepare` works on synthetic data (and on real data if present); `pytest backend/tests -k "data or history"` green; `docs/data.md` written.

---

## Phase 2 — Features + leakage tests (FR-F3, §9.4)

- [ ] **2.1** `features/build.py::build_features` per `architecture.md §5` with feature groups `time | occupancy | weather | price | spatial`.
- [ ] **2.2** Vectorised shifting (no Python loops over rows); output `float32`; drop rows with `t < min_history_h` or NaN target.
- [ ] **2.3** Leakage test: features at `t` identical when built from `data[:t+1]` vs full data (random sample of `t`).
- [ ] **2.4** Test: tariff features at `t+h` are the only future-looking input; weather uses bucket ≤ t.
- [ ] **2.5** Test: split indices strictly increasing, no overlap; warm-up respected.
- [ ] **2.6** Document each feature in `docs/data.md#features`.

**Exit gate:** leakage tests green (`pytest backend/tests/leakage`).

---

## Phase 3 — Baselines + XGBoost forecasting (FR-F*)

- [ ] **3.1** `forecasting/baselines.py`: `persistence(store, t_idx, h)`, `historical_average_expanding(store, ...)` (cumulative sums by hour-of-week, data ≤ t only).
- [ ] **3.2** `forecasting/metrics.py`: MAE, RMSE, sMAPE (ε-guarded), R², plus slicing helpers (by horizon, hour, capacity bucket).
- [ ] **3.3** `forecasting/xgb_model.py`: `train_mean` per horizon with early stopping on validation; hyper-parameters in config (`max_depth`, `eta`, `subsample`, `n_estimators` with cap).
- [ ] **3.4** `forecasting/registry.py`: save/load model + JSON metadata (config hash, data hash, split hash, metrics, versions).
- [ ] **3.5** `forecasting/train.py::train_all` + `cli train`; prints a forecast-metrics table (baselines vs XGBoost, h=1..3, val and test).
- [ ] **3.6** **Feature-group ablation** (FR-F5): retrain with each group removed + time-only; write `artifacts/reports/ablation_forecast.csv`.
- [ ] **3.7** Tests: baselines on a hand-made series, metric functions, model train/predict round-trip on the fixture (small `n_estimators`), registry save/load.

**Exit gate:** on synthetic data XGBoost beats persistence on validation MAE for h=1..3 (if it does not, investigate for bugs — not by changing metrics). `cli train` completes in a few minutes on a laptop.

---

## Phase 4 — Uncertainty (FR-U*)

- [ ] **4.1** `train_quantile` (multi-quantile `reg:quantileerror`, quantiles 0.1/0.5/0.9); sort quantiles to prevent crossing; clip [0,1].
- [ ] **4.2** `forecasting/conformal.py`: `fit_cqr`, `apply_cqr` (per horizon, validation only). Store `qhat` in the registry.
- [ ] **4.3** Metrics: coverage, mean width, pinball loss, coverage by hour-of-day and by occupancy level, reliability data (nominal vs empirical for several α). Save as `artifacts/reports/uncertainty.json`.
- [ ] **4.4** `forecasting/store.py::ForecastStore.precompute(...)`: predictions for **val+test** window, all stations, h=1..3 (`point`, raw & calibrated `q10/q50/q90`, `hist_avg`) → `artifacts/forecasts/<dataset>.npz`; `cli precompute`.
- [ ] **4.5** Confidence score + label helper (`FR-U5`).
- [ ] **4.6** Tests: CQR on synthetic residuals gives ≈ nominal coverage; calibration never touches test; interval monotonicity; store arrays align with `ts`.

**Exit gate:** test-set coverage of the calibrated 80 % interval is reported; it should be roughly 70–90 % (if wildly off, check calibration code; document honestly if distribution shift explains it). Forecast store file generated.

---

## Phase 5 — Decision engine (FR-Q*, FR-R*)

- [ ] **5.1** `decision/queueing.py::erlang_c_wait_min` (use the reference in `architecture.md §7`). Tests per FR-Q6 plus: vectorisation equals scalar loop; `c` up to 200 stable; saturation flag.
- [ ] **5.2** `decision/geo.py`: `haversine_km`, `travel_time_min`; `RoutingProvider` stub for OSMnx (not implemented until Phase 9).
- [ ] **5.3** `decision/carbon.py`: `ScenarioCarbonProvider` (flat / tou_profile / low / high). `source = "scenario"`.
- [ ] **5.4** `decision/costs.py`: `price_total`, `carbon_kg`, `generalised_cost`, `total_time_min` (formulas `specs §5.5–5.6`).
- [ ] **5.5** `decision/candidates.py`: top-k within radius × delays; drop `required_h > 3`.
- [ ] **5.6** `decision/pareto.py`: `pareto_mask`, `label_options` with deterministic tie-breaks. Tests: hand-made frontier, duplicate points, single candidate, all identical.
- [ ] **5.7** `decision/explain.py`: cost-term breakdown, queue intermediates, vs-nearest deltas, templated sentence (e.g. "Chosen because its upper-bound wait (≈ X min) is still lower than the nearest station's expected wait (≈ Y min)"). No LLMs, no randomness.
- [ ] **5.8** `decision/engine.py::recommend` — single entry point; strategies `uncertainty_aware | point_forecast | current_availability | historical_average | nearest | cheapest`; returns options, Pareto set, dominated set, `params_used`.
- [ ] **5.9** Property tests (hypothesis, small): `κ=0` ⇒ same choice as point-forecast; higher occupancy never lowers wait; Pareto set non-empty when candidates exist; FASTEST has min time among Pareto set.
- [ ] **5.10** Golden test: fixed inputs → fixed JSON output (`tests/golden/recommend_basic.json`).

**Exit gate:** `pytest backend/tests -k "queue or pareto or engine"` green; a REPL snippet in `docs/results.md#engine-demo` shows one real recommendation with the three options.

---

## Phase 6 — Replay evaluator + reports (FR-E*)

- [ ] **6.1** `evaluation/strategies.py`: strategy objects wrapping `engine.recommend` (and `oracle` computed from truth). Same candidate set for all strategies.
- [ ] **6.2** `evaluation/replay.py`: decision-time loop per `architecture.md §8`; `sample_origins` deterministic per `(seed, t_idx)`; `reveal()` is the only place reading beyond `t_idx` and runs after choices are frozen.
- [ ] **6.3** `evaluation/metrics.py`: regret (mean/median/P90/zero-regret share), averages of realised wait/distance/cost/carbon, station-load imbalance (+Gini), failure rate, high-uncertainty subset flagging (top quartile interval width).
- [ ] **6.4** `evaluation/stats.py`: paired bootstrap CIs (2,000 resamples, seed), win/tie/loss rates vs each baseline.
- [ ] **6.5** Settings A (station-only) and B (station+time) (`specs §9.2`).
- [ ] **6.6** `evaluation/sensitivity.py`: sweeps over `risk_kappa`, VOT, carbon scenario; (optional) `origins_per_hour`, radius.
- [ ] **6.7** `evaluation/report.py`: figures (regret histogram & bars with CI, regret by hour, coverage reliability, κ sensitivity, forecast metrics) + `report.md` + `docs/results.md` with a Findings section **generated from the numbers** (templated sentences: "uncertainty-aware reduced mean regret by X% (95 % CI …) vs point-forecast" or "did not significantly differ").
- [ ] **6.8** Run artifacts: `artifacts/runs/<run_id>/…` with config & hashes; `cli evaluate` and `cli reproduce` (prepare → train → precompute → evaluate → seed-db).
- [ ] **6.9** **Leakage test suite** (`tests/leakage/`): mutate data after `t` → identical choices; `HistoryView` guard; `reveal` called after `choose` (use a spy); calibration isolation; determinism (run twice → identical `metrics.json`).
- [ ] **6.10** Performance check: full synthetic run < 10 min; if real data is large, enable `concurrent.futures` over decision times.

**Exit gate:** `make reproduce` runs end-to-end on synthetic data, writes a run directory, two consecutive runs produce byte-identical `metrics.json`; `pytest backend/tests/leakage` green; `docs/results.md` generated with honest findings.

---

## Phase 7 — Backend API + DB (FR-A*)

- [ ] **7.1** `db/models.py` (SQLAlchemy 2.0, tables per `architecture.md §4.3`), `db/session.py`, `db/seed.py` (`cli seed-db`: stations, model registry, runs, metrics, decisions, ablation, sensitivity, cross-city).
- [ ] **7.2** `api/schemas.py` Pydantic models mirroring `specs.md §6` exactly (request validation limits included).
- [ ] **7.3** `api/main.py`: app factory, lifespan context (`AppContext`: settings, store, forecast store, registry, engine, db), CORS from env, request-id + access-log middleware, error handlers, in-memory rate limit for POST.
- [ ] **7.4** Routes: `health`, `meta`, `stations` (list/detail/forecast/reveal), `recommend` (single/compare), `evaluation` (runs/regret/uncertainty/ablation/sensitivity/cross-city), `insights` (stub until Phase 11), `queueing/explain`.
- [ ] **7.5** Hot-path optimisation: `/stations` from numpy arrays + LRU cache.
- [ ] **7.6** `as_of` snapping/validation, `no_candidates` handling, 422 messages.
- [ ] **7.7** `reveal` logic: truth for `as_of+1..3h`, realised wait proxy, realised regret vs hindsight-best (for `/recommend/compare`).
- [ ] **7.8** Export OpenAPI: `scripts/export_openapi.py` → `frontend/openapi.json`.
- [ ] **7.9** API tests with `httpx.AsyncClient` on synthetic bundle: each endpoint's happy path + validation errors + contract shape; `POST /recommend` identical to calling `engine.recommend` directly (consistency test); performance smoke (`/stations` < 800 ms, `/recommend` < 1.5 s locally).

**Exit gate:** `make serve` then `curl localhost:8000/api/v1/meta` and a sample `POST /recommend` return valid JSON; `/docs` shows all endpoints; API tests green.

---

## Phase 8 — Frontend dashboard (FR-UI*)

**Step 0 — gate:** `view` every file in `design/inspiration/` and write `docs/design-notes.md` (layout, palette, type, components, map/chart styling). Derive `frontend/src/styles/tokens.css`. If the folder is empty, use the fallback theme (`specs §7.2`) and note it.

- [ ] **8.1** Scaffold Vite + React + TS (strict) + Tailwind + Router + TanStack Query + zustand; ESLint/Prettier; `npm run gen:api` (openapi-typescript) → `src/api/types.gen.ts`; `client.ts` + typed hooks.
- [ ] **8.2** `AppShell`: nav, dataset/“SYNTHETIC DATA” banner, theme toggle (data-theme), responsive layout.
- [ ] **8.3** `MapView` with station markers (canvas), occupancy layer toggle (current/+1/+2/+3 h), origin pin (drag/click), radius circle, OSM attribution, list-view alternative.
- [ ] **8.4** `TimeMachine` (range from `/meta`), ±1 h step buttons, URL query sync (`?t=…&lat=…&lon=…`) so views are shareable.
- [ ] **8.5** `PreferencesPanel` mapped to request params, defaults from `/meta`, reset button, tooltips explaining each parameter in plain language.
- [ ] **8.6** Recommend flow: debounce → `POST /recommend` → three `OptionCard`s with confidence + carbon-assumption badges; selection highlights route/marker.
- [ ] **8.7** `ExplanationDrawer`: `CostBreakdownBar`, `ForecastBandChart`, `QueueSteps` (calls `/queueing/explain` or uses payload), vs-nearest deltas, assumption list.
- [ ] **8.8** `TradeoffChart` (time × price, carbon colour, Pareto line, click-to-select).
- [ ] **8.9** `RevealPanel` ("Reveal what actually happened"), clearly labelled evaluation-only.
- [ ] **8.10** Station detail page (history + forecast bands h=1..3, heat map, neighbours).
- [ ] **8.11** Compare page (all strategies' picks + realised outcomes + regret).
- [ ] **8.12** Evaluation page with tabs (Overview, Uncertainty, Ablation, Sensitivity, Forecast metrics, Cross-city, Reproduce) and the "what this does/does not show" callout.
- [ ] **8.13** Insights page (wire to Phase 11 API; show empty state until then).
- [ ] **8.14** About/Methodology page: pipeline diagram, M/M/c explainer, leakage protocol, assumptions A1–A9, limitations, non-goals, literature positioning, SDG table (7, 11, 13, secondary 12), team/guide from config.
- [ ] **8.15** Loading skeletons, empty, error states (`QueryState`), toasts for API failures.
- [ ] **8.16** Accessibility pass (labels, focus, contrast ≥ AA, keyboard map alternative), responsive checks at 375 / 768 / 1280 px.
- [ ] **8.17** Tests: Vitest for `format`, `colors`, components (cards, badges, preference panel); Playwright smoke: load → set origin → three options visible → open explanation → reveal.
- [ ] **8.18** `npm run build` clean; Lighthouse performance ≥ 80 (desktop); no console errors.

**Exit gate:** with backend running on synthetic data, the smoke test passes; screenshots of each page saved to `docs/screenshots/`; visual comparison vs inspiration images noted in `docs/design-notes.md`.

---

## Phase 9 — Optional extras (flagged P1/P2; implement after core is green)

- [ ] **9.1** (P1) `forecasting/ensemble.py`: K=5 XGBoost seeds/subsamples; `uncertainty.method: ensemble`; evaluate coverage vs CQR; add to uncertainty tab.
- [ ] **9.2** (P2) `forecasting/lstm_model.py` (PyTorch, small GRU/LSTM, CPU); `pip install .[lstm]`; guarded import; compare MAE/RMSE with XGBoost in the forecast-metrics table. Code path absent from the default Docker image.
- [ ] **9.3** (P2) `decision/geo.py` OSMnx provider: download/cached graph for the bbox, nearest-node routing, `routing.provider: osmnx`; precompute station-to-node mapping; fall back to haversine on failure.
- [ ] **9.4** (P2) `ElectricityMapsCarbonProvider` (token from env, cached responses); UI badge flips to `observed` only if the provider is active and returned data for that time/place.
- [ ] **9.5** (P2) Fleet scheduling demo (greedy assignment of N vehicles; shows total regret vs independent choices) — keep to one page/section and one API endpoint.

**Exit gate:** with each flag off, the system behaves exactly as before; with each on, its own tests pass.

---

## Phase 10 — CHARGED + cross-city (FR-X*)

- [ ] **10.1** Inspect CHARGED files (Zenodo record `15763454` / GitHub `IntelligentSystemsLab/CHARGED`); document layout in `docs/data.md`.
- [ ] **10.2** `CHARGEDAdapter`: per-city canonical files; handle missing columns (e.g., no tariff) by config defaults and flags; mark per-city quality report.
- [ ] **10.3** `evaluation/cross_city.py` + `cli cross-city`: train on source city (default Shenzhen), calibrate on source validation, evaluate zero-shot on each target city with the replay protocol; record forecast metrics, coverage, regret vs baselines.
- [ ] **10.4** Load results into `cross_city` table; wire `GET /evaluation/cross-city` and the UI tab; empty-state message if data not downloaded.
- [ ] **10.5** Tests using a **synthetic second city** (different parameters) so the code path is verified without CHARGED.
- [ ] **10.6** Write the "Roadmap to major project" section (GNN/Transformer, domain adaptation, conformal under shift, grid-aware optimisation, live APIs) in `docs/results.md` and the About page.

**Exit gate:** cross-city command runs on synthetic two-city data and on real CHARGED if available; UI tab shows results or the empty state.

---

## Phase 11 — Insights (FR-I*)

- [ ] **11.1** `evaluation/insights.py`: per-station mean/peak utilisation, saturation share, hour×weekday heat map, over/under-used ranking (thresholds in config), load-balance index (Gini).
- [ ] **11.2** `GET /insights/utilisation?from=&to=` + tests.
- [ ] **11.3** Insights page: ranking tables, heat map, map overlay (over/under-used markers), applications text.
- [ ] **11.4** (P2) Link to fleet demo from Phase 9.5 if built.

**Exit gate:** page renders real numbers; API test green.

---

## Phase 12 — Docker, CI, deployment (FR-OPS*)

- [ ] **12.1** `deploy/Dockerfile.backend` (multi-stage, non-root, lock-file install, optional `WITH_LSTM`), `.dockerignore`.
- [ ] **12.2** `deploy/Dockerfile.frontend` + `nginx.conf` (SPA fallback, `/api/` proxy, gzip, caching).
- [ ] **12.3** `deploy/docker-compose.yml` (+ dev override): services, volumes `artifacts` & `data`, healthchecks, `.env.example`, optional `bootstrap` profile running `evision reproduce`.
- [ ] **12.4** `make bundle` → `evision-artifacts.tar.gz` (derived artifacts only); `docs/deployment.md`: single-VM steps (Docker + Caddy TLS example), PaaS notes (Render/Railway/Fly), how to restore the bundle, backups, resource sizing.
- [ ] **12.5** Full CI (`.github/workflows/ci.yml`): backend (ruff, mypy, pytest + coverage), frontend (lint, tsc, vitest, build), docker (build, run with synthetic bundle, curl `/health` and `POST /recommend`).
- [ ] **12.6** Fresh-machine drill: clone → `cp .env.example .env` → `docker compose --profile bootstrap up` (synthetic fallback if no data) → open `http://localhost` → full user journey works.

**Exit gate:** CI green; the fresh-machine drill is documented in `docs/deployment.md` and passes.

---

## Phase 13 — Hardening, docs, final QA

- [ ] **13.1** Coverage ≥ 80 % on `decision/`, `evaluation/`, `forecasting/`; fix flaky tests; `mypy --strict` on `decision/` and `evaluation/`.
- [ ] **13.2** Security pass: input limits, CORS, rate limit, headers in nginx (CSP basics, `X-Content-Type-Options`), dependency audit (`pip-audit`, `npm audit`), no secrets in git history.
- [ ] **13.3** Re-run `make reproduce` on the **real dataset** if available; regenerate `docs/results.md` and screenshots; double-check findings text matches numbers.
- [ ] **13.4** Read the UI Methodology page against `specs.md §0.1` and `§1.2` — every honest-framing statement and non-goal present.
- [ ] **13.5** README: what it is, screenshot, quickstart (3 commands), architecture diagram, data instructions, how to run tests/evaluation, deployment links, citation list (from the report's reference section), licence notes.
- [ ] **13.6** `docs/assumptions.md` final review: A1–A9 resolved/updated with real findings (e.g., A1 true file layout).
- [ ] **13.7** Remove dead code/TODOs, check logs are quiet in normal use, final lint/format.

---

## 14. Task detail cheat-sheet (where numbers come from)

| Need | Source |
|---|---|
| Formulas (M/M/c, costs, carbon, regret) | `specs.md §5`, `§9.3` |
| Default parameter values | `specs.md §11` (assumptions A9, must be shown in UI) |
| API shapes | `specs.md §6` |
| UI pages and behaviour | `specs.md §7` |
| DB schema | `architecture.md §4.3` |
| Module/function layout | `architecture.md §2, §5–§8` |
| Deployment layout | `architecture.md §11` |

### Suggested command surface (keep exactly; docs and CI rely on it)
```bash
make setup                 # venv/uv + npm install
make bootstrap             # download|synthetic → prepare → train → precompute → evaluate → seed-db
make reproduce             # same as bootstrap but wipes artifacts first; asserts determinism
make serve                 # uvicorn backend on :8000
make frontend-dev          # vite dev server on :5173 (proxy /api → :8000)
make test                  # pytest + vitest
make bundle                # artifacts tarball for deployment
make docker-up             # docker compose up --build
python -m evision.cli --help
```

### Risks and fallbacks

| Risk | Fallback |
|---|---|
| UrbanEV download blocked / manual only | Synthetic adapter + tiny fixture; real adapter tested on fixture slice; instructions printed |
| Real file layout differs from report (zones vs stations) | Treat unit as "station"; document in `docs/data.md`, assumption A1 |
| Occupancy saturates (censored demand) | ρ cap + wait cap + `saturated` flag; mention in limitations |
| XGBoost training too slow | Subsample stations/time for ablations; `n_estimators` cap; `hist` tree method; float32 |
| Quantile model coverage off | Rely on CQR; report empirical coverage honestly |
| Proposed strategy does **not** beat baselines | Report as-is (valid finding); show where it helps/hurts (high-variance subset); never retune on test |
| Replay too slow | Vectorise candidates; parallelise over `t_idx`; reduce `origins_per_hour` (document) |
| Frontend images missing | Fallback theme + TODO note; tokens make re-skin trivial |
| CHARGED unavailable | Synthetic second-city test; UI empty state |
| Heavy deps (torch, osmnx) | Optional extras; defaults never import them |

---

## 15. Final acceptance checklist (run before declaring done)

- [ ] `specs.md §12` Definition of Done items 1–7 all true.
- [ ] Every `FR-*` marked P0 or P1 in `specs.md` is implemented, or its exclusion is recorded with a reason in `docs/decisions.md`.
- [ ] Leakage tests, determinism test, API contract tests, unit tests: all green locally and in CI.
- [ ] `docker compose up` on a clean machine works; user journey (origin → time → three options → explanation → trade-off chart → reveal) verified manually and by Playwright.
- [ ] Evaluation page shows: strategy table with CIs, regret distribution, high-uncertainty subset, coverage/width, ablation, sensitivity, setting A & B, cross-city (or empty state).
- [ ] Carbon is labelled "scenario assumption" everywhere; synthetic data is labelled everywhere it is used.
- [ ] Methodology page includes honest framing, limitations, non-goals, SDG mapping.
- [ ] README quickstart verified by following it literally.
- [ ] No secrets, raw datasets or large binaries committed.
