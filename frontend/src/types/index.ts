export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';

export type UserRole = 'SYSTEM_ADMIN' | 'DISASTER_OFFICER' | 'OPERATIONS_OFFICER' | 'DATA_MANAGER' | 'READ_ONLY_ANALYST';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  is_active?: boolean;
  must_change_password?: boolean;
  last_login_at?: string | null;
  created_at?: string;
}

export interface Neighbourhood {
  id: string;
  name: string;
  zone: string;
  ward_no?: number;
  population: number;
  area_sqkm: number;
  hazard_factor: number;
  drainage_factor: number;
  elevation_m?: number;
  lake_proximity?: string;
  centroid: [number, number]; // [lon, lat]
  is_pilot: boolean;
  verification_status: string;
}

export interface Facility {
  id: string;
  name: string;
  type: 'HOSPITAL' | 'CLINIC' | 'FIRE_STATION' | 'POLICE_STATION';
  subtype?: string;
  lat: number;
  lon: number;
  nearest_node_id: string;
  capacity_beds: number;
  icu_beds: number;
  has_emergency_ward: boolean;
  phone?: string;
  address?: string;
  neighbourhood_id?: string;
  verification_status: string;
  operational_status: string;
  is_network_accessible?: boolean;
  travel_mins?: number;
  distance_km?: number;
}

export interface Shelter {
  id: string;
  name: string;
  address?: string;
  lat: number;
  lon: number;
  nearest_node_id: string;
  total_capacity: number;
  current_occupancy: number;
  available_capacity: number;
  status: string;
  amenities: string[];
  elevation_m?: number;
  neighbourhood_id?: string;
  contact_officer?: string;
  phone?: string;
  distance_km?: number;
  estimated_walk_mins?: number;
  estimated_drive_mins?: number;
}

export interface RescueTeam {
  id: string;
  name: string;
  type: 'BOAT_RESCUE' | 'DEWATERING_PUMP' | 'MEDICAL_EVAC' | 'SEARCH_AND_RESCUE';
  capabilities: string[];
  personnel_count: number;
  boats_count: number;
  pumps_count: number;
  ambulances_count: number;
  status: 'AVAILABLE' | 'DISPATCHED' | 'MAINTENANCE';
  current_assigned_incident_id?: string | null;
  base_lat: number;
  base_lon: number;
  nearest_node_id: string;
  contact_commander?: string;
  phone?: string;
}

export interface IncidentReport {
  id: number;
  tracking_id: string;
  citizen_name: string;
  phone: string;
  lat: number;
  lon: number;
  neighbourhood_id?: string;
  nearest_node_id?: string;
  incident_type: 'WATERLOGGING' | 'ROAD_BLOCK' | 'STRANDED_PERSONS' | 'DRAIN_OVERFLOW' | 'TREE_FALL';
  severity: RiskLevel;
  description: string;
  photo_url?: string;
  status: 'PENDING_VERIFICATION' | 'VERIFIED' | 'RESOLVED' | 'REJECTED';
  authority_notes?: string;
  assigned_team_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RiskAssessment {
  risk_score: number;
  classification: RiskLevel;
  color: string;
  advisory: string;
  formula: string;
  components: {
    P: { label: string; value: number; weight: number; weighted_contribution: number; pct_of_total: number };
    E: { label: string; value: number; weight: number; weighted_contribution: number; pct_of_total: number };
    H: { label: string; value: number; weight: number; weighted_contribution: number; pct_of_total: number };
    D: { label: string; value: number; weight: number; weighted_contribution: number; pct_of_total: number };
  };
  limitations_notice: string;
}

export interface RoadEdge {
  id: string;
  name: string;
  source: string;
  target: string;
  length_km: number;
  road_type: string;
  speed_limit_kmh: number;
  base_flood_risk: string;
  elevation_risk_score: number;
  is_critical: boolean;
  one_way: boolean;
}

export interface RoadNode {
  id: string;
  name: string;
  lat: number;
  lon: number;
  elevation: number;
  neighbourhood_id: string;
}

export interface RouteResponse {
  success: boolean;
  error?: string;
  primary_route?: {
    total_distance_km: number;
    travel_time_mins: number;
    node_sequence: string[];
    road_names: string[];
    coordinates: [number, number][]; // [lon, lat]
    turn_by_turn: string[];
  };
  alternative_route?: {
    total_distance_km: number;
    travel_time_mins: number;
    node_sequence: string[];
    road_names: string[];
    coordinates: [number, number][];
    turn_by_turn: string[];
  } | null;
  algorithm_used?: string;
  closed_roads_active?: string[];
}

export interface WeatherData {
  source: string;
  status: string;
  location: string;
  latitude: number;
  longitude: number;
  temperature_c: number;
  rainfall_current_mm: number;
  wind_speed_kmh: number;
  humidity_pct: number;
  weather_description: string;
  hourly_forecast: { time: string; precipitation_mm: number; temperature_c: number }[];
  last_updated: string;
  disclaimer: string;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'URGENT' | 'CRITICAL';
  target_zone: string;
  created_at?: string;
}

export interface ScenarioSimulationResult {
  scenario_name: string;
  rainfall_scenario: string;
  rainfall_mm: number;
  active_disruptions: string[];
  total_exposed_population: number;
  connectivity: {
    total_nodes: number;
    total_edges: number;
    active_edges: number;
    edges_disrupted: number;
    num_connected_components: number;
    primary_component_size: number;
    isolated_node_count: number;
    isolated_neighbourhood_ids: string[];
    network_integrity_pct: number;
  };
  neighbourhood_assessment: (Neighbourhood & RiskAssessment & { exposed_population: number })[];
  facility_accessibility: {
    total_facilities: number;
    reachable_facilities: number;
    unreachable_facilities: number;
    overall_accessibility_pct: number;
    facility_status: Facility[];
    wards_with_zero_trauma_access: { neighbourhood_id: string; name: string; reason: string }[];
  };
  shelter_allocation: {
    total_evacuation_demand: number;
    total_allocated_population: number;
    total_unmet_demand: number;
    total_unreachable_demand: number;
    allocation_fulfillment_pct: number;
    total_shelter_capacity: number;
    remaining_shelter_capacity: number;
    shelter_utilization_pct: number;
    assignments: {
      neighbourhood_id: string;
      neighbourhood_name: string;
      shelter_id: string;
      shelter_name: string;
      allocated_population: number;
      travel_distance_km: number;
      travel_time_mins: number;
    }[];
    unmet_records: { neighbourhood_id: string; name: string; unmet_count: number; reason: string }[];
  };
  rescue_coordination: {
    total_incidents_evaluated: number;
    dispatched_count: number;
    unassigned_count: number;
    coverage_rate_pct: number;
    assignments: {
      incident_id: number;
      tracking_id: string;
      incident_type: string;
      severity: string;
      assigned_team_id: string;
      assigned_team_name: string;
      team_type: string;
      estimated_arrival_mins: number;
      response_distance_km: number;
      contact_commander?: string;
      phone?: string;
    }[];
    unassigned_incidents: { incident_id: number; tracking_id: string; description: string; reason: string }[];
  };
  situation_report: {
    report_id: string;
    scenario_name: string;
    timestamp: string;
    executive_summary: string;
    markdown_content: string;
    metrics: Record<string, any>;
    recommendations: { priority: string; action: string; target_zone: string; expected_impact: string }[];
  };
}

export interface ScenarioComparisonResponse {
  disruptions_applied: string[];
  roads_restored: string[];
  label: 'MODELLED';
  stages: {
    baseline: ScenarioSimulationResult;
    disrupted: ScenarioSimulationResult;
    restored: ScenarioSimulationResult;
  };
  comparison_matrix: {
    network_integrity_pct: { baseline: number; disrupted: number; restored: number; improvement_over_disrupted: number };
    isolated_wards_count: { baseline: number; disrupted: number; restored: number; difference: number };
    unreachable_facilities: { baseline: number; disrupted: number; restored: number; recovered_facilities: number };
    wards_losing_trauma_access: { baseline: number; disrupted: number; restored: number; reconnected_wards: number };
    unmet_shelter_demand: { baseline: number; disrupted: number; restored: number; demand_relief: number };
    dispatched_rescue_teams: { baseline: number; disrupted: number; restored: number };
  };
}
