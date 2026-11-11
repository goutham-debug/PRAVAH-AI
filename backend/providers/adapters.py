"""Concrete adapters. Only Open-Meteo and OpenStreetMap (Overpass) are keyless public APIs.
IMD, KSNDMC, CWC, GBA/BBMP and NRSC Bhuvan are *authorised-endpoint* adapters: they make real requests only after the
operator supplies the endpoint (and credentials where the provider requires them) through environment variables.
No endpoint, key or response is invented here."""
from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import formats
from .base import (Adapter, AdapterResult, FAILED, FORECAST, INVALID, NOT_CONFIGURED, OBSERVED, OFFICIAL, OK,
                   UNAVAILABLE, UNVERIFIED, now_iso)
from .http import fetch

INGEST_DIR = Path(os.environ.get("INGEST_DIR") or Path(__file__).resolve().parent.parent / "data" / "ingested")


def _num(v) -> Optional[float]:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _store(key: str, content: bytes, ext: str) -> str:
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    path = INGEST_DIR / f"{key}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.{ext}"
    path.write_bytes(content)
    return str(path)


class OpenMeteoAdapter(Adapter):
    key, provider, name = "open_meteo", "Open-Meteo", "Weather forecast (rainfall, temperature, wind)"
    dataset_type = "weather_forecast"
    source_url = "https://api.open-meteo.com/v1/forecast"
    licence = "CC BY 4.0 (attribution); free tier is non-commercial — check terms for operational use"
    coverage = "Study-area point (lat/lon from configuration)"
    ttl_seconds = 1800
    notes = "Model output (forecast/reanalysis), not gauge observations and not a flood warning."

    def __init__(self, lat: float, lon: float):
        self.lat, self.lon = lat, lon

    def run(self) -> AdapterResult:
        params = {"latitude": self.lat, "longitude": self.lon, "timezone": "Asia/Kolkata", "forecast_days": 2,
                  "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                  "hourly": "temperature_2m,precipitation,precipitation_probability"}
        ev = [f"GET {self.source_url}"]
        r = fetch(self.source_url, params=params, timeout=(3.5, 10), retries=2, cache_ttl=0)
        ev.append(f"HTTP {r.status_code} after {r.attempts} attempt(s), {r.elapsed_ms} ms" if r.status_code
                  else f"No response after {r.attempts} attempt(s): {r.error}")
        if not r.ok:
            return AdapterResult(FAILED, UNAVAILABLE, error=r.error, http_status=r.status_code, attempts=r.attempts,
                                 duration_ms=r.elapsed_ms, events=ev)
        try:
            raw = r.json()
        except Exception as e:  # noqa: BLE001
            return AdapterResult(INVALID, UNAVAILABLE, error=f"Invalid JSON: {e}", attempts=r.attempts,
                                 duration_ms=r.elapsed_ms, events=ev)
        errs, warns = [], []
        cur, hourly = raw.get("current") or {}, raw.get("hourly") or {}
        for k, lo, hi in (("temperature_2m", -20, 60), ("relative_humidity_2m", 0, 100),
                          ("precipitation", 0, 500), ("wind_speed_10m", 0, 400)):
            v = _num(cur.get(k))
            if v is None:
                errs.append(f"current.{k} missing")
            elif not lo <= v <= hi:
                errs.append(f"current.{k}={v} outside plausible range")
        times, rain = hourly.get("time") or [], hourly.get("precipitation") or []
        if not times or len(times) != len(rain):
            errs.append("hourly series missing or length mismatch")
        if errs:
            ev.append("Validation failed: " + "; ".join(errs))
            return AdapterResult(INVALID, UNAVAILABLE, error="; ".join(errs), validation={"ok": False, "errors": errs,
                                 "warnings": warns, "records": 0}, http_status=r.status_code, attempts=r.attempts,
                                 duration_ms=r.elapsed_ms, events=ev)
        ev.append("Validation passed")
        payload = {"current": cur, "hourly": {"time": times, "precipitation": rain,
                                              "temperature_2m": hourly.get("temperature_2m") or [],
                                              "precipitation_probability": hourly.get("precipitation_probability") or []},
                   "latitude": raw.get("latitude"), "longitude": raw.get("longitude")}
        return AdapterResult(OK, FORECAST, records=len(times), payload=payload, observed_at=cur.get("time"),
                             validation={"ok": True, "errors": [], "warnings": warns, "records": len(times)},
                             http_status=r.status_code, attempts=r.attempts, duration_ms=r.elapsed_ms,
                             checksum=r.sha256, events=ev)

    def probe(self):
        r = fetch(self.source_url, params={"latitude": self.lat, "longitude": self.lon, "current": "temperature_2m"},
                  timeout=(3, 5), retries=0)
        return ("REACHABLE" if r.ok else "UNREACHABLE", r.error or f"HTTP {r.status_code}, {r.elapsed_ms} ms")


class OverpassRoadsAdapter(Adapter):
    key, provider, name = "osm_roads", "OpenStreetMap (Overpass API)", "Road network (highway ways)"
    dataset_type = "road_network"
    source_url = "https://overpass-api.de/api/interpreter"
    licence = "ODbL 1.0 — © OpenStreetMap contributors (attribution required)"
    fmt = "json"
    ttl_seconds = 7 * 86400
    notes = "Community-mapped, not an official authority record. Directions/closures/flood status are not included."
    HIGHWAYS = "motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"

    def __init__(self, bbox: str):
        self.bbox = bbox  # south,west,north,east
        self.coverage = f"Study-area bounding box S,W,N,E = {bbox}"

    def query(self) -> str:
        return f'[out:json][timeout:60];way["highway"~"^({self.HIGHWAYS})$"]({self.bbox});out tags geom;'

    def run(self) -> AdapterResult:
        ev = [f"POST {self.source_url} (bbox {self.bbox})"]
        r = fetch(self.source_url, method="POST", data={"data": self.query()}, timeout=(5, 90), retries=1, backoff=3)
        ev.append(f"HTTP {r.status_code} after {r.attempts} attempt(s), {r.elapsed_ms} ms" if r.status_code
                  else f"No response after {r.attempts} attempt(s): {r.error}")
        if not r.ok:
            return AdapterResult(FAILED, UNAVAILABLE, error=r.error, http_status=r.status_code, attempts=r.attempts,
                                 duration_ms=r.elapsed_ms, events=ev)
        obj, rep = formats.parse_json(r.content)
        errs, warns = list(rep["errors"]), []
        ways = [e for e in (obj or {}).get("elements", []) if e.get("type") == "way"] if isinstance(obj, dict) else []
        if isinstance(obj, dict) and not ways:
            errs.append("No highway ways returned for bounding box")
        no_geom = sum(1 for w in ways if not w.get("geometry"))
        if ways and no_geom:
            warns.append(f"{no_geom} ways lack geometry")
        if ways and no_geom == len(ways):
            errs.append("No way has geometry")
        base = (obj or {}).get("osm3s", {}).get("timestamp_osm_base") if isinstance(obj, dict) else None
        validation = {"ok": not errs, "errors": errs, "warnings": warns, "records": len(ways)}
        if errs:
            ev.append("Validation failed: " + "; ".join(errs))
            return AdapterResult(INVALID, UNAVAILABLE, error="; ".join(errs), validation=validation,
                                 http_status=r.status_code, attempts=r.attempts, duration_ms=r.elapsed_ms, events=ev)
        path = _store(self.key, r.content, "json")
        ev.append(f"Validation passed ({len(ways)} ways); stored {path}")
        return AdapterResult(OK, OBSERVED, records=len(ways), payload=None, observed_at=base, validation=validation,
                             http_status=r.status_code, attempts=r.attempts, duration_ms=r.elapsed_ms,
                             checksum=r.sha256, storage_path=path, events=ev)

    def probe(self):
        r = fetch("https://overpass-api.de/api/status", timeout=(3, 5), retries=0)
        return ("REACHABLE" if r.ok else "UNREACHABLE", r.error or f"HTTP {r.status_code}, {r.elapsed_ms} ms")


class AuthorisedEndpointAdapter(Adapter):
    """Adapter for providers that need operator-supplied access.

    Environment (PREFIX = IMD | KSNDMC | CWC | GBA | BHUVAN):
      <PREFIX>_URL            authorised dataset/API URL (required)
      <PREFIX>_API_KEY        credential (required where `needs_key`)
      <PREFIX>_AUTH_HEADER    header name for the key (default Authorization -> "Bearer <key>")
      <PREFIX>_FORMAT         json | csv | geojson | shapefile | geotiff (default: adapter default)
      <PREFIX>_OBSERVED_FIELD top-level JSON key holding the observation timestamp (optional)
    """
    needs_key = True
    default_class = OFFICIAL

    @property
    def prefix(self) -> str:
        return self.key.upper()

    @property
    def required_env(self):  # type: ignore[override]
        return [f"{self.prefix}_URL"] + ([f"{self.prefix}_API_KEY"] if self.needs_key else [])

    def endpoint(self) -> str:
        return os.environ.get(f"{self.prefix}_URL", "").strip()

    def run(self) -> AdapterResult:
        missing = self.missing_env()
        if missing:
            return AdapterResult(NOT_CONFIGURED, UNAVAILABLE, missing_credentials=missing,
                                 error="Access not configured: " + ", ".join(missing),
                                 events=[f"Skipped: missing {', '.join(missing)}"])
        url, fmt = self.endpoint(), os.environ.get(f"{self.prefix}_FORMAT", self.fmt).lower()
        headers = {}
        key = os.environ.get(f"{self.prefix}_API_KEY", "").strip()
        if key:
            hdr = os.environ.get(f"{self.prefix}_AUTH_HEADER", "Authorization")
            headers[hdr] = f"Bearer {key}" if hdr.lower() == "authorization" else key
        ev = [f"GET {url.split('?')[0]} (format {fmt})"]
        r = fetch(url, headers=headers, timeout=(5, 60), retries=2, backoff=1.5)
        ev.append(f"HTTP {r.status_code} after {r.attempts} attempt(s), {r.elapsed_ms} ms" if r.status_code
                  else f"No response after {r.attempts} attempt(s): {r.error}")
        if not r.ok:
            return AdapterResult(FAILED, UNAVAILABLE, error=r.error, http_status=r.status_code, attempts=r.attempts,
                                 duration_ms=r.elapsed_ms, events=ev)
        obj, rep = formats.validate(fmt, r.content)
        observed = None
        field_name = os.environ.get(f"{self.prefix}_OBSERVED_FIELD", "").strip()
        if field_name and isinstance(obj, dict) and obj.get(field_name):
            observed = str(obj[field_name])
        if field_name and not observed:
            rep.setdefault("warnings", []).append(f"Observation field '{field_name}' not found")
        if not rep["ok"]:
            ev.append("Validation failed: " + "; ".join(rep["errors"]))
            return AdapterResult(INVALID, UNAVAILABLE, error="; ".join(rep["errors"]), validation=rep,
                                 http_status=r.status_code, attempts=r.attempts, duration_ms=r.elapsed_ms, events=ev)
        ext = {"geojson": "geojson", "shapefile": "zip", "geotiff": "tif"}.get(fmt, fmt)
        path = _store(self.key, r.content, ext)
        ev.append(f"Validation passed ({rep['records']} records); stored {path}")
        return AdapterResult(OK, self.default_class, records=rep["records"], observed_at=observed, validation=rep,
                             http_status=r.status_code, attempts=r.attempts, duration_ms=r.elapsed_ms,
                             checksum=r.sha256, storage_path=path, events=ev)

    def probe(self):
        if not self.configured():
            return ("NOT_CONFIGURED", "Missing: " + ", ".join(self.missing_env()))
        r = fetch(self.endpoint(), method="GET", headers={}, timeout=(3, 5), retries=0)
        # An auth-protected endpoint answering 401/403 is reachable but we do not send credentials on probes.
        if r.status_code in (401, 403):
            return ("REACHABLE", f"HTTP {r.status_code} (endpoint up; credentials not sent on probe)")
        return ("REACHABLE" if r.ok else "UNREACHABLE", r.error or f"HTTP {r.status_code}, {r.elapsed_ms} ms")


class IMDAdapter(AuthorisedEndpointAdapter):
    key, provider, name = "imd", "India Meteorological Department", "Weather observations, rainfall and warnings"
    dataset_type = "weather_observation_warning"
    source_url = "https://mausam.imd.gov.in"
    licence = "Per IMD data-supply terms (access/approval required)"
    coverage = "Karnataka / Bengaluru stations"
    ttl_seconds = 3 * 3600
    notes = "No public documented API is assumed. Set IMD_URL/IMD_API_KEY after obtaining authorised access."


class KSNDMCAdapter(AuthorisedEndpointAdapter):
    key, provider, name = "ksndmc", "KSNDMC", "Rainfall telemetry and disaster-monitoring information"
    dataset_type = "rainfall_telemetry"
    source_url = "https://ksndmc.karnataka.gov.in"
    licence = "Per KSNDMC data-sharing terms (approval required)"
    coverage = "Karnataka rain-gauge telemetry stations"
    ttl_seconds = 3600
    notes = "Set KSNDMC_URL/KSNDMC_API_KEY after obtaining authorised access."


class CWCAdapter(AuthorisedEndpointAdapter):
    key, provider, name = "cwc", "Central Water Commission / India-WRIS", "River water-level information"
    dataset_type = "river_water_level"
    source_url = "https://indiawris.gov.in"
    licence = "Per CWC / India-WRIS terms"
    coverage = "CWC gauging stations (relevance to Bengaluru urban catchment must be confirmed)"
    ttl_seconds = 6 * 3600
    notes = "Set CWC_URL (and CWC_API_KEY if required) once an authorised endpoint is confirmed."


class GBAAdapter(AuthorisedEndpointAdapter):
    key, provider, name = "gba", "GBA / BBMP", "Official ward boundaries and civic GIS"
    dataset_type = "ward_boundaries"
    source_url = "https://bbmp.gov.in"
    licence = "Per GBA/BBMP open-data licence"
    coverage = "Bengaluru wards"
    fmt = "geojson"
    needs_key = False
    ttl_seconds = 30 * 86400
    notes = "Provide GBA_URL pointing to an official GeoJSON/Shapefile download (set GBA_FORMAT accordingly)."


class BhuvanAdapter(AuthorisedEndpointAdapter):
    key, provider, name = "bhuvan", "NRSC Bhuvan", "Geographic and flood-hazard layers"
    dataset_type = "flood_hazard_layer"
    source_url = "https://bhuvan.nrsc.gov.in"
    licence = "Per NRSC Bhuvan terms (registration/token may be required)"
    coverage = "Karnataka / Bengaluru layers as available"
    fmt = "geojson"
    ttl_seconds = 30 * 86400
    notes = "Set BHUVAN_URL (WFS/GeoJSON or GeoTIFF download) and BHUVAN_API_KEY if a token is issued."


def build_adapters(lat: float, lon: float, bbox: str) -> Dict[str, Adapter]:
    ads = [OpenMeteoAdapter(lat, lon), OverpassRoadsAdapter(bbox), IMDAdapter(), KSNDMCAdapter(), CWCAdapter(),
           GBAAdapter(), BhuvanAdapter()]
    return {a.key: a for a in ads}
