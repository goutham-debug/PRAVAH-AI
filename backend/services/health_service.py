"""Real backend health probes. Each check performs the operation it reports on."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text

from config import Config
from database import engine

_STARTED = datetime.utcnow()


def check_database() -> Dict[str, Any]:
    t = time.time()
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
            version = None
            if Config.database_backend() == "postgresql":
                version = c.execute(text("SHOW server_version")).scalar()
                try:
                    postgis = c.execute(text("SELECT postgis_version()")).scalar()
                except Exception:  # noqa: BLE001
                    c.rollback()
                    postgis = None
            else:
                version, postgis = c.execute(text("select sqlite_version()")).scalar(), None
        return {"status": "UP", "backend": Config.database_backend(), "server_version": version,
                "postgis": postgis or ("not enabled" if Config.database_backend() == "postgresql" else "n/a (SQLite)"),
                "latency_ms": int((time.time() - t) * 1000), "development_fallback": Config.database_backend() == "sqlite"}
    except Exception as e:  # noqa: BLE001
        return {"status": "DOWN", "backend": Config.database_backend(), "error": f"{type(e).__name__}: {str(e)[:160]}",
                "latency_ms": int((time.time() - t) * 1000)}


def api_status() -> Dict[str, Any]:
    return {"status": "UP", "environment": Config.ENV, "started_at": _STARTED.isoformat() + "Z",
            "uptime_seconds": int((datetime.utcnow() - _STARTED).total_seconds())}
