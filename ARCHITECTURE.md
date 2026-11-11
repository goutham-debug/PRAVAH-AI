# Architecture

```
Browser (React/TS, MapLibre)  --HTTPS /api-->  Flask API  --SQLAlchemy/TLS-->  Supabase Postgres
                                   |
                                   +-- security.py: session check + role policy on every request
                                   +-- services/: graph (NetworkX), routing, flood index, scenario, shelter, rescue, sitrep, weather
```

- **Auth**: `routes/auth_routes.py`, `routes/admin_routes.py`, `security.py` (single `before_request` guard; public: `/api/health`, `/api/auth/login`).
- **Shared assessment**: the frontend `AssessmentContext` holds one set of road closures and rainfall assumption; every module sends the same inputs to the backend engine. Default is baseline (no closures).
- **Engine**: baseline graph is never mutated; scenarios run on copies. Flood index is a screening index (MODELLED), not flood depth.
- **Database**: Supabase Postgres via `DATABASE_URL`; schema in `supabase/migrations/`. RLS enabled, no policies (backend-only access).
- **Data layer**: `providers/` (HTTP with timeout/retry/cache, format validators, adapters) → `services/ingestion_service.py` (registry `data_sources`, `ingestion_runs`, `ingestion_events`) → `routes/dataops_routes.py` (authority-only; UI polls). Weather panel also records into the registry.
- **Known gaps**: PostGIS point columns only (ward/road geometry tables, graph rebuild from OSM and field mapping of official feeds are Part 2); IMD/KSNDMC/CWC/GBA/Bhuvan adapters need credentials; scheduler is opt-in; no per-assessment ID/versioning; no PDF export; no self-service password reset by email.
