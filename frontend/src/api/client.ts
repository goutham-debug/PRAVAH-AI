import {
  User,
  RouteResponse,
  Neighbourhood,
  Facility,
  Shelter,
  RescueTeam,
  IncidentReport,
  WeatherData,
  ScenarioSimulationResult,
  ScenarioComparisonResponse,
  RoadEdge,
  RoadNode
} from '../types';

const API_BASE = '/api';

export interface SystemStatus {
  success: boolean;
  zone: string;
  counts: { neighbourhoods: number; facilities: number; shelters: number; response_teams: number };
  road_network: { nodes: number; edges: number; status: string };
  unverified_records: number;
  dataset_status: 'UNVERIFIED' | 'UNAVAILABLE' | 'OFFICIAL';
}

export type Classification =
  'OBSERVED' | 'OFFICIAL' | 'FORECAST' | 'MODELLED' | 'UNVERIFIED' | 'STALE' | 'UNAVAILABLE' | 'NOT_ASSESSED';

export interface DataSourceView {
  key: string; provider: string; name: string; dataset_type: string; source_url: string; format: string;
  licence: string | null; coverage: string | null; classification: Classification;
  validation_status: 'NOT_RUN' | 'PASSED' | 'FAILED'; last_status: string | null;
  last_attempt_at: string | null; last_success_at: string | null; retrieved_at: string | null;
  observation_date: string | null; record_count: number | null; ttl_seconds: number; configured: boolean;
  missing_credentials: string[]; last_error: string | null; notes: string | null; connectivity: string;
  probe_detail?: string; validation: { errors?: string[]; warnings?: string[] };
}
export interface DataOpsOverview {
  success: boolean;
  api: { status: string; environment: string; started_at: string; uptime_seconds: number };
  database: { status: string; backend: string; server_version?: string; postgis?: string; latency_ms: number;
              error?: string; development_fallback?: boolean };
  sources: DataSourceView[];
  ingestion: { total_runs: number; failed_runs: number; running: number; last_successful_retrieval: string | null; scheduler: string };
  live_probe: boolean;
}
export interface IngestionRunView {
  id: number; source_key: string; status: string; triggered_by: string | null; started_at: string | null;
  finished_at: string | null; http_status: number | null; attempts: number | null; duration_ms: number | null;
  records: number | null; error: string | null;
}
export interface IngestionEventView { id: number; run_id: number | null; source_key: string; level: string; message: string; at: string }
export interface DatasetInventoryRow {
  id: string; label: string; source_key: string | null; state: Classification; records_in_use: number;
  unverified_records: number; provider_status: string | null; missing_credentials: string[]; note: string;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('pravah_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
    const data = await res.json();
    if (res.status === 401 && endpoint !== '/auth/login') {
      localStorage.removeItem('pravah_token');
      window.dispatchEvent(new Event('pravah:unauthorized'));
    }
    if (res.status === 403 && data?.code === 'PASSWORD_CHANGE_REQUIRED') {
      window.dispatchEvent(new Event('pravah:password-change-required'));
    }
    return data;
  } catch (error) {
    console.warn(`[PRAVAH-API] Fetch error for ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ success: boolean; token: string; user: User; error?: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  logout: () => request<{ success: boolean }>('/auth/logout', { method: 'POST' }),

  getMe: () => request<{ success: boolean; user: User; error?: string }>('/auth/me'),

  changePassword: (current_password: string, new_password: string) =>
    request<{ success: boolean; token?: string; user?: User; error?: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password }),
    }),

  getSystemStatus: () => request<SystemStatus>('/system/status'),

  planJourney: (payload: { start_lat: number; start_lon: number; dest_lat: number; dest_lon: number; avoid_roads?: string[]; algorithm?: string }) =>
    request<RouteResponse>('/roads/route', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getRoadCriticalLinks: () =>
    request<{ success: boolean; critical_link_count: number; critical_links: any[] }>('/roads/critical-links'),

  getRoadNetworkAnalysis: () =>
    request<{ success: boolean; connectivity: any }>('/roads/network-analysis'),

  getFacilityAccessibility: (active_disruptions: string[] = []) =>
    request<{ success: boolean } & any>('/facilities/accessibility', {
      method: 'POST',
      body: JSON.stringify({ active_disruptions }),
    }),

  getBoundaryAnalysis: () =>
    request<{ success: boolean; ward_count: number; boundaries: any[] }>('/geo/boundaries/analysis'),

  getWaterBodyProximity: () =>
    request<{ success: boolean; exposed_roads_count: number; exposed_roads: any[] }>('/geo/water-bodies/proximity'),

  // Incidents
  listIncidents: (status?: string) =>
    request<{ success: boolean; incidents: IncidentReport[]; total_count: number }>(
      `/incidents${status ? `?status=${status}` : ''}`
    ),

  submitIncident: (payload: any) =>
    request<{ success: boolean; tracking_id: string; incident: IncidentReport; error?: string }>('/incidents', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  verifyIncident: (id: number, payload: { status: string; authority_notes?: string; assigned_team_id?: string }) =>
    request<{ success: boolean; incident: IncidentReport }>(`/incidents/${id}/verify`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Geo & Roads
  getNeighbourhoodsGeoJSON: () => request<any>('/geo/neighbourhoods/geojson'),
  
  getNeighbourhoods: () =>
    request<{ success: boolean; neighbourhoods: Neighbourhood[] }>('/geo/neighbourhoods'),

  getFacilities: () =>
    request<{ success: boolean; facilities: Facility[] }>('/geo/facilities'),

  getRoadTopology: () =>
    request<{ success: boolean; nodes: RoadNode[]; edges: RoadEdge[] }>('/roads/topology'),

  // Flood & Simulation
  getFloodFormula: () => request<any>('/flood/formula'),

  assessFlood: (rainfall_scenario: string, active_disruptions: string[]) =>
    request<{ success: boolean; results: any[]; assumptions: any }>('/flood/assess', {
      method: 'POST',
      body: JSON.stringify({ rainfall_scenario, active_disruptions }),
    }),

  simulateScenario: (payload: { rainfall_scenario: string; active_disruptions: string[]; scenario_name?: string }) =>
    request<{ success: boolean; scenario: ScenarioSimulationResult }>('/scenarios/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCandidateDisruptions: () =>
    request<{ success: boolean; candidate_roads: RoadEdge[] }>(
      '/scenarios/candidate-disruptions'
    ),

  compareScenarios: (payload: { rainfall_scenario: string; closed_road_ids: string[]; restored_road_ids?: string[] }) =>
    request<{ success: boolean; error?: string } & ScenarioComparisonResponse>('/scenarios/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Shelters & Rescue
  listShelters: () => request<{ success: boolean; shelters: Shelter[] }>('/shelters'),

  allocateShelters: (active_disruptions: string[]) =>
    request<{ success: boolean } & any>('/shelters/allocate', {
      method: 'POST',
      body: JSON.stringify({ active_disruptions }),
    }),

  listRescueTeams: () => request<{ success: boolean; teams: RescueTeam[] }>('/rescue/teams'),

  coordinateRescue: (active_disruptions: string[]) =>
    request<{ success: boolean } & any>('/rescue/coordinate', {
      method: 'POST',
      body: JSON.stringify({ active_disruptions }),
    }),

  // Weather & Situation Report
  getWeather: (lat?: number, lon?: number) =>
    request<{ success: boolean; weather: WeatherData }>(
      `/weather${lat && lon ? `?lat=${lat}&lon=${lon}` : ''}`
    ),

  generateSitrep: (rainfall_scenario: string, active_disruptions: string[]) =>
    request<{ success: boolean; situation_report: any }>('/sitrep/generate', {
      method: 'POST',
      body: JSON.stringify({ rainfall_scenario, active_disruptions }),
    }),

  // AI Assistant
  queryAI: (payload: { question: string; assessment_id?: string; rainfall_scenario?: string; closed_road_ids?: string[] }) =>
    request<{ success: boolean; answer: string; data_used: string[]; intent: string; classification: string; assessment_id: string; timestamp: string; uncertainty_note: string; error?: string }>('/ai/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // System Execution Monitor
  getMonitorEvents: (limit: number = 50) =>
    request<{ success: boolean; total_returned: number; events: any[] }>(`/monitor/events?limit=${limit}`),

  getMonitorHealth: () =>
    request<{ success: boolean; overall_status: string; api: any; database: any; providers: any; ingestion: any; timestamp: string }>('/monitor/health'),

  // Data Operations (authority-only)
  dataOpsOverview: (live = false) => request<DataOpsOverview>(`/dataops/overview${live ? '?live=1' : ''}`),
  dataOpsDatasets: () => request<{ success: boolean; datasets: DatasetInventoryRow[] }>('/dataops/datasets'),
  dataOpsRuns: (limit = 20) => request<{ success: boolean; runs: IngestionRunView[] }>(`/dataops/runs?limit=${limit}`),
  dataOpsEvents: (afterId = 0) =>
    request<{ success: boolean; events: IngestionEventView[]; running: number; last_id: number }>(`/dataops/events?after_id=${afterId}`),
  dataOpsRefresh: (key: string) =>
    request<{ success: boolean; run_id?: number; error?: string }>(`/dataops/sources/${key}/refresh`, { method: 'POST' }),
};
