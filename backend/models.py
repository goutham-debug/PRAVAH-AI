from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(40), nullable=False, default='READ_ONLY_ANALYST')
    phone = Column(String(30), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False)
    failed_logins = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident_reports = relationship("IncidentReport", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "phone": self.phone,
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LoginAudit(Base):
    __tablename__ = 'login_audit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    email = Column(String(254), nullable=False)
    event = Column(String(40), nullable=False)  # LOGIN_SUCCESS, LOGIN_FAILED, LOGIN_LOCKED, LOGOUT, PASSWORD_CHANGED, USER_CREATED, USER_UPDATED, PASSWORD_RESET
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    detail = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "email": self.email,
            "event": self.event, "ip_address": self.ip_address, "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Neighbourhood(Base):
    __tablename__ = 'neighbourhoods'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(120), nullable=False)
    zone = Column(String(80), nullable=False, default='Mahadevapura')
    ward_no = Column(Integer, nullable=True)
    population = Column(Integer, nullable=False, default=0)
    area_sqkm = Column(Float, nullable=False, default=1.0)
    hazard_factor = Column(Float, nullable=False, default=50.0) # 0 - 100
    drainage_factor = Column(Float, nullable=False, default=50.0) # 0 - 100
    elevation_m = Column(Float, nullable=True)
    lake_proximity = Column(String(255), nullable=True)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    is_pilot = Column(Boolean, default=True)
    verification_status = Column(String(80), default='UNVERIFIED')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "zone": self.zone,
            "ward_no": self.ward_no,
            "population": self.population,
            "area_sqkm": self.area_sqkm,
            "hazard_factor": self.hazard_factor,
            "drainage_factor": self.drainage_factor,
            "elevation_m": self.elevation_m,
            "lake_proximity": self.lake_proximity,
            "centroid": [self.centroid_lon, self.centroid_lat],
            "is_pilot": self.is_pilot,
            "verification_status": self.verification_status
        }

class Facility(Base):
    __tablename__ = 'facilities'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    type = Column(String(40), nullable=False)  # 'HOSPITAL', 'CLINIC', 'FIRE_STATION', 'POLICE_STATION'
    subtype = Column(String(60), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    nearest_node_id = Column(String(50), nullable=False)
    capacity_beds = Column(Integer, default=0)
    icu_beds = Column(Integer, default=0)
    has_emergency_ward = Column(Boolean, default=False)
    phone = Column(String(40), nullable=True)
    address = Column(String(255), nullable=True)
    neighbourhood_id = Column(String(50), nullable=True)
    verification_status = Column(String(80), default='UNVERIFIED')
    operational_status = Column(String(40), default='OPERATIONAL') # 'OPERATIONAL', 'DEGRADED', 'INUNDATED'

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "subtype": self.subtype,
            "lat": self.lat,
            "lon": self.lon,
            "nearest_node_id": self.nearest_node_id,
            "capacity_beds": self.capacity_beds,
            "icu_beds": self.icu_beds,
            "has_emergency_ward": self.has_emergency_ward,
            "phone": self.phone,
            "address": self.address,
            "neighbourhood_id": self.neighbourhood_id,
            "verification_status": self.verification_status,
            "operational_status": self.operational_status
        }

class Shelter(Base):
    __tablename__ = 'shelters'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    nearest_node_id = Column(String(50), nullable=False)
    total_capacity = Column(Integer, nullable=False, default=500)
    current_occupancy = Column(Integer, nullable=False, default=0)
    status = Column(String(40), default='OPERATIONAL') # 'OPERATIONAL', 'FULL', 'UNAVAILABLE'
    amenities_json = Column(Text, default='[]')
    elevation_m = Column(Float, nullable=True)
    neighbourhood_id = Column(String(50), nullable=True)
    contact_officer = Column(String(120), nullable=True)
    phone = Column(String(40), nullable=True)
    verification_status = Column(String(80), default='UNVERIFIED')

    def to_dict(self):
        amenities = []
        try:
            amenities = json.loads(self.amenities_json) if self.amenities_json else []
        except Exception:
            amenities = []
            
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lon": self.lon,
            "nearest_node_id": self.nearest_node_id,
            "total_capacity": self.total_capacity,
            "current_occupancy": self.current_occupancy,
            "available_capacity": max(0, self.total_capacity - self.current_occupancy),
            "status": self.status,
            "amenities": amenities,
            "elevation_m": self.elevation_m,
            "neighbourhood_id": self.neighbourhood_id,
            "contact_officer": self.contact_officer,
            "phone": self.phone,
            "verification_status": self.verification_status
        }

class RescueTeam(Base):
    __tablename__ = 'rescue_teams'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    type = Column(String(50), nullable=False) # 'BOAT_RESCUE', 'DEWATERING_PUMP', 'MEDICAL_EVAC', 'SEARCH_AND_RESCUE'
    capabilities_json = Column(Text, default='[]')
    personnel_count = Column(Integer, default=5)
    boats_count = Column(Integer, default=0)
    pumps_count = Column(Integer, default=0)
    ambulances_count = Column(Integer, default=0)
    status = Column(String(40), default='AVAILABLE') # 'AVAILABLE', 'DISPATCHED', 'MAINTENANCE'
    current_assigned_incident_id = Column(String(50), nullable=True)
    base_lat = Column(Float, nullable=False)
    base_lon = Column(Float, nullable=False)
    nearest_node_id = Column(String(50), nullable=False)
    contact_commander = Column(String(120), nullable=True)
    phone = Column(String(40), nullable=True)
    verification_status = Column(String(80), default='UNVERIFIED')

    def to_dict(self):
        caps = []
        try:
            caps = json.loads(self.capabilities_json) if self.capabilities_json else []
        except Exception:
            caps = []
            
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "capabilities": caps,
            "personnel_count": self.personnel_count,
            "boats_count": self.boats_count,
            "pumps_count": self.pumps_count,
            "ambulances_count": self.ambulances_count,
            "status": self.status,
            "current_assigned_incident_id": self.current_assigned_incident_id,
            "base_lat": self.base_lat,
            "base_lon": self.base_lon,
            "nearest_node_id": self.nearest_node_id,
            "contact_commander": self.contact_commander,
            "phone": self.phone,
            "verification_status": self.verification_status
        }

class IncidentReport(Base):
    __tablename__ = 'incident_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_id = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    citizen_name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    neighbourhood_id = Column(String(50), nullable=True)
    nearest_node_id = Column(String(50), nullable=True)
    incident_type = Column(String(50), nullable=False) # 'WATERLOGGING', 'ROAD_BLOCK', 'STRANDED_PERSONS', 'DRAIN_OVERFLOW', 'TREE_FALL'
    severity = Column(String(20), nullable=False, default='MODERATE') # 'LOW', 'MODERATE', 'HIGH', 'SEVERE'
    description = Column(Text, nullable=False)
    photo_url = Column(String(255), nullable=True)
    status = Column(String(40), default='PENDING_VERIFICATION') # 'PENDING_VERIFICATION', 'VERIFIED', 'RESOLVED', 'REJECTED'
    authority_notes = Column(Text, nullable=True)
    assigned_team_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="incident_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "tracking_id": self.tracking_id,
            "user_id": self.user_id,
            "citizen_name": self.citizen_name,
            "phone": self.phone,
            "lat": self.lat,
            "lon": self.lon,
            "neighbourhood_id": self.neighbourhood_id,
            "nearest_node_id": self.nearest_node_id,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "photo_url": self.photo_url,
            "status": self.status,
            "authority_notes": self.authority_notes,
            "assigned_team_id": self.assigned_team_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Scenario(Base):
    __tablename__ = 'scenarios'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    rainfall_scenario = Column(String(40), nullable=False, default='HEAVY') # 'NORMAL', 'HEAVY', 'EXTREME', 'CLOUDBURST'
    rainfall_mm = Column(Float, nullable=False, default=85.0)
    active_disruptions_json = Column(Text, default='[]')
    status = Column(String(40), default='COMPLETED')
    run_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        disruptions = []
        try:
            disruptions = json.loads(self.active_disruptions_json) if self.active_disruptions_json else []
        except Exception:
            disruptions = []
            
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rainfall_scenario": self.rainfall_scenario,
            "rainfall_mm": self.rainfall_mm,
            "active_disruptions": disruptions,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class SituationReport(Base):
    __tablename__ = 'situation_reports'
    
    id = Column(String(50), primary_key=True)
    scenario_id = Column(String(50), nullable=False)
    report_title = Column(String(200), nullable=False)
    executive_summary = Column(Text, nullable=False)
    metrics_json = Column(Text, default='{}')
    recommendations_json = Column(Text, default='[]')
    generated_by = Column(String(100), default='PRAVAH AI Intelligence Engine')
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        metrics = {}
        recommendations = []
        try:
            metrics = json.loads(self.metrics_json) if self.metrics_json else {}
            recommendations = json.loads(self.recommendations_json) if self.recommendations_json else []
        except Exception:
            pass
            
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "report_title": self.report_title,
            "executive_summary": self.executive_summary,
            "metrics": metrics,
            "recommendations": recommendations,
            "generated_by": self.generated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }



class DataSource(Base):
    """Central data registry: one row per external/ingested dataset (provenance record)."""
    __tablename__ = 'data_sources'

    key = Column(String(60), primary_key=True)
    provider = Column(String(150), nullable=False)
    name = Column(String(200), nullable=False)
    dataset_type = Column(String(80), nullable=False)
    source_url = Column(String(500), nullable=False)
    data_format = Column(String(20), nullable=False, default='json')
    licence = Column(String(300), nullable=True)
    coverage = Column(String(300), nullable=True)
    classification = Column(String(20), nullable=False, default='NOT_ASSESSED')  # of last successful data
    validation_status = Column(String(20), nullable=False, default='NOT_RUN')    # NOT_RUN | PASSED | FAILED
    last_status = Column(String(20), nullable=True)           # OK | FAILED | INVALID | NOT_CONFIGURED
    last_attempt_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, nullable=True)            # retrieval time of the last successful fetch
    observation_date = Column(String(60), nullable=True)      # observation/reference time reported by provider
    record_count = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    storage_path = Column(String(500), nullable=True)
    ttl_seconds = Column(Integer, nullable=False, default=3600)
    configured = Column(Boolean, nullable=False, default=False)
    missing_credentials = Column(String(300), nullable=True)
    last_error = Column(String(500), nullable=True)
    validation_json = Column(Text, default='{}')
    notes = Column(String(500), nullable=True)


class IngestionRun(Base):
    __tablename__ = 'ingestion_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_key = Column(String(60), ForeignKey('data_sources.key'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='RUNNING')  # RUNNING | OK | FAILED | INVALID | NOT_CONFIGURED
    triggered_by = Column(String(80), nullable=True)                # user email or 'scheduler' / 'weather-panel'
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)
    http_status = Column(Integer, nullable=True)
    attempts = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    records = Column(Integer, nullable=True)
    error = Column(String(500), nullable=True)
    validation_json = Column(Text, default='{}')


class IngestionEvent(Base):
    """Real execution events written by the backend while a run executes (never synthesised)."""
    __tablename__ = 'ingestion_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey('ingestion_runs.id'), nullable=True, index=True)
    source_key = Column(String(60), nullable=False, index=True)
    level = Column(String(10), nullable=False, default='INFO')  # INFO | WARN | ERROR
    message = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
