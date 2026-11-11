import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def _database_url() -> str:
    """Supabase Postgres connection string from DATABASE_URL.

    Accepts the 'postgres://' / 'postgresql://' forms Supabase shows in its dashboard
    and normalises them for SQLAlchemy + psycopg2. A local SQLite file is used only
    when DATABASE_URL is unset AND APP_ENV is not 'production' (Config.validate() enforces this).
    """
    url = os.environ.get('DATABASE_URL', '').strip()
    if not url:
        return f"sqlite:///{BASE_DIR / 'pravah_dev.db'}"
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        url = 'postgresql+psycopg2://' + url[len('postgresql://'):]
    return url


class Config:
    ENV = os.environ.get('APP_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    SQLALCHEMY_DATABASE_URI = _database_url()

    # Sessions
    SESSION_HOURS = int(os.environ.get('SESSION_HOURS', '8'))
    MAX_FAILED_LOGINS = int(os.environ.get('MAX_FAILED_LOGINS', '5'))
    LOCKOUT_MINUTES = int(os.environ.get('LOCKOUT_MINUTES', '15'))
    MIN_PASSWORD_LENGTH = 12

    # One-time bootstrap administrator (disabled automatically once any admin exists)
    BOOTSTRAP_ADMIN_EMAIL = os.environ.get('BOOTSTRAP_ADMIN_EMAIL', '').strip().lower()
    BOOTSTRAP_ADMIN_PASSWORD = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD', '')

    # CORS: comma-separated list of allowed frontend origins (empty = same-origin only)
    CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]

    # Study area (used as map/weather default)
    PILOT_LAT = 12.9698
    PILOT_LON = 77.7499
    PILOT_ZONE = "Whitefield-Mahadevapura, Bengaluru"

    # External APIs
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    WEATHER_CACHE_SECONDS = 600
    MAX_SNAP_DISTANCE_KM = 3.0

    # Study-area bounding box S,W,N,E used for OSM extraction (an operator setting, not a data claim)
    STUDY_BBOX = os.environ.get('STUDY_BBOX', '12.90,77.66,13.03,77.82')

    # Quarantined development files (backend/data/dev_quarantine) are NOT real data. Loading is explicit,
    # defaults to OFF, and is refused in production.
    LOAD_PILOT_DATASET = os.environ.get('LOAD_PILOT_DATASET', 'false').lower() == 'true'

    # Data Operations
    INGEST_INTERVAL_MINUTES = int(os.environ.get('INGEST_INTERVAL_MINUTES', '0'))  # 0 = no background scheduler

    @classmethod
    def is_production(cls) -> bool:
        return cls.ENV.lower() == 'production'

    @classmethod
    def database_backend(cls) -> str:
        return 'sqlite' if cls.SQLALCHEMY_DATABASE_URI.startswith('sqlite') else 'postgresql'

    @classmethod
    def validate(cls):
        """Fail fast on unsafe production configuration. Called at app start."""
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY must be set (32+ characters). Generate one with: "
                               "python -c 'import secrets;print(secrets.token_urlsafe(48))'")
        if cls.is_production():
            if cls.database_backend() != 'postgresql':
                raise RuntimeError("APP_ENV=production requires DATABASE_URL pointing to PostgreSQL (Supabase). "
                                   "SQLite is a development fallback and is refused in production.")
            if cls.LOAD_PILOT_DATASET:
                raise RuntimeError("LOAD_PILOT_DATASET=true is refused in production: quarantined development data "
                                   "must never be loaded into a production database.")
