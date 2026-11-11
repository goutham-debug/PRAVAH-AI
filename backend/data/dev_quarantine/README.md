# QUARANTINED DEVELOPMENT DATA — NOT REAL

These files were created for early development. They are **not verified against any official source**.
Ward polygons/populations, road graph, hospitals (bed counts), shelters (capacities) and response teams are
placeholders. Contact names/phone numbers in them are never loaded.

- Loaded only when `LOAD_PILOT_DATASET=true` and `APP_ENV` is not `production` (production start is refused otherwise).
- Every record loaded from here is stored with `verification_status = UNVERIFIED`.
- Replace with: GBA/BBMP wards, OSM roads (see Data Operations), state health registry, official shelter and
  resource registers.
