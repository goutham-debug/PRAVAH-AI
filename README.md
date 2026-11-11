# PRAVAH AI — Urban Flood Impact Intelligence & Evacuation Platform

**Whitefield–Mahadevapura Region, Bengaluru (BBMP)**  
An integrated operational intelligence platform for government disaster authorities (BBMP, KSDMA, SDRF, NDRF).

---

## 🚀 Quick Start (Local Run)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env
python app.py
```
- Starts Flask server at `http://127.0.0.1:5000`
- Initial bootstrap admin:
  - **Email:** `admin@example.test`
  - **Password:** Set a unique `BOOTSTRAP_ADMIN_PASSWORD` in `backend/.env` before first startup. The system prompts for a password change upon first login.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Opens dashboard at `http://localhost:5173`
- Production build: `npm run build`

### 3. Run Test Suite
```bash
# From project root
python -m pytest tests -v
```
- **85 tests passing (100%)** across all methodology stages.

---

## 🏛️ Six-Stage Operational Methodology

| Stage | Module | Key Capabilities |
|---|---|---|
| **Stage 1** | **Data Ingestion & Integrity** | Schema validation, quarantine isolation, classification badges (`OBSERVED`, `MODELLED`, `UNVERIFIED`, `UNAVAILABLE`) |
| **Stage 2** | **Flood Risk Screening** | Explainable formula $R = 0.35P + 0.20E + 0.25H + 0.20D$, factor contributions, `NOT_ASSESSED` guard |
| **Stage 3** | **Geospatial & Network Analysis** | NetworkX directed graph, articulation points, bridges, edge betweenness, GeoPandas EPSG:3857, Shapely 350m lake buffers |
| **Stage 4** | **Intelligent Evacuation Routing** | Dijkstra & A* routing, coordinate snapping (3.0 km), closure avoidance, alternative routes, hazard warnings |
| **Stage 5** | **Resource Optimisation** | Capacity-constrained shelter allocation (zero overflow), capability-aware rescue squad assignment (boat squads, pumps, ambulances) |
| **Stage 6** | **Scenario Simulation** | Multi-stage simulation on graph copies, baseline vs disrupted vs restored comparative delta matrix |

---

## 🤖 AI Assistant & Operational Telemetry

- **AI Assistant (`/authority/ai`):** Answers operational queries strictly grounded in backend algorithmic assessments. Refuses autonomous dispatch orders.
- **SITREP Generator (`/authority/sitrep`):** Generates structured incident command reports with Markdown download.
- **System Execution Monitor (`/authority/monitor`):** Real in-memory thread-safe event ring buffer showing genuine execution cycles and live provider diagnostics.
- **Data Operations (`/authority/data-operations`):** Full data registry, provider health, and background ingestion scheduler status.

---

## 📖 Key Documentation Files

- [FINAL_HANDOFF.md](FINAL_HANDOFF.md): Comprehensive Part 3 delivery report, architecture, and endpoints.
- [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md): Full test execution log (85 passed, 0 failed).
- [API_CONFIGURATION_GUIDE.md](API_CONFIGURATION_GUIDE.md): Credentials, registration links, and configuration steps for all external APIs.
- [REAL_DATA_READINESS.md](REAL_DATA_READINESS.md): Audit table of provider status and data provenance.
- [DATA_SOURCES.md](DATA_SOURCES.md): Datasets in use, schemas, coverage, and licensing.
- [.env.example](.env.example): Environment variable template.
