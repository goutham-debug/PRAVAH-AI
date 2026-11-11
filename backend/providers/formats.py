"""Format validators for JSON, CSV, GeoJSON, Shapefile (zip) and GeoTIFF.

Validation is structural and honest about its depth: GeoTIFF/Shapefile checks read headers only
(raster/vector analysis needs rasterio/pyshp, which are not required to run the platform).
"""
from __future__ import annotations

import csv
import io
import json
import struct
import zipfile
from typing import Any, Dict, List, Tuple

GEOJSON_TYPES = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"}


def parse_json(content: bytes) -> Tuple[Any, Dict]:
    try:
        obj = json.loads(content.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return None, {"ok": False, "errors": [f"Invalid JSON: {e}"], "warnings": [], "records": 0}
    n = len(obj) if isinstance(obj, (list, dict)) else 1
    empty = n == 0
    return obj, {"ok": not empty, "errors": ["Empty document"] if empty else [], "warnings": [], "records": n}


def parse_csv(content: bytes) -> Tuple[List[dict], Dict]:
    try:
        text = content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as e:  # noqa: BLE001
        return [], {"ok": False, "errors": [f"Invalid CSV: {e}"], "warnings": [], "records": 0}
    errors = [] if rows else ["No data rows"]
    return rows, {"ok": bool(rows), "errors": errors, "warnings": [], "records": len(rows)}


def validate_geojson(content: bytes) -> Tuple[Any, Dict]:
    obj, rep = parse_json(content)
    if not rep["ok"]:
        return obj, rep
    errors, warnings = [], []
    feats = []
    if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
        feats = obj.get("features") or []
    elif isinstance(obj, dict) and obj.get("type") == "Feature":
        feats = [obj]
    else:
        errors.append("Not a GeoJSON FeatureCollection/Feature")
    bad = 0
    for f in feats:
        g = (f or {}).get("geometry")
        if not g or g.get("type") not in GEOJSON_TYPES or "coordinates" not in g and g.get("type") != "GeometryCollection":
            bad += 1
    if feats and bad:
        warnings.append(f"{bad} of {len(feats)} features have missing/invalid geometry")
    if not feats and not errors:
        errors.append("No features")
    return obj, {"ok": not errors and bad < max(1, len(feats)), "errors": errors, "warnings": warnings,
                 "records": len(feats)}


def validate_shapefile_zip(content: bytes) -> Dict:
    try:
        z = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        return {"ok": False, "errors": ["Not a zip archive"], "warnings": [], "records": 0}
    names = {n.lower().rsplit(".", 1)[-1]: n for n in z.namelist() if "." in n}
    missing = [e for e in ("shp", "shx", "dbf") if e not in names]
    if missing:
        return {"ok": False, "errors": [f"Missing components: {', '.join(missing)}"], "warnings": [], "records": 0}
    warnings = [] if "prj" in names else ["No .prj file: coordinate reference system unknown"]
    shp = z.read(names["shp"])[:100]
    if len(shp) < 100 or struct.unpack(">i", shp[:4])[0] != 9994:
        return {"ok": False, "errors": ["Invalid .shp header"], "warnings": warnings, "records": 0}
    shape_type = struct.unpack("<i", shp[32:36])[0]
    dbf = z.read(names["dbf"])[:8]
    records = struct.unpack("<i", dbf[4:8])[0] if len(dbf) == 8 else 0
    return {"ok": records > 0, "errors": [] if records else ["DBF has no records"], "warnings": warnings,
            "records": records, "shape_type": shape_type}


def validate_geotiff(content: bytes) -> Dict:
    head = content[:16]
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        kind = "TIFF"
    elif head[:4] in (b"II+\x00", b"MM\x00+"):
        kind = "BigTIFF"
    else:
        return {"ok": False, "errors": ["Not a TIFF file"], "warnings": [], "records": 0}
    return {"ok": True, "errors": [], "warnings": [
        f"{kind} header verified only; GeoKeys/raster values not analysed (rasterio not installed)"], "records": 1}


def validate(fmt: str, content: bytes) -> Tuple[Any, Dict]:
    fmt = (fmt or "json").lower()
    if fmt == "json":
        return parse_json(content)
    if fmt == "csv":
        return parse_csv(content)
    if fmt == "geojson":
        return validate_geojson(content)
    if fmt == "shapefile":
        return None, validate_shapefile_zip(content)
    if fmt == "geotiff":
        return None, validate_geotiff(content)
    return None, {"ok": False, "errors": [f"Unsupported format: {fmt}"], "warnings": [], "records": 0}
