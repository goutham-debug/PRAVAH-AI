import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session

from config import Config
from models import Base, User, Neighbourhood, Facility, Shelter, RescueTeam
from security import hash_password, validate_password_strength

_url = Config.SQLALCHEMY_DATABASE_URI
if _url.startswith('sqlite'):
    engine = create_engine(_url, echo=False, connect_args={"check_same_thread": False})
else:
    # Supabase Postgres: TLS required; pre-ping handles pooler-dropped connections.
    engine = create_engine(
        _url, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=5, pool_recycle=1800,
        connect_args={"sslmode": "require"} if "sslmode" not in _url else {},
    )
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

DATA_DIR = Path(__file__).resolve().parent / 'data' / 'dev_quarantine'


def _bootstrap_admin(session):
    """Create the first System Administrator from environment variables.

    Runs only while no SYSTEM_ADMIN exists. The account is forced to set a new password
    at first login. Remove BOOTSTRAP_ADMIN_* from the environment afterwards.
    """
    if session.query(func.count(User.id)).filter(User.role == 'SYSTEM_ADMIN').scalar():
        return
    email, password = Config.BOOTSTRAP_ADMIN_EMAIL, Config.BOOTSTRAP_ADMIN_PASSWORD
    if not email or not password:
        print("[PRAVAH-AI] No System Administrator exists. Set BOOTSTRAP_ADMIN_EMAIL and "
              "BOOTSTRAP_ADMIN_PASSWORD for first start, or run: python manage.py create-user")
        return
    problem = validate_password_strength(password, email)
    if problem:
        print(f"[PRAVAH-AI] Bootstrap administrator not created: {problem}")
        return
    session.add(User(
        email=email, password_hash=hash_password(password), full_name="System Administrator",
        role='SYSTEM_ADMIN', must_change_password=True, password_changed_at=datetime.utcnow(),
    ))
    session.commit()
    print(f"[PRAVAH-AI] Bootstrap administrator created: {email} (password change required at first login)")


def _load_pilot_dataset(session):
    """Loads the bundled study-area files ONCE into an empty database.
    These records are flagged UNVERIFIED and shown as such in the application."""
    if session.query(func.count(Neighbourhood.id)).scalar():
        return
    geojson_path = DATA_DIR / 'whitefield_neighbourhoods.geojson'
    if geojson_path.exists():
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geo_data = json.load(f)
            for feat in geo_data.get('features', []):
                props = feat.get('properties', {})
                centroid = props.get('centroid', [77.7499, 12.9698])
                nb = Neighbourhood(
                    id=props.get('id'),
                    name=props.get('name'),
                    zone=props.get('zone', 'Mahadevapura'),
                    ward_no=props.get('ward_no'),
                    population=props.get('population', 0),
                    area_sqkm=props.get('area_sqkm', 1.0),
                    hazard_factor=props.get('hazard_factor', 50.0),
                    drainage_factor=props.get('drainage_factor', 50.0),
                    elevation_m=props.get('elevation_m'),
                    lake_proximity=props.get('lake_proximity'),
                    centroid_lat=centroid[1],
                    centroid_lon=centroid[0],
                    is_pilot=props.get('is_pilot', True),
                    verification_status='UNVERIFIED'
                )
                session.merge(nb)
                
    # 3. Seed Facilities
    fac_path = DATA_DIR / 'facilities.json'
    if fac_path.exists():
        with open(fac_path, 'r', encoding='utf-8') as f:
            fac_data = json.load(f)
            for item in fac_data:
                fac = Facility(
                    id=item.get('id'),
                    name=item.get('name'),
                    type=item.get('type'),
                    subtype=item.get('subtype'),
                    lat=item.get('lat'),
                    lon=item.get('lon'),
                    nearest_node_id=item.get('nearest_node_id'),
                    capacity_beds=item.get('capacity_beds', 0),
                    icu_beds=item.get('icu_beds', 0),
                    has_emergency_ward=item.get('has_emergency_ward', False),
                    phone=None,  # development phone numbers are fictional: never loaded
                    address=item.get('address'),
                    neighbourhood_id=item.get('neighbourhood_id'),
                    verification_status='UNVERIFIED'
                )
                session.merge(fac)
                
    # 4. Seed Shelters
    shelter_path = DATA_DIR / 'shelters.json'
    if shelter_path.exists():
        with open(shelter_path, 'r', encoding='utf-8') as f:
            shelter_data = json.load(f)
            for item in shelter_data:
                sh = Shelter(
                    id=item.get('id'),
                    name=item.get('name'),
                    address=item.get('address'),
                    lat=item.get('lat'),
                    lon=item.get('lon'),
                    nearest_node_id=item.get('nearest_node_id'),
                    total_capacity=item.get('total_capacity', 500),
                    current_occupancy=item.get('current_occupancy', 0),
                    status=item.get('status', 'OPERATIONAL'),
                    amenities_json=json.dumps(item.get('amenities', [])),
                    elevation_m=item.get('elevation_m'),
                    neighbourhood_id=item.get('neighbourhood_id'),
                    contact_officer=None,   # development names/phones are fictional: never loaded
                    phone=None,
                    verification_status='UNVERIFIED'
                )
                session.merge(sh)
                
    # 5. Seed Rescue Teams
    teams_path = DATA_DIR / 'rescue_teams.json'
    if teams_path.exists():
        with open(teams_path, 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
            for item in teams_data:
                rt = RescueTeam(
                    id=item.get('id'),
                    name=item.get('name'),
                    type=item.get('type'),
                    capabilities_json=json.dumps(item.get('capabilities', [])),
                    personnel_count=item.get('personnel_count', 6),
                    boats_count=item.get('boats_count', 0),
                    pumps_count=item.get('pumps_count', 0),
                    ambulances_count=item.get('ambulances_count', 0),
                    status=item.get('status', 'AVAILABLE'),
                    base_lat=item.get('base_lat'),
                    base_lon=item.get('base_lon'),
                    nearest_node_id=item.get('nearest_node_id'),
                    contact_commander=None,  # development names/phones are fictional: never loaded
                    phone=None,
                    verification_status='UNVERIFIED'
                )
                session.merge(rt)
                
    session.commit()


def init_db():
    if _url.startswith('sqlite'):
        print("[PRAVAH-AI] WARNING: using the SQLite development fallback. Data is NOT production data.")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        from services.ingestion_service import sync_registry  # local import: avoids circular import at module load
        sync_registry(session)
        _bootstrap_admin(session)
        if Config.LOAD_PILOT_DATASET:
            _load_pilot_dataset(session)
    finally:
        session.close()
