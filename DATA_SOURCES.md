# Data sources and status

Live state is shown in the app under **Data Operations** (authority roles). This file documents what each source needs.

| Provider | Registry key | Access | Status in this build | To enable |
|---|---|---|---|---|
| Open-Meteo (forecast) | `open_meteo` | Public, keyless | Implemented; **not verified against the live API in the build sandbox (no internet)** — class FORECAST | none |
| OpenStreetMap via Overpass (roads) | `osm_roads` | Public, keyless (ODbL) | Implemented; not verified live. Downloads to `backend/data/ingested/`; routing graph is **not yet rebuilt from it** | none |
| IMD (observations, rainfall, warnings) | `imd` | Authorised access needed | Adapter only — NOT_CONFIGURED | `IMD_URL`, `IMD_API_KEY` |
| KSNDMC (rain-gauge telemetry) | `ksndmc` | Authorised access needed | Adapter only — NOT_CONFIGURED | `KSNDMC_URL`, `KSNDMC_API_KEY` |
| CWC / India-WRIS (water level) | `cwc` | Authorised endpoint to be confirmed | Adapter only — NOT_CONFIGURED | `CWC_URL`, `CWC_API_KEY` |
| GBA / BBMP (wards, civic GIS) | `gba` | Official file/URL | Adapter only — NOT_CONFIGURED | `GBA_URL`, `GBA_FORMAT` |
| NRSC Bhuvan (hazard layers) | `bhuvan` | Token/endpoint to be confirmed | Adapter only — NOT_CONFIGURED | `BHUVAN_URL`, `BHUVAN_API_KEY` |

No IMD/KSNDMC/CWC/GBA/Bhuvan endpoint, schema or key is assumed by the code. The adapters fetch the URL you supply,
validate the format (JSON, CSV, GeoJSON, Shapefile zip, GeoTIFF header), store the file with a checksum and record
provenance. Field-level mapping of these datasets into the analysis tables is a later stage.

## Datasets with no source yet (UNAVAILABLE in the app)
Hospitals/critical facilities (state health registry), shelters and capacities, response teams/resources.

## Quarantined development data
`backend/data/dev_quarantine/` — fictional/unverified wards, roads, hospitals, shelters, teams. Off by default
(`LOAD_PILOT_DATASET=false`), refused in production, loaded as UNVERIFIED, fictional contact names/phones never loaded.

## Classification vocabulary
OBSERVED · OFFICIAL · FORECAST · MODELLED · UNVERIFIED · STALE (last success older than 3x refresh interval) ·
UNAVAILABLE · NOT_ASSESSED (never retrieved).
