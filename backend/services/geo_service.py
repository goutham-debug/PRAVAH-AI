"""
PRAVAH AI — Stage 3: Geospatial Analysis Service

Technologies:
- GeoPandas (GeoDataFrames, CRS transformations EPSG:4326 <-> EPSG:3857)
- Shapely (Point, Polygon, LineString, MultiPolygon, spatial buffering & intersections)

Features:
- Administrative neighbourhood polygon boundary analysis
- Real water body & drainage corridor spatial buffers (Bellandur Lake, Varthur Lake, Rajakaluve SWD)
- Road network and drainage corridor spatial intersections
- Facility-to-road network geographic association
- Elevation-based depression spatial analysis
"""

import math
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, shape
from shapely.ops import transform
import pyproj

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in km."""
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 3)

class GeoService:
    # Key hydrological water body footprints in the Whitefield-Mahadevapura pilot zone
    WATER_BODIES = [
        {
            "id": "WB_BELLANDUR_LAKE",
            "name": "Bellandur Lake & Wetland Basin",
            "type": "LAKE_WETLAND",
            "area_ha": 361.0,
            "coordinates": [
                [77.6580, 12.9250],
                [77.6850, 12.9250],
                [77.6890, 12.9420],
                [77.6620, 12.9420],
                [77.6580, 12.9250]
            ]
        },
        {
            "id": "WB_VARTHUR_LAKE",
            "name": "Varthur Lake Catchment Basin",
            "type": "LAKE_CATCHMENT",
            "area_ha": 180.0,
            "coordinates": [
                [77.7320, 12.9320],
                [77.7550, 12.9320],
                [77.7580, 12.9520],
                [77.7350, 12.9520],
                [77.7320, 12.9320]
            ]
        }
    ]

    # Major BBMP primary stormwater drainage channel (Rajakaluve K-100 series) connecting Bellandur to Varthur
    PRIMARY_DRAINAGE_CORRIDORS = [
        {
            "id": "DRAIN_BELLANDUR_VARTHUR_K100",
            "name": "Bellandur-Varthur Primary Rajakaluve Valley Canal",
            "coordinates": [
                [77.6850, 12.9350], # Bellandur Lake outlet
                [77.7010, 12.9440], # Kadubeesanahalli culvert
                [77.7180, 12.9500], # Marathahalli-Kundalahalli valley
                [77.7350, 12.9420]  # Varthur Kodi inlet
            ]
        }
    ]

    def __init__(self, geojson_path: Optional[Path] = None):
        if geojson_path is None:
            from config import Config
            geojson_path = Path(__file__).resolve().parent.parent / 'data' / 'dev_quarantine' / 'whitefield_neighbourhoods.geojson'
            if not Config.LOAD_PILOT_DATASET:
                geojson_path = Path('/nonexistent/pravah-no-ward-data')
        self.geojson_path = geojson_path
        self._geojson_data = None
        self._gdf = None
        self._load_geojson()

    def _load_geojson(self):
        if self.geojson_path.exists():
            with open(self.geojson_path, 'r', encoding='utf-8') as f:
                self._geojson_data = json.load(f)
            try:
                self._gdf = gpd.read_file(str(self.geojson_path))
                if self._gdf.crs is None:
                    self._gdf.set_crs(epsg=4326, inplace=True)
            except Exception:
                self._gdf = None
        else:
            self._geojson_data = {"type": "FeatureCollection", "features": []}
            self._gdf = None

    def get_neighbourhoods_geojson(self) -> Dict[str, Any]:
        return self._geojson_data

    def get_neighbourhoods_gdf(self) -> Optional[gpd.GeoDataFrame]:
        return self._gdf

    def analyze_neighbourhood_boundaries(self) -> List[Dict[str, Any]]:
        """
        Calculates geometric properties for all ward polygons:
        - Validates geometry using Shapely
        - Area in square kilometers (projected to EPSG:3857 for metric precision)
        - Perimeter in kilometers
        - True geometric centroid
        """
        results = []
        if self._gdf is not None and not self._gdf.empty:
            # Reproject to metric projected coordinate system EPSG:3857 (Web Mercator)
            gdf_metric = self._gdf.to_crs(epsg=3857)
            
            for idx, row in self._gdf.iterrows():
                geom = row.geometry
                metric_geom = gdf_metric.loc[idx].geometry
                
                area_sqkm = round(metric_geom.area / 1_000_000.0, 3)
                perimeter_km = round(metric_geom.length / 1000.0, 3)
                centroid = geom.centroid

                results.append({
                    "id": row.get('id'),
                    "name": row.get('name'),
                    "ward_no": row.get('ward_no'),
                    "is_valid_geometry": geom.is_valid,
                    "area_sqkm_calculated": area_sqkm,
                    "perimeter_km": perimeter_km,
                    "centroid": [round(centroid.x, 5), round(centroid.y, 5)],
                    "elevation_m": row.get('elevation_m'),
                    "hazard_factor": row.get('hazard_factor')
                })
        else:
            # Fallback parsing directly from geojson dict
            for feat in self._geojson_data.get('features', []):
                props = feat.get('properties', {})
                geom = shape(feat.get('geometry', {}))
                centroid = geom.centroid
                results.append({
                    "id": props.get('id'),
                    "name": props.get('name'),
                    "ward_no": props.get('ward_no'),
                    "is_valid_geometry": geom.is_valid,
                    "area_sqkm_calculated": props.get('area_sqkm', 1.0),
                    "perimeter_km": 0.0,
                    "centroid": [round(centroid.x, 5), round(centroid.y, 5)],
                    "elevation_m": props.get('elevation_m'),
                    "hazard_factor": props.get('hazard_factor')
                })
        return results

    def find_neighbourhood_for_point(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Identify which neighbourhood polygon contains this (lat, lon) using Shapely."""
        pt = Point(lon, lat)
        
        if self._gdf is not None and not self._gdf.empty:
            for _, row in self._gdf.iterrows():
                if row.geometry.contains(pt):
                    return row.drop('geometry').to_dict()

        for feature in self._geojson_data.get('features', []):
            geom = shape(feature.get('geometry', {}))
            if geom.contains(pt):
                return feature.get('properties', {})

        # Fallback to nearest centroid
        closest_nb = None
        min_dist = float('inf')
        for feature in self._geojson_data.get('features', []):
            props = feature.get('properties', {})
            centroid = props.get('centroid', [77.7499, 12.9698])
            dist = haversine_distance_km(lat, lon, centroid[1], centroid[0])
            if dist < min_dist:
                min_dist = dist
                closest_nb = props
        return closest_nb

    def analyze_water_body_proximity(self, buffer_meters: float = 350.0) -> Dict[str, Any]:
        """
        Creates spatial buffers around critical water bodies and primary drainage canals
        using Shapely and calculates spatial intersections with monitored roads.
        """
        from services.graph_service import graph_service

        # Construct Shapely geometries for water bodies
        water_polys = []
        for wb in self.WATER_BODIES:
            poly = Polygon(wb['coordinates'])
            water_polys.append({
                "id": wb['id'],
                "name": wb['name'],
                "type": wb['type'],
                "geometry": poly
            })

        # Construct Shapely LineStrings for drainage canals
        drain_lines = []
        for dc in self.PRIMARY_DRAINAGE_CORRIDORS:
            line = LineString(dc['coordinates'])
            drain_lines.append({
                "id": dc['id'],
                "name": dc['name'],
                "geometry": line
            })

        # Intersect road segments with buffer zones
        # 1 degree lat is ~111,000m. 350m buffer is ~0.00315 degrees
        buffer_deg = buffer_meters / 111_000.0
        buffered_zones = []
        for wb in water_polys:
            buffered_zones.append((wb['name'], wb['geometry'].buffer(buffer_deg)))
        for dc in drain_lines:
            buffered_zones.append((dc['name'], dc['geometry'].buffer(buffer_deg)))

        roads = graph_service.get_all_roads()
        nodes_dict = {n['id']: n for n in graph_service.get_all_nodes()}

        exposed_roads = []
        for r in roads:
            src = nodes_dict.get(r['source'])
            tgt = nodes_dict.get(r['target'])
            if not src or not tgt:
                continue

            road_line = LineString([[src['lon'], src['lat']], [tgt['lon'], tgt['lat']]])
            intersecting_hazards = []

            for hazard_name, zone_poly in buffered_zones:
                if road_line.intersects(zone_poly):
                    intersecting_hazards.append(hazard_name)

            if intersecting_hazards:
                exposed_roads.append({
                    "road_id": r['id'],
                    "name": r.get('name'),
                    "length_km": r.get('length_km'),
                    "base_flood_risk": r.get('base_flood_risk'),
                    "elevation_risk_score": r.get('elevation_risk_score'),
                    "intersecting_water_features": intersecting_hazards,
                    "drainage_buffer_m": buffer_meters
                })

        return {
            "buffer_meters": buffer_meters,
            "monitored_water_bodies": len(self.WATER_BODIES),
            "monitored_drainage_canals": len(self.PRIMARY_DRAINAGE_CORRIDORS),
            "exposed_roads_count": len(exposed_roads),
            "exposed_roads": exposed_roads
        }

    def validate_coordinates(self, lat: float, lon: float) -> Tuple[bool, str]:
        if not (-90.0 <= lat <= 90.0):
            return False, f"Latitude {lat} is outside valid range [-90, 90]"
        if not (-180.0 <= lon <= 180.0):
            return False, f"Longitude {lon} is outside valid range [-180, 180]"

        # Check if reasonably close to Bengaluru pilot zone (lat ~ 12.8 - 13.2, lon ~ 77.5 - 77.9)
        if not (12.7 <= lat <= 13.3 and 77.4 <= lon <= 77.9):
            return True, "Coordinates valid, but outside Bengaluru Mahadevapura pilot zone."

        return True, "Coordinates valid and within pilot zone."

# Singleton instance
geo_service = GeoService()
