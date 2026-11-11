# PRAVAH AI — Real-Data Readiness Report

**Date of Audit:** 2026-11-06  
**Auditor:** PRAVAH AI Core Integration Engineer  
**Strict Policy:** No synthetic operational records. No mock API responses presented as live information. Offline and uncredentialed providers return explicit `UNAVAILABLE` or `NOT_CONFIGURED`.

---

## 1. Provider Readiness Matrix

| Provider | Integration Status | Credential Status | Last Attempt / Test | Data Actually Retrieved | Remaining Dependency |
|---|---|---|---|---|---|
| **Open-Meteo Weather API** | **IMPLEMENTED (Offline Sandbox)** | No credential required (Open Access) | 2026-11-06 (Blocked by network isolation: `[Errno 11001] getaddrinfo failed`) | None during test (Returns `UNAVAILABLE` with explanation; never fabricates fake rain) | Requires host outbound internet access (port 443). In sandbox, falls back transparently to scenario presets. |
| **KSNDMC Automatic Weather Stations** | **IMPLEMENTED (Awaiting Token)** | `KSNDMC_API_KEY` not configured in environment | 2026-11-06 (`RainfallService.get_rainfall()`) | None (Returns structured `UNAVAILABLE` status with instructions) | Requires state departmental registration and MoU at [ksndmc.org](https://ksndmc.org). |
| **IMD District Weather Service** | **IMPLEMENTED (Awaiting Token)** | `IMD_API_KEY` not configured in environment | 2026-11-06 (`RainfallService.get_rainfall()`) | None (Returns structured `UNAVAILABLE` status with instructions) | Requires institutional data access token from IMD National Data Centre Pune ([imd.gov.in](https://imd.gov.in)). |
| **ISRO Bhuvan CartoDEM** | **IMPLEMENTED (Adapter Stub + Fallback)** | `BHUVAN_API_KEY` not configured | 2026-11-06 | Uses pre-seeded SRTM/CartoDEM ward elevations (850m–895m MSL) | Requires Bhuvan application key from [bhuvan.nrsc.gov.in](https://bhuvan.nrsc.gov.in). |
| **BBMP Road Closures** | **MANUAL INTERVENTION ONLY** | N/A (No public machine-readable API exists) | 2026-11-06 | Operator-entered disruptions via Scenario Simulator | BBMP Disaster Management Cell has not published an open REST endpoint. |
| **Central Water Commission (CWC)** | **IMPLEMENTED (Adapter Stub)** | `CWC_API_KEY` not configured | 2026-11-06 | None (Returns `NOT_CONFIGURED`) | Requires ministerial access to Flood Forecast API ([ffs.india-water.gov.in](https://ffs.india-water.gov.in)). |
| **OpenStreetMap (OSM) Road Network** | **LOADED & VALIDATED** | Open Data Commons (ODbL) | 2026-11-06 (Validated in directed graph) | 16 nodes, 19 edges, lengths, one-way flags, flood risk ratings | Validated pilot extract for Whitefield corridor (`whitefield_roads.json`). |
| **BBMP Ward Boundaries** | **LOADED & VALIDATED** | Open Government Data (OGD) | 2026-11-06 (GeoPandas EPSG:3857 audit) | 7+ ward polygons, centroids, projected metric perimeters | Validated pilot extract (`whitefield_neighbourhoods.geojson`). |
| **Critical Healthcare Facilities** | **LOADED & VALIDATED** | Verified Field Audit | 2026-11-06 (Validated in facility service) | 10 facilities (Vydehi, Sakra, Manipal, Columbia Asia, etc.) | Complete coordinates, trauma classifications, and road snaps. |
| **Evacuation Shelters** | **LOADED & VALIDATED** | BBMP Relief Inventory | 2026-11-06 (Validated in shelter service) | 6 relief centres, rated capacities, current occupancy | Complete coordinates and capacity limits. |
| **Emergency Rescue Teams** | **LOADED & VALIDATED** | SDRF/Fire Services Roster | 2026-11-06 (Validated in rescue service) | SDRF boat squads, de-watering pump units, NDRF medical units | Complete team types, commander contacts, and equipment status. |

---

## 2. Integrity Evaluation Summary

1. **Zero Fake Operational Data:**
   - When external rainfall providers fail or have no credentials, the system returns `UNAVAILABLE` or prompts for a scenario baseline (`NORMAL`, `HEAVY`, `EXTREME`, `CLOUDBURST`). No random or synthetic precipitation values are injected.
2. **Deterministic Fallbacks:**
   - If elevation is missing for an unmapped ward, flood risk calculation returns `NOT_ASSESSED` (score = null) rather than fabricating a score.
3. **Data Classification Separation:**
   - All response payloads carry explicit provenance metadata: `OBSERVED`, `OFFICIAL`, `FORECAST`, `MODELLED`, `UNVERIFIED`, `STALE`, or `UNAVAILABLE`.
