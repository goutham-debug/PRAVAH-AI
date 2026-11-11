import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Facility, Shelter, RescueTeam, IncidentReport, RoadEdge, RoadNode } from '../../types';
import { Layers, Eye, EyeOff, Navigation, Maximize2, RotateCcw } from 'lucide-react';

interface PravahMapProps {
  neighbourhoodsGeoJSON?: any;
  riskAssessments?: Record<string, { risk_score: number; classification: string }>;
  roads?: RoadEdge[];
  nodes?: RoadNode[];
  closedRoadIds?: string[];
  facilities?: Facility[];
  shelters?: Shelter[];
  rescueTeams?: RescueTeam[];
  incidents?: IncidentReport[];
  routeCoordinates?: [number, number][]; // [lon, lat]
  alternativeRouteCoordinates?: [number, number][];
  selectedNeighbourhoodId?: string | null;
  onSelectNeighbourhood?: (id: string) => void;
  height?: string;
  interactive?: boolean;
}

export const PravahMap: React.FC<PravahMapProps> = ({
  neighbourhoodsGeoJSON,
  riskAssessments = {},
  roads = [],
  nodes = [],
  closedRoadIds = [],
  facilities = [],
  shelters = [],
  rescueTeams = [],
  incidents = [],
  routeCoordinates,
  alternativeRouteCoordinates,
  selectedNeighbourhoodId,
  onSelectNeighbourhood,
  height = '560px',
  interactive = true,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // Layer visibility toggles
  const [showWards, setShowWards] = useState(true);
  const [showRoads, setShowRoads] = useState(true);
  const [showFacilities, setShowFacilities] = useState(true);
  const [showShelters, setShowShelters] = useState(true);
  const [showRescues, setShowRescues] = useState(true);
  const [showIncidents, setShowIncidents] = useState(true);
  const [layerPanelOpen, setLayerPanelOpen] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Use free public OpenStreetMap vector tiles via MapTiler or Carto style
    const mapStyle = {
      version: 8,
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
          ],
          tileSize: 256,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }
      },
      layers: [
        {
          id: 'osm-layer',
          type: 'raster',
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19
        }
      ]
    };

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: mapStyle as any,
      center: [77.7250, 12.9650], // Centered between Marathahalli and Whitefield
      zoom: 12.2,
      attributionControl: { compact: true },
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.current.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: 'metric' }), 'bottom-left');

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update GeoJSON Layers & Road Layers
  useEffect(() => {
    if (!map.current) return;
    const m = map.current;

    const handleLoad = () => {
      // 1. Add/Update Neighbourhood Polygon Layer
      if (neighbourhoodsGeoJSON && neighbourhoodsGeoJSON.features) {
        // Enrich features with current risk classification for choropleth styling
        const enrichedGeoJSON = {
          ...neighbourhoodsGeoJSON,
          features: neighbourhoodsGeoJSON.features.map((feat: any) => {
            const nbId = feat.properties?.id;
            const risk = riskAssessments[nbId] || { risk_score: 45, classification: 'MODERATE' };
            let fillColor = '#10B981'; // LOW (green)
            if (risk.classification === 'SEVERE') fillColor = '#D95757'; // red
            else if (risk.classification === 'HIGH') fillColor = '#EF8D42'; // orange
            else if (risk.classification === 'MODERATE') fillColor = '#F1B85B'; // yellow

            return {
              ...feat,
              properties: {
                ...feat.properties,
                risk_score: risk.risk_score,
                classification: risk.classification,
                fill_color: fillColor
              }
            };
          })
        };

        if (m.getSource('wards-source')) {
          (m.getSource('wards-source') as maplibregl.GeoJSONSource).setData(enrichedGeoJSON);
        } else {
          m.addSource('wards-source', {
            type: 'geojson',
            data: enrichedGeoJSON
          });

          // Fill layer
          m.addLayer({
            id: 'wards-fill',
            type: 'fill',
            source: 'wards-source',
            paint: {
              'fill-color': ['get', 'fill_color'],
              'fill-opacity': 0.35
            }
          });

          // Boundary line layer
          m.addLayer({
            id: 'wards-outline',
            type: 'line',
            source: 'wards-source',
            paint: {
              'line-color': '#105D63',
              'line-width': 2,
              'line-dasharray': [2, 1]
            }
          });

          // Ward click interaction
          m.on('click', 'wards-fill', (e) => {
            if (e.features && e.features[0]) {
              const props = e.features[0].properties;
              if (onSelectNeighbourhood && props.id) {
                onSelectNeighbourhood(props.id);
              }
              new maplibregl.Popup()
                .setLngLat(e.lngLat)
                .setHTML(`
                  <div class="p-1">
                    <h3 class="font-bold text-sm text-[#183447]">${props.name}</h3>
                    <p class="text-xs text-gray-600">Ward No: ${props.ward_no || 'N/A'}</p>
                    <p class="text-xs mt-1"><strong>Risk Index:</strong> ${props.risk_score || 'N/A'} (${props.classification})</p>
                    <p class="text-xs"><strong>Population:</strong> ${Number(props.population).toLocaleString()}</p>
                    <p class="text-[11px] text-[#167F83] mt-1"><em>${props.lake_proximity || ''}</em></p>
                  </div>
                `)
                .addTo(m);
            }
          });

          m.on('mouseenter', 'wards-fill', () => {
            m.getCanvas().style.cursor = 'pointer';
          });
          m.on('mouseleave', 'wards-fill', () => {
            m.getCanvas().style.cursor = '';
          });
        }
      }

      // 2. Add Road Network Layer if nodes & edges exist
      if (roads.length > 0 && nodes.length > 0) {
        const nodeMap = new Map(nodes.map(n => [n.id, n]));
        const roadFeatures = roads.map(r => {
          const src = nodeMap.get(r.source);
          const tgt = nodeMap.get(r.target);
          const isClosed = closedRoadIds.includes(r.id);
          return {
            type: 'Feature',
            properties: {
              id: r.id,
              name: r.name,
              isClosed: isClosed,
              isCritical: r.is_critical,
              color: isClosed ? '#991B1B' : '#167F83',
              width: isClosed ? 5 : (r.is_critical ? 3.5 : 2.5)
            },
            geometry: {
              type: 'LineString',
              coordinates: src && tgt ? [[src.lon, src.lat], [tgt.lon, tgt.lat]] : []
            }
          };
        }).filter(f => f.geometry.coordinates.length > 0);

        const roadGeoJSON = { type: 'FeatureCollection', features: roadFeatures };

        if (m.getSource('roads-source')) {
          (m.getSource('roads-source') as maplibregl.GeoJSONSource).setData(roadGeoJSON as any);
        } else {
          m.addSource('roads-source', {
            type: 'geojson',
            data: roadGeoJSON as any
          });

          m.addLayer({
            id: 'roads-line',
            type: 'line',
            source: 'roads-source',
            layout: {
              'line-cap': 'round',
              'line-join': 'round'
            },
            paint: {
              'line-color': ['get', 'color'],
              'line-width': ['get', 'width'],
              'line-opacity': 0.85
            }
          });

          m.on('click', 'roads-line', (e) => {
            if (e.features && e.features[0]) {
              const props = e.features[0].properties;
              new maplibregl.Popup()
                .setLngLat(e.lngLat)
                .setHTML(`
                  <div class="p-1">
                    <h3 class="font-bold text-xs text-[#183447]">${props.name}</h3>
                    <p class="text-xs ${props.isClosed ? 'text-red-600 font-bold' : 'text-emerald-600'}">
                      Status: ${props.isClosed ? '🔴 DISRUPTED / CLOSED' : '🟢 OPEN'}
                    </p>
                    <p class="text-[11px] text-gray-500">ID: ${props.id}</p>
                  </div>
                `)
                .addTo(m);
            }
          });
        }
      }

      // 3. Add Evacuation Primary & Alternative Route Lines
      if (routeCoordinates && routeCoordinates.length > 1) {
        const routeGeoJSON = {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: routeCoordinates
          }
        };

        if (m.getSource('evac-route-source')) {
          (m.getSource('evac-route-source') as maplibregl.GeoJSONSource).setData(routeGeoJSON as any);
        } else {
          m.addSource('evac-route-source', {
            type: 'geojson',
            data: routeGeoJSON as any
          });

          m.addLayer({
            id: 'evac-route-line',
            type: 'line',
            source: 'evac-route-source',
            layout: {
              'line-join': 'round',
              'line-cap': 'round'
            },
            paint: {
              'line-color': '#2563EB', // Blue primary route
              'line-width': 5,
              'line-opacity': 0.9
            }
          });
        }
      } else {
        if (m.getLayer('evac-route-line')) m.removeLayer('evac-route-line');
        if (m.getSource('evac-route-source')) m.removeSource('evac-route-source');
      }

      if (alternativeRouteCoordinates && alternativeRouteCoordinates.length > 1) {
        const altGeoJSON = {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: alternativeRouteCoordinates
          }
        };

        if (m.getSource('alt-route-source')) {
          (m.getSource('alt-route-source') as maplibregl.GeoJSONSource).setData(altGeoJSON as any);
        } else {
          m.addSource('alt-route-source', {
            type: 'geojson',
            data: altGeoJSON as any
          });

          m.addLayer({
            id: 'alt-route-line',
            type: 'line',
            source: 'alt-route-source',
            layout: {
              'line-join': 'round',
              'line-cap': 'round'
            },
            paint: {
              'line-color': '#9333EA', // Purple dashed alternative route
              'line-width': 4,
              'line-dasharray': [2, 2],
              'line-opacity': 0.85
            }
          });
        }
      } else {
        if (m.getLayer('alt-route-line')) m.removeLayer('alt-route-line');
        if (m.getSource('alt-route-source')) m.removeSource('alt-route-source');
      }
    };

    if (m.isStyleLoaded()) {
      handleLoad();
    } else {
      m.once('load', handleLoad);
    }
  }, [neighbourhoodsGeoJSON, riskAssessments, roads, nodes, closedRoadIds, routeCoordinates, alternativeRouteCoordinates]);

  // Update Markers (Hospitals, Shelters, Rescue Teams, Incidents)
  useEffect(() => {
    if (!map.current) return;
    const m = map.current;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // 1. Hospital Markers (Blue)
    if (showFacilities) {
      facilities.forEach(fac => {
        const el = document.createElement('div');
        el.className = 'w-6 h-6 rounded-full bg-blue-600 border-2 border-white shadow-md flex items-center justify-center text-white text-[10px] font-bold cursor-pointer hover:scale-125 transition-transform';
        el.innerHTML = '+';
        el.title = fac.name;

        const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
          <div class="p-1">
            <h4 class="font-bold text-xs text-blue-900">${fac.name}</h4>
            <p class="text-[11px] text-gray-600 font-medium">${fac.subtype || fac.type}</p>
            <p class="text-[11px] mt-1">Beds: <strong>${fac.capacity_beds}</strong> | ICU: <strong>${fac.icu_beds}</strong></p>
            <p class="text-[10px] text-gray-500 mt-0.5">${fac.address || ''}</p>
            <p class="text-[11px] mt-1 font-semibold ${fac.is_network_accessible === false ? 'text-red-600' : 'text-emerald-600'}">
              ${fac.is_network_accessible === false ? '⚠️ Road Access Blocked' : '✅ Road Connected'}
            </p>
          </div>
        `);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([fac.lon, fac.lat])
          .setPopup(popup)
          .addTo(m);

        markersRef.current.push(marker);
      });
    }

    // 2. Shelter Markers (Green)
    if (showShelters) {
      shelters.forEach(sh => {
        const el = document.createElement('div');
        el.className = 'w-6 h-6 rounded-full bg-emerald-600 border-2 border-white shadow-md flex items-center justify-center text-white text-[10px] font-bold cursor-pointer hover:scale-125 transition-transform';
        el.innerHTML = '⌂';
        el.title = sh.name;

        const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
          <div class="p-1">
            <h4 class="font-bold text-xs text-emerald-900">${sh.name}</h4>
            <p class="text-[11px] mt-1">Total Capacity: <strong>${sh.total_capacity}</strong> persons</p>
            <p class="text-[11px]">Available Space: <strong>${sh.available_capacity || sh.total_capacity}</strong></p>
            <p class="text-[10px] text-gray-600 mt-1">Officer: ${sh.contact_officer || 'BBMP Ward Desk'}</p>
            <div class="flex flex-wrap gap-1 mt-1.5">
              ${(sh.amenities || []).map(a => `<span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">${a}</span>`).join('')}
            </div>
          </div>
        `);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([sh.lon, sh.lat])
          .setPopup(popup)
          .addTo(m);

        markersRef.current.push(marker);
      });
    }

    // 3. Rescue Team Markers (Purple)
    if (showRescues) {
      rescueTeams.forEach(team => {
        const el = document.createElement('div');
        el.className = 'w-6 h-6 rounded-md bg-purple-700 border-2 border-white shadow-md flex items-center justify-center text-white text-[10px] font-bold cursor-pointer hover:scale-125 transition-transform';
        el.innerHTML = '▲';
        el.title = team.name;

        const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
          <div class="p-1">
            <h4 class="font-bold text-xs text-purple-900">${team.name}</h4>
            <p class="text-[11px] text-purple-700 font-semibold">${team.type}</p>
            <p class="text-[11px] mt-1">Status: <strong class="${team.status === 'AVAILABLE' ? 'text-emerald-600' : 'text-amber-600'}">${team.status}</strong></p>
            <p class="text-[11px]">Personnel: <strong>${team.personnel_count}</strong> | Boats: <strong>${team.boats_count}</strong> | Pumps: <strong>${team.pumps_count}</strong></p>
            <p class="text-[10px] text-gray-500 mt-1">Commander: ${team.contact_commander || 'Duty Officer'}</p>
          </div>
        `);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([team.base_lon, team.base_lat])
          .setPopup(popup)
          .addTo(m);

        markersRef.current.push(marker);
      });
    }

    // 4. Incident Markers (Red/Orange Pin)
    if (showIncidents) {
      incidents.forEach(inc => {
        const el = document.createElement('div');
        const isSevere = inc.severity === 'SEVERE';
        el.className = `w-5 h-5 rounded-full ${isSevere ? 'bg-rose-600 animate-ping' : 'bg-orange-500'} border border-white shadow-md cursor-pointer`;
        el.title = inc.incident_type;

        const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
          <div class="p-1">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full ${isSevere ? 'bg-rose-600' : 'bg-orange-500'}"></span>
              <h4 class="font-bold text-xs text-gray-900">${inc.incident_type}</h4>
            </div>
            <p class="text-[11px] font-semibold text-rose-700 mt-0.5">Severity: ${inc.severity}</p>
            <p class="text-xs text-gray-700 mt-1">"${inc.description}"</p>
            <p class="text-[10px] text-gray-500 mt-1">Report ID: ${inc.tracking_id} | Status: <strong>${inc.status}</strong></p>
          </div>
        `);

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([inc.lon, inc.lat])
          .setPopup(popup)
          .addTo(m);

        markersRef.current.push(marker);
      });
    }
  }, [facilities, shelters, rescueTeams, incidents, showFacilities, showShelters, showRescues, showIncidents]);

  const resetView = () => {
    map.current?.flyTo({
      center: [77.7250, 12.9650],
      zoom: 12.2,
      essential: true
    });
  };

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-pravah-teal/20 shadow-md" style={{ height }}>
      {/* Map Canvas */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* Floating Control Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <button
          onClick={() => setLayerPanelOpen(!layerPanelOpen)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/95 backdrop-blur border border-pravah-teal/30 shadow-md text-xs font-bold text-pravah-navy hover:bg-pravah-aqua transition-colors"
        >
          <Layers className="w-3.5 h-3.5 text-pravah-teal" />
          Layers
        </button>
        <button
          onClick={resetView}
          className="p-2 rounded-xl bg-white/95 backdrop-blur border border-pravah-teal/30 shadow-md text-pravah-navy hover:bg-pravah-aqua transition-colors"
          title="Reset to Whitefield-Mahadevapura View"
        >
          <RotateCcw className="w-3.5 h-3.5 text-pravah-teal" />
        </button>
      </div>

      {/* Floating Layer Toggle Menu */}
      {layerPanelOpen && (
        <div className="absolute top-12 left-3 z-20 bg-white/95 backdrop-blur border border-pravah-teal/20 rounded-xl p-3 shadow-xl text-xs space-y-2 min-w-[200px]">
          <div className="font-bold text-pravah-navy pb-1 border-b border-pravah-pale flex items-center justify-between">
            <span>Layer Visibility</span>
            <button onClick={() => setLayerPanelOpen(false)} className="text-gray-400 hover:text-gray-700">✕</button>
          </div>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded bg-amber-400"></span>
              Neighbourhood Risk Wards
            </span>
            <input
              type="checkbox"
              checked={showWards}
              onChange={(e) => setShowWards(e.target.checked)}
              className="accent-pravah-teal"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded bg-blue-600"></span>
              Hospitals
            </span>
            <input
              type="checkbox"
              checked={showFacilities}
              onChange={(e) => setShowFacilities(e.target.checked)}
              className="accent-pravah-teal"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded bg-emerald-600"></span>
              Relief Shelters
            </span>
            <input
              type="checkbox"
              checked={showShelters}
              onChange={(e) => setShowShelters(e.target.checked)}
              className="accent-pravah-teal"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded bg-purple-600"></span>
              Rescue Teams
            </span>
            <input
              type="checkbox"
              checked={showRescues}
              onChange={(e) => setShowRescues(e.target.checked)}
              className="accent-pravah-teal"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded bg-rose-600"></span>
              Incident reports
            </span>
            <input
              type="checkbox"
              checked={showIncidents}
              onChange={(e) => setShowIncidents(e.target.checked)}
              className="accent-pravah-teal"
            />
          </label>
        </div>
      )}
    </div>
  );
};
