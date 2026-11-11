"""Central data registry + ingestion execution.

Every event recorded here is written by code that actually executed (request sent, status received, validation
run, file stored). Nothing is synthesised for display.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from config import Config
from providers.adapters import build_adapters
from providers.base import (AdapterResult, FAILED, INVALID, NOT_ASSESSED, NOT_CONFIGURED, OK, STALE, UNAVAILABLE,
                            now_iso)

log = logging.getLogger("pravah.ingestion")

ADAPTERS = build_adapters(Config.PILOT_LAT, Config.PILOT_LON, Config.STUDY_BBOX)
_locks = {k: threading.Lock() for k in ADAPTERS}
STALE_FACTOR = 3  # data older than 3x its expected refresh interval is STALE


def _now() -> datetime:
    return datetime.utcnow()


def _iso(d: Optional[datetime]) -> Optional[str]:
    return d.isoformat() + "Z" if d else None


def sync_registry(session) -> None:
    """Ensure one registry row per adapter; refresh static metadata and credential status."""
    from models import DataSource
    for key, ad in ADAPTERS.items():
        src = session.get(DataSource, key)
        d = ad.describe()
        if not src:
            src = DataSource(key=key, classification=NOT_ASSESSED, validation_status="NOT_RUN")
            session.add(src)
        src.provider, src.name, src.dataset_type = d["provider"], d["name"], d["dataset_type"]
        src.source_url, src.data_format, src.licence, src.coverage = d["source_url"], d["format"], d["licence"], d["coverage"]
        src.ttl_seconds, src.notes = d["ttl_seconds"], d["notes"][:500]
        src.configured = not d["missing_credentials"]
        src.missing_credentials = ", ".join(d["missing_credentials"]) or None
    session.commit()


def effective_classification(src) -> str:
    """Classification a consumer must display *now*: NOT_ASSESSED if never retrieved, UNAVAILABLE if the only
    attempts failed, STALE if the last good retrieval is older than STALE_FACTOR x ttl."""
    if not src.last_success_at:
        return UNAVAILABLE if src.last_attempt_at else NOT_ASSESSED
    if _now() - src.last_success_at > timedelta(seconds=src.ttl_seconds * STALE_FACTOR):
        return STALE
    return src.classification


def source_view(src) -> Dict[str, Any]:
    return {
        "key": src.key, "provider": src.provider, "name": src.name, "dataset_type": src.dataset_type,
        "source_url": src.source_url, "format": src.data_format, "licence": src.licence, "coverage": src.coverage,
        "classification": effective_classification(src), "stored_classification": src.classification,
        "validation_status": src.validation_status, "last_status": src.last_status,
        "last_attempt_at": _iso(src.last_attempt_at), "last_success_at": _iso(src.last_success_at),
        "retrieved_at": _iso(src.retrieved_at), "observation_date": src.observation_date,
        "record_count": src.record_count, "checksum": src.checksum, "ttl_seconds": src.ttl_seconds,
        "configured": bool(src.configured),
        "missing_credentials": [m.strip() for m in (src.missing_credentials or "").split(",") if m.strip()],
        "last_error": src.last_error, "notes": src.notes,
        "validation": json.loads(src.validation_json or "{}"),
    }


def log_event(session, source_key: str, message: str, level: str = "INFO", run_id: Optional[int] = None) -> None:
    from models import IngestionEvent
    session.add(IngestionEvent(run_id=run_id, source_key=source_key, level=level, message=message[:500]))
    session.commit()


def persist_result(session, key: str, result: AdapterResult, triggered_by: str, run=None, started: Optional[datetime] = None):
    """Write the outcome of one real retrieval attempt to the run log and the registry. Returns the run."""
    from models import DataSource, IngestionRun
    src = session.get(DataSource, key)
    if src is None:
        sync_registry(session)
        src = session.get(DataSource, key)
    if run is None:
        run = IngestionRun(source_key=key, triggered_by=triggered_by, started_at=started or _now())
        session.add(run)
        session.flush()
    for line in result.events:
        lvl = "ERROR" if "failed" in line.lower() or line.startswith("No response") else "INFO"
        log_event(session, key, line, lvl, run.id)
    run.status, run.finished_at = result.status, _now()
    run.http_status, run.attempts, run.duration_ms = result.http_status, result.attempts, result.duration_ms
    run.records, run.error = result.records, (result.error or None) and result.error[:500]
    run.validation_json = json.dumps(result.validation or {})
    src.last_attempt_at, src.last_status, src.last_error = run.finished_at, result.status, run.error
    if result.status == OK:
        src.last_success_at = run.finished_at
        src.retrieved_at = datetime.fromisoformat(result.retrieved_at).replace(tzinfo=None)
        src.classification, src.validation_status = result.classification, "PASSED"
        src.observation_date, src.record_count = result.observed_at, result.records
        src.checksum, src.storage_path = result.checksum, result.storage_path
        src.validation_json = json.dumps(result.validation or {})
    elif result.status == INVALID:
        src.validation_status = "FAILED"
        src.validation_json = json.dumps(result.validation or {})
    session.commit()
    return run


def execute_run(key: str, triggered_by: str, run_id: Optional[int] = None) -> int:
    """Synchronously execute one source. Safe to call from a request thread or a worker thread."""
    from database import SessionLocal
    from models import IngestionRun
    ad = ADAPTERS[key]
    session = SessionLocal()
    try:
        run = session.get(IngestionRun, run_id) if run_id else None
        if run is None:
            run = IngestionRun(source_key=key, triggered_by=triggered_by)
            session.add(run)
            session.flush()
        started = run.started_at
        log_event(session, key, f"Run #{run.id} started ({ad.provider}, triggered by {triggered_by})", "INFO", run.id)
        try:
            result = ad.run()
        except Exception as e:  # noqa: BLE001 - adapter bug must surface as a failed run, not crash the worker
            log.exception("adapter crashed")
            result = AdapterResult(FAILED, UNAVAILABLE, error=f"Adapter error: {type(e).__name__}: {str(e)[:200]}",
                                   events=[f"Adapter raised {type(e).__name__}"])
        persist_result(session, key, result, triggered_by, run=run, started=started)
        log_event(session, key, f"Run #{run.id} finished: {result.status}"
                  + (f" ({result.records} records)" if result.status == OK else f" — {result.error}"),
                  "INFO" if result.status in (OK, NOT_CONFIGURED) else "ERROR", run.id)
        return run.id
    finally:
        SessionLocal.remove()


def start_async(key: str, triggered_by: str) -> Optional[int]:
    """Queue a background run. Returns the run id, or None if this source is already running."""
    from database import SessionLocal
    from models import IngestionRun
    lock = _locks[key]
    if not lock.acquire(blocking=False):
        return None
    session = SessionLocal()
    try:
        run = IngestionRun(source_key=key, triggered_by=triggered_by, status="RUNNING")
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()

    def _worker():
        try:
            execute_run(key, triggered_by, run_id)
        finally:
            lock.release()

    threading.Thread(target=_worker, name=f"ingest-{key}", daemon=True).start()
    return run_id


def record_external_run(key: str, result: AdapterResult, triggered_by: str) -> None:
    """Used by consumers that fetched through an adapter themselves (e.g. the weather panel) so the registry
    reflects reality. Best-effort: registry failure must never break the caller."""
    from database import SessionLocal
    session = SessionLocal()
    try:
        persist_result(session, key, result, triggered_by)
    except Exception:  # noqa: BLE001
        session.rollback()
        log.exception("could not record external run for %s", key)
    finally:
        session.close()


_scheduler_started = False


def start_scheduler_if_configured() -> bool:
    """Optional background refresh of configured sources. Off unless INGEST_INTERVAL_MINUTES > 0."""
    global _scheduler_started
    if _scheduler_started or Config.INGEST_INTERVAL_MINUTES <= 0:
        return False
    _scheduler_started = True

    def loop():
        import time
        while True:
            for key, ad in ADAPTERS.items():
                if ad.configured() and key != "osm_roads":  # large OSM extracts are refreshed manually
                    start_async(key, "scheduler")
            time.sleep(Config.INGEST_INTERVAL_MINUTES * 60)

    threading.Thread(target=loop, name="ingest-scheduler", daemon=True).start()
    return True
