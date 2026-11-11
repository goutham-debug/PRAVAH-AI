# PRAVAH AI — Final Project Handoff & Production Delivery

**Platform:** PRAVAH AI Urban Flood Impact Intelligence & Evacuation Routing Engine  
**Operational Zone:** Whitefield–Mahadevapura Corridor, Bengaluru (BBMP)  
**Status:** COMPLETE (All 6 Methodology Stages Implemented, Integrated, and Validated)  
**Date of Delivery:** 2026-11-06  
**Backend Framework:** Flask (Python 3.14 / 3.11+)  
**Frontend Framework:** React 18 + TypeScript + Vite + MapLibre GL JS + Tailwind CSS  
**Test Suite:** 85/85 tests passed (100%)  
**Production Build:** 0 errors (1608 modules transformed)  

---

## 1. Executive Summary & Methodology Fulfillment

All six core methodology stages are fully implemented, connected end-to-end, and validated:

```mermaid
flowchart LR
    S1[Stage 1: Ingestion & Verification] --> S2[Stage 2: Flood Susceptibility Screening]
    S2 --> S3[Stage 3: Geospatial & Graph Network Analysis]
    S3 --> S4[Stage 4: Intelligent Evacuation Routing]
    S4 --> S5[Stage 5: Resource Optimisation]
    S5 --> S6[Stage 6: Scenario Simulation]
    S6 --> AI[Grounded AI & SITREP Generation]
    AI --> Mon[Execution Monitor]
```

### Stage 1: Data Ingestion & Integrity Protection ✅
- Schema validation, data quarantine, and provenance classification: `OBSERVED`, `OFFICIAL`, `FORECAST`, `MODELLED`, `UNVERIFIED`, `STALE`, `UNAVAILABLE`, `NOT_ASSESSED`.
- Quarantined pilot data loaded only when `LOAD_PILOT_DATASET=true`. Strictly isolated in dev mode.

### Stage 2: Weighted Flood Risk Assessment Engine ✅
- **Formula:** $R = 0.35P + 0.20E + 0.25H + 0.20D$
- Normalised factor scaling (0–100).
- `NOT_ASSESSED` return code when essential elevation or drainage inputs are unavailable — zero fabrication.
- Per-factor contributions, percentage of total, primary driver identification, and scientific disclaimers.

### Stage 3: Geospatial & Network Analysis ✅
- Directed graph built using **NetworkX** preserving real geographic topology.
- Graph analytics: Articulation points, topological bridges, edge betweenness centrality, connected components.
- Spatial analytics: **GeoPandas** projected area (EPSG:3857) and perimeter calculations; **Shapely** 350m buffer intersections with Bellandur Lake, Varthur Lake, and the K-100 Rajakaluve canal.
- Critical road link ranking with natural-language `why_critical` rationale.
- Healthcare facility dependency mapping: identifies arterial roads supporting 2+ hospital transit routes.

### Stage 4: Intelligent Evacuation Routing ✅
- Dual algorithm support: **Dijkstra** and **A\*** with Haversine admissible heuristic.
- Coordinate snapping within 3.0 km threshold.
- Verified closure avoidance (inundated/disrupted segments completely excluded from graph).
- Alternative route generation via 4× primary edge penalisation.
- Turn-by-turn directions with flood hazard zone warnings per step.

### Stage 5: Resource Optimisation ✅
- **Capacity-Constrained Shelter Allocation:** Solves minimum-cost flow / greedy matching matching displaced ward populations to shelters under strict capacity ceilings. Unmet demand explicitly reported.
- **Capability-Aware Rescue Assignment:** Matches SDRF inflatable boat squads, BBMP high-flow de-watering pump units, and NDRF ambulances to verified incidents by severity and accessibility. Enforces zero duplicate squad assignments.

### Stage 6: Scenario Simulation & Comparative Analysis ✅
- Independent graph copies for all simulations — baseline network is never mutated.
- Baseline vs. Disrupted vs. Restored comparative matrix: deltas for network integrity, isolated wards, hospital access times, and shelter demand relief.
- All intervention outputs strictly badged as `MODELLED`.

### AI Assistant & Automated Situation Reports (SITREPs) ✅
- **AI Assistant:** Grounded queries on flood risk, critical links, hospital access, and shelter capacities. Refuses autonomous dispatch orders.
- **SITREP Generator:** Generates structured operational reports with executive summaries, metric matrices, priority action recommendations, and downloadable Markdown export.

### Real Execution Monitor ✅
- In-memory thread-safe event ring buffer capturing real backend cycles (API requests, geospatial processing, routing calculations).
- Live health probes for API, SQLite/PostGIS database, and external providers with auto-refreshing UI.

---

## 2. Inventory of Implemented Files

### Backend Services (`backend/services/`)
- `flood_engine.py`: Explainable multi-factor susceptibility engine ($R = 0.35P + 0.20E + 0.25H + 0.20D$).
- `graph_service.py`: NetworkX directed graph analysis, articulation points, bridges, betweenness.
- `geo_service.py`: GeoPandas EPSG:3857 boundaries and Shapely 350m water body buffers.
- `facility_service.py`: Dijkstra healthcare accessibility matrix and hospital dependency links.
- `routing_service.py`: Dijkstra + A* routing, coordinate snapping, closure avoidance, alternative routes.
- `shelter_service.py`: Capacity-constrained greedy/min-cost flow shelter allocation.
- `rescue_service.py`: Capability-matching rescue coordination with zero duplicate assignments.
- `scenario_service.py`: Multi-stage simulation on graph copies with comparative delta matrix.
- `situation_report_service.py`: Deterministic SITREP generation and Markdown export.
- `ai_service.py`: Grounded AI question answering from model outputs.
- `event_logger.py`: Thread-safe in-memory execution event ring buffer.
- `rainfall_service.py`: Telemetric rainfall provider wrapper (KSNDMC / IMD).
- `health_service.py`: Database and Flask API live diagnostic probes.

### Backend REST Routes (`backend/routes/`)
- `auth_routes.py`: JWT authentication, password rotation, RBAC.
- `flood_routes.py`: `POST /api/flood/assess`, `GET /api/flood/formula`.
- `road_routes.py`: `POST /api/roads/route`, `GET /api/roads/critical-links`, `GET /api/roads/network-analysis`, `POST /api/roads/closure-impact`.
- `geo_routes.py`: `GET /api/geo/boundaries/analysis`, `GET /api/geo/water-bodies/proximity`, `GET /api/geo/neighbourhoods/geojson`.
- `facility_routes.py`: `POST /api/facilities/accessibility`.
- `shelter_routes.py`: `GET /api/shelters`, `POST /api/shelters/allocate`.
- `rescue_routes.py`: `GET /api/rescue/teams`, `POST /api/rescue/coordinate`, `POST /api/rescue/teams/<id>/status`.
- `scenario_routes.py`: `POST /api/scenarios/simulate`, `POST /api/scenarios/compare`, `GET /api/scenarios/candidate-disruptions`.
- `situation_report_routes.py`: `POST /api/sitrep/generate`, `POST /api/sitrep/export/markdown`.
- `ai_routes.py`: `POST /api/ai/query`.
- `monitor_routes.py`: `GET /api/monitor/events`, `GET /api/monitor/health`.
- `system_routes.py`: `GET /api/system/status`.
- `dataops_routes.py`: `GET /api/dataops/overview`, `GET /api/dataops/datasets`.

### Frontend Pages (`frontend/src/pages/authority/`)
- `CommandCentrePage.tsx`: Interactive MapLibre overview with live KPI cards and closure status.
- `FloodIntelligencePage.tsx`: Explainable P/E/H/D factor breakdown and primary risk driver cards.
- `ImpactAnalysisPage.tsx`: Population exposure and hazard ranking from live API.
- `NeighbourhoodPage.tsx`: Boundary metrics, drainage vulnerability, and ward polygons.
- `CriticalFacilitiesPage.tsx`: Trauma centre travel times and hospital dependency road list.
- `EvacuationPlanningPage.tsx`: Dijkstra vs A* route planner, turn-by-turn steps, and hazard alerts.
- `ShelterManagementPage.tsx`: Capacity allocation, remaining capacity, and unmet demand alerts.
- `RescueOperationsPage.tsx`: Mission dispatch roster and idle squad status.
- `ScenarioSimulatorPage.tsx`: Baseline vs disrupted vs restored comparative analysis.
- `RoadIntelligencePage.tsx`: Critical links, articulation points, and topological bridges.
- `SituationReportsPage.tsx`: SITREP reader with live metrics and Markdown download.
- `AIAssistantPage.tsx`: Grounded AI assistant with operational disclaimers.
- `SystemMonitorPage.tsx`: Live execution event stream and provider diagnostic cards.
- `DataOperationsPage.tsx`: Data registry, provider status, and ingestion audit log.

---

## 3. How to Run the Project Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.14 / 3.11)
- Node.js 18+ (Tested on Node.js v20)
- PowerShell (Windows) or Bash (macOS/Linux)

### Step 1: Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item ..\.env.example .env

# Run database setup and start Flask server
python app.py
```
*The backend starts at `http://127.0.0.1:5000` with the SQLite database initialized and pilot datasets loaded.*

### Step 2: Frontend Setup (in a separate terminal)
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*The frontend dashboard opens at `http://localhost:5173`.*

### Step 3: Run the Test Suite
```powershell
# From project root
python -m pytest tests -v
```
*Executes all 85 unit and integration tests across Stages 1–6.*

### Step 4: Login Credentials
- **Email:** `admin@example.test`
- **Password:** Set a unique `BOOTSTRAP_ADMIN_PASSWORD` in `backend/.env` before first startup. The system prompts for a password change upon first login.

---

## 4. Real Data Status & Limitations

- **Open-Meteo:** Fully integrated. In environments with direct internet access, hourly rainfall is fetched. In sandboxed environments without outbound DNS, the system gracefully falls back to scenario presets (`UNAVAILABLE` classification).
- **KSNDMC / IMD:** Service wrappers implemented with credential guards. When keys are omitted, returns transparent `UNAVAILABLE` states.
- **Elevation Data:** SRTM/CartoDEM elevations for all 10 Mahadevapura wards are pre-seeded (`KNOWN_WARD_ELEVATIONS`).
- **Road Network & Boundaries:** Loaded from validated GeoJSON/JSON extracts for the Whitefield pilot corridor.

*PRAVAH AI — Final Delivery Complete | Technical review ready.*
