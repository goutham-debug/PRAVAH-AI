# PRAVAH AI — Part 2 Handoff Document

**Date:** 2026-11-06  
**Status:** COMPLETE — Stages 2, 3, and 4 implemented and validated  
**Tests:** 72 passed, 0 failures  
**Frontend build:** ✓ 0 errors  

---

## 1. Architecture Overview

### Backend (Flask)
| Component | Location | Purpose |
|---|---|---|
| Entry point | `backend/app.py` | Flask app factory, blueprint registration, CORS |
| Models | `backend/models.py` | SQLAlchemy ORM (Users, Neighbourhoods, Roads, Facilities, Incidents) |
| Services | `backend/services/` | Business logic layer |
| Routes | `backend/routes/` | REST API blueprints |
| Data | `backend/data/dev_quarantine/` | Pilot datasets (UNVERIFIED — dev only) |
| Config | `backend/config.py` | Environment-based configuration |

**Database:** SQLite (`pravah_dev.db`) in development. Schema managed by SQLAlchemy `create_all()`.  
**Auth:** JWT tokens via `flask-jwt-extended`. RBAC with `AUTHORITY` and `PUBLIC` roles enforced per route.  
**Dev data loading:** Set `LOAD_PILOT_DATASET=true` to load quarantined pilot data on startup.

### Frontend (React 18 + Vite + TypeScript)
| Component | Location | Purpose |
|---|---|---|
| Entry | `frontend/src/main.tsx` | React root mount |
| API client | `frontend/src/api/client.ts` | Centralised Axios-based API layer |
| Pages | `frontend/src/pages/authority/` | Authority dashboard pages |
| Map | `frontend/src/components/PravahMap.tsx` | MapLibre GL JS integration |
| Auth | `frontend/src/context/AuthContext.tsx` | JWT session management |

**Styling:** Tailwind CSS  
**Map:** MapLibre GL JS (open-source, no API key required for base tiles)  
**Build tool:** Vite (production build: `npm run build`)

---

## 2. Completed Methodology Stages

### Stage 2 — Weighted Flood Risk Assessment ✅

**Formula:** R = 0.35P + 0.20E + 0.25H + 0.20D

| Factor | Weight | Source | Justification |
|---|---|---|---|
| P (Rainfall intensity) | 0.35 | Open-Meteo / IMD | Primary trigger for urban flooding |
| E (Elevation vulnerability) | 0.20 | SRTM / CartoDEM (KNOWN_WARD_ELEVATIONS) | Low-lying areas accumulate runoff |
| H (Historical flood vulnerability) | 0.25 | BBMP flood records (pilot data) | Recurrence is best predictor |
| D (Drainage vulnerability) | 0.20 | BBMP drainage network data | Inadequate drainage amplifies risk |

**Key implementation details:**
- All factors normalised to 0–100 scale before weighting
- Returns `NOT_ASSESSED` (risk_score = null) if any factor is unavailable — never fabricates
- Per-factor `weighted_contribution`, `pct_of_total`, `source`, `freshness` in every response
- `primary_driver` field identifies the dominant contributing factor
- Full methodology metadata via `GET /api/flood/formula`
- Scientific disclaimer present: this is a screening index, not a 1D/2D hydrodynamic model
- Data classification: OBSERVED / OFFICIAL / FORECAST / MODELLED / UNVERIFIED / STALE / UNAVAILABLE maintained strictly

**Elevation lookup (KNOWN_WARD_ELEVATIONS):**
- Pre-seeded SRTM/CartoDEM elevations for 10 Mahadevapura wards (850m–895m MSL range)
- Fallback: population density proxy (higher density → assumed lower elevation catchment)
- If neither available: E factor = None → NOT_ASSESSED

### Stage 3 — Geospatial and Network Analysis ✅

**Road Graph (NetworkX DiGraph):**
- 16 nodes (intersections), ~19 directed edges (road segments)
- Edge attributes: `length_km`, `flood_risk`, `one_way`, `name`, `road_type`, `elevation_m`
- Flood-risk weighted edge costs: Low=1.0×, Moderate=1.25×, High=1.75×, Severe=3.0×

**Network analyses implemented:**
- Connected components (weakly and strongly)
- Articulation points (cut vertices whose removal disconnects the graph)
- Bridge edges (cut edges)
- Edge betweenness centrality (identifies structurally critical road links)
- Road closure impact simulation with network status: `NORMAL` / `DEGRADED` / `CRITICAL_SPLIT`
- `why_critical` natural-language explanation for each critical link

**Spatial analyses (GeoPandas + Shapely):**
- Neighbourhood boundary analysis: projected area (EPSG:3857), perimeter, centroid validation
- Water-body proximity: 350m Shapely buffer around Bellandur Lake, Varthur Lake, K-100 Rajakaluve canal
- Road-drainage intersection identification
- `find_neighbourhood_for_point()` uses Shapely `.contains()` with real GeoJSON polygons

**Hospital accessibility (facility_service.py):**
- Dijkstra path traversal from each ward centroid to each hospital
- `road_facility_dependencies`: roads appearing on 2+ hospital routes ranked by count
- `nearest_trauma_mins`, `nearest_trauma_name` per ward
- Emergency transit speed: 25 km/h (conservative crawl for flood conditions)
- `NOT_ASSESSED` returned if ward or hospital is topologically isolated

### Stage 4 — Intelligent Routing ✅

**Algorithms:**
- **Dijkstra**: Standard shortest-path using weighted edge costs
- **A\***: Haversine-admissible heuristic for faster convergence on sparse graph

**Cost function:** `weight = length_km × (1.0 + flood_risk_penalty)`  
Penalties: Low=0.0, Moderate=0.25, High=0.75, Severe=2.0

**Features:**
- Coordinate snapping to nearest road node within 3.0 km threshold
- Confirmed closure avoidance (closed roads excluded from graph entirely)
- Alternative route via 4× primary edge penalisation (forces detour)
- Turn-by-turn directions with flood hazard zone labels per step
- `high_risk_segments` list, `route_explanation`, `safety_notice`, `traffic_notice`
- Topological isolation detection: `is_isolated: true` with explanation
- Route distance (km), estimated travel time at 25 km/h, road names list

**Disclaimers always present:**
- No live traffic data: routing uses static network distance only
- No flood depth validation: road passability not verified without live sensor data
- Route described as `MODELLED`, not `SAFE`

---

## 3. API Contract

### New Endpoints Added in Part 2

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/flood/assess` | AUTHORITY | Explainable multi-factor flood risk assessment |
| `GET` | `/api/flood/formula` | AUTHORITY | Methodology metadata, weights, justification |
| `GET` | `/api/roads/critical-links` | AUTHORITY | Ranked critical links with `why_critical` |
| `GET` | `/api/roads/network-analysis` | AUTHORITY | Graph topology: articulation points, bridges |
| `POST` | `/api/roads/closure-impact` | AUTHORITY | Road closure impact simulation |
| `GET` | `/api/geo/boundaries/analysis` | AUTHORITY | GeoPandas neighbourhood polygon analysis |
| `GET` | `/api/geo/water-bodies/proximity` | AUTHORITY | Shapely 350m buffer water proximity |
| `POST` | `/api/facilities/accessibility` | AUTHORITY | Dijkstra hospital reachability matrix |

### Existing Endpoints Updated in Part 2

| Method | Endpoint | Change |
|---|---|---|
| `POST` | `/api/roads/route` | Added `algorithm` param (dijkstra/astar), enriched response with explanation, alternative route, turn-by-turn |

### Response Schema Standards
All endpoints return:
```json
{
  "status": "success|error|not_assessed",
  "data": { ... },
  "metadata": {
    "assessment_id": "uuid",
    "dataset_version": "string",
    "generated_at": "ISO8601",
    "data_classification": "UNVERIFIED|OBSERVED|OFFICIAL|...",
    "source": { ... }
  },
  "errors": []
}
```

---

## 4. Files Created in Part 2

| File | Purpose |
|---|---|
| `tests/test_stage2_flood_risk.py` | 5 tests: weights, normalisation, NOT_ASSESSED, component breakdown, provenance |
| `tests/test_stage3_network_geospatial.py` | 8 tests: directed graph, components, articulation points, bridges, critical links, closure impact, GeoPandas boundaries, Shapely buffer, hospital accessibility |
| `tests/test_stage4_routing.py` | 6 tests: Dijkstra, A*, snap threshold, closure avoidance, alternative route, isolation handling |
| `PART2_HANDOFF.md` | This document |

---

## 5. Files Modified in Part 2

### Backend Services
| File | Key Changes |
|---|---|
| `backend/services/flood_engine.py` | Full rewrite: R=w1P+w2E+w3H+w4D formula, NOT_ASSESSED logic, KNOWN_WARD_ELEVATIONS, factor provenance, methodology metadata |
| `backend/services/graph_service.py` | Full rewrite: flood-risk weighted costs, articulation points, bridge analysis, edge betweenness, closure impact simulation, `why_critical` text |
| `backend/services/geo_service.py` | Full rewrite: GeoPandas EPSG:3857 projected analysis, Shapely `.contains()`, water-body 350m buffer, real water-body coordinates |
| `backend/services/facility_service.py` | Full rewrite: Dijkstra hospital accessibility matrix, `road_facility_dependencies`, `nearest_trauma_*` fields |
| `backend/services/routing_service.py` | Full rewrite: Dijkstra + A* with Haversine heuristic, coordinate snapping, closure avoidance, alternative route, turn-by-turn, isolation detection |

### Backend Routes
| File | Key Changes |
|---|---|
| `backend/routes/flood_routes.py` | Added `POST /api/flood/assess`, `GET /api/flood/formula` |
| `backend/routes/road_routes.py` | Added `GET /api/roads/critical-links`, `GET /api/roads/network-analysis`, `POST /api/roads/closure-impact` |
| `backend/routes/geo_routes.py` | Added `GET /api/geo/boundaries/analysis`, `GET /api/geo/water-bodies/proximity` |

### Frontend
| File | Key Changes |
|---|---|
| `frontend/src/api/client.ts` | Added `getRoadCriticalLinks()`, `getRoadNetworkAnalysis()`, `getFacilityAccessibility()`, `getBoundaryAnalysis()`, `getWaterBodyProximity()`. Updated `planJourney()` with `algorithm` param |
| `frontend/src/pages/authority/FloodIntelligencePage.tsx` | Full rewrite: P/E/H/D factor breakdown, weighted contributions, primary driver, source provenance, NOT_ASSESSED handling, loading/error states |
| `frontend/src/pages/authority/RoadIntelligencePage.tsx` | Full rewrite: 3-tab UI (Critical Links, All Roads, Topology), `why_critical` rationale, bridge/betweenness columns, articulation points and bridges cards |
| `frontend/src/pages/authority/ImpactAnalysisPage.tsx` | Dynamic population metrics from API (removed hardcoded values), risk_score column, error/loading states |
| `frontend/src/pages/authority/CriticalFacilitiesPage.tsx` | Full rewrite: live `getFacilityAccessibility()`, `critical_facility_dependency_roads`, `nearest_trauma_mins`, loading/error states |
| `frontend/src/pages/authority/EvacuationPlanningPage.tsx` | Full rewrite: Dijkstra/A* algorithm selector, isolation warning, `route_explanation`, alternative route summary, `traffic_notice` |
| `frontend/src/pages/authority/NeighbourhoodPage.tsx` | Added `drainage_factor` column, loading/empty/error states |

---

## 6. Datasets Used

All datasets are in `backend/data/dev_quarantine/` and classified as **UNVERIFIED** (dev pilot only).  
They are loaded only when `LOAD_PILOT_DATASET=true`.

| Dataset | File | Records | Coverage |
|---|---|---|---|
| Road network | `whitefield_roads.json` | 16 nodes, 19 edges | Mahadevapura pilot zone, Bengaluru |
| Neighbourhood polygons | `whitefield_neighbourhoods.geojson` | 7+ polygons | Mahadevapura wards (EPSG:4326 GeoJSON) |
| Facilities | `facilities.json` | 10 (4 hospitals, 2 TERTIARY_TRAUMA) | Mahadevapura area |
| Shelters | `shelters.json` | 6 | Mahadevapura area |
| Rescue teams | `rescue_teams.json` | Variable | Mahadevapura area |

**Hardcoded reference data (not pilot datasets):**
- `KNOWN_WARD_ELEVATIONS`: 10 ward elevations from SRTM/CartoDEM (850m–895m MSL, public domain)
- `WATER_BODIES`: Bellandur Lake, Varthur Lake, K-100 Rajakaluve canal (coordinates from OpenStreetMap / BBMP surveys, used for proximity analysis only)

---

## 7. External Integrations

| Integration | Status | Notes |
|---|---|---|
| Open-Meteo (weather) | ✅ Working (Part 1) | No API key required. Used for P factor when available |
| IMD / KSNDMC rainfall API | ⚠️ NOT CONFIGURED | No credentials provided. P factor falls back to UNAVAILABLE |
| BBMP flood incident API | ⚠️ NOT CONFIGURED | H factor uses pilot data only |
| BBMP drainage network API | ⚠️ NOT CONFIGURED | D factor uses pilot data only |
| PostGIS | ⚠️ NOT CONFIGURED | SQLite used in dev. PostGIS integration stubs present |
| MapLibre GL JS | ✅ Working (Part 1) | Open-source renderer, no API key |

---

## 8. Test Results

**Run command:** `cd pravah-ai && python -m pytest tests -q`  
**Result:** **72 passed, 141 warnings in 22.11s** ✅

| Test file | Tests | Status |
|---|---|---|
| `test_auth.py` | (Part 1) | ✅ |
| `test_data_registry.py` | (Part 1) | ✅ |
| `test_weather_service.py` | (Part 1) | ✅ |
| `test_scenario_service.py` | (Part 1) | ✅ |
| (Other Part 1 tests) | 53 total | ✅ |
| `test_stage2_flood_risk.py` | 5 | ✅ |
| `test_stage3_network_geospatial.py` | 8 | ✅ |
| `test_stage4_routing.py` | 6 | ✅ |
| **TOTAL** | **72** | **✅ ALL PASSED** |

**Frontend build:** `cd frontend && npm run build`  
**Result:** **✓ 1606 modules transformed, built in ~8s, 0 errors** ✅  
(Note: chunk size warning present — not an error, acceptable for dashboard application)

---

## 9. Database Changes

No schema changes from Part 1. The following tables were already present:
- `users`, `neighbourhoods`, `roads`, `facilities`, `incidents`, `shelters`

Part 2 services read road network, neighbourhood polygons, and facility data primarily from:
1. JSON files in `backend/data/dev_quarantine/` (pilot dev mode)
2. Database tables via SQLAlchemy (production mode)

No new migrations required. The SQLite `pravah_dev.db` is regenerated on startup from `create_all()`.

---

## 10. Architecture Decisions

### 10.1 NOT_ASSESSED over fabrication
When any flood risk factor (P, E, H, D) lacks verified data, the formula returns `NOT_ASSESSED` with a `missing_inputs` list. This prevents misleading risk scores from reaching operators.

### 10.2 Data classification separation
All API responses carry `data_classification` metadata. The frontend displays classification badges (OBSERVED, OFFICIAL, UNVERIFIED, etc.) so operators always know the provenance and reliability of displayed information.

### 10.3 Static road network for routing
The pilot road network (`whitefield_roads.json`) is a static JSON file — not a live OSM or traffic feed. Routes are labelled `MODELLED`. No live traffic claims are made.

### 10.4 GeoPandas EPSG:3857 projection
Neighbourhood area and perimeter calculations use EPSG:3857 (Web Mercator) projection to get results in metres. Input polygons are stored in EPSG:4326 (WGS84) and converted at analysis time. This avoids distorted degree-based measurements.

### 10.5 Flood-weighted routing cost
Edge weights incorporate flood risk as a multiplier on distance: `weight = length_km × (1.0 + penalty)`. This makes flooded roads costlier to traverse but does not exclude them entirely unless explicitly closed. This design correctly separates:
- **Topological accessibility** (can a path exist?)
- **Operational advisability** (should this route be used?)

### 10.6 25 km/h emergency transit speed
Used consistently across routing, facility accessibility, and evacuation planning. This conservative speed reflects crawl conditions during flood events. It is not based on live traffic data.

---

## 11. Remaining Work for Part 3

### High Priority
1. **PostGIS integration** — Replace SQLite + GeoPandas file reads with PostGIS spatial queries. Enables full spatial indexing, server-side buffer operations, and production scalability.
2. **Live rainfall API** — Connect IMD / KSNDMC API (requires credentials/MoU). Enables real-time P factor in flood risk assessments.
3. **NDRF/BBMP verified road closure API** — Live closure feed to replace manual closure input in routing.
4. **Historical flood records API** — BBMP flood history API (requires credentials) for validated H factor.

### Medium Priority
5. **1D/2D hydrodynamic model integration** — HEC-RAS or SWMM output integration for validated flood depth estimates. Currently the system produces a screening index only.
6. **Real-time incident verification pipeline** — Crowd-sourced incident reports with verification workflow before they affect routing or risk scores.
7. **Full OSM road network** — Replace 16-node pilot network with OpenStreetMap-derived complete network for Mahadevapura (via osmnx or Overpass API).
8. **Shelter accessibility routing** — Extend evacuation routing to include verified shelter destinations.

### Low Priority
9. **WebSocket real-time updates** — Push flood risk and road status updates to dashboard without page refresh.
10. **Mobile PWA** — Progressive Web App optimisation for field use on mobile.
11. **Report export** — PDF/CSV export of flood risk assessments for official record-keeping.
12. **Audit log frontend** — Display data access and assessment audit trail in the UI.

---

## 12. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Pilot road network has only 16 nodes / 19 edges | Routing covers only the pilot zone | Replace with full OSM network in Part 3 |
| No live rainfall API connected | P factor often UNAVAILABLE → NOT_ASSESSED result | Open-Meteo provides forecast fallback when configured |
| Flood risk formula not scientifically calibrated | Risk score is indicative only | Disclaimer present in all API responses and UI |
| No live road closure feed | Closures must be entered manually | Manual closure input available in routing UI |
| SQLite not suitable for production | Concurrent writes will fail | PostGIS migration planned for Part 3 |
| No flood depth validation | Road passability cannot be confirmed | Routes labelled MODELLED with safety notice |

---

## 13. Part 1 Functionality Preserved

The following Part 1 components were **not modified** in Part 2 and remain fully functional:
- Authentication (JWT, login, logout, session management)
- RBAC (AUTHORITY / PUBLIC role enforcement)
- Data Registry (dataset registration, versioning, audit trail)
- Ingestion Service (data ingestion pipeline with quarantine)
- Weather Service (Open-Meteo integration)
- Scenario Service (scenario creation and simulation)
- All Part 1 API endpoints
- All Part 1 frontend pages not listed in Section 5 above
- MapLibre GL JS map integration (PravahMap component)

All 53 Part 1 tests continue to pass.

---

*PRAVAH AI — Part 2 Handoff | Pilot Zone: Mahadevapura, Bengaluru (BBMP) | Classification: DEVELOPMENT*
