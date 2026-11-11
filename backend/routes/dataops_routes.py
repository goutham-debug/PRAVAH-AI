"""Authority-only Data Operations API. Access policy lives in security.py (READ_POLICY / WRITE_POLICY)."""
from __future__ import annotations

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from config import Config
from database import SessionLocal
from models import DataSource, Facility, IngestionEvent, IngestionRun, Neighbourhood, RescueTeam, Shelter
from services import health_service, ingestion_service as ing
from services.graph_service import graph_service

dataops_bp = Blueprint('dataops', __name__)

_CONNECTIVITY = {'OK': 'CONNECTED', 'INVALID': 'CONNECTED_INVALID_DATA', 'FAILED': 'UNREACHABLE',
                 'NOT_CONFIGURED': 'NOT_CONFIGURED', None: 'NOT_CHECKED'}


def _iso(d):
    return d.isoformat() + 'Z' if d else None


def _run_dict(r):
    return {"id": r.id, "source_key": r.source_key, "status": r.status, "triggered_by": r.triggered_by,
            "started_at": _iso(r.started_at), "finished_at": _iso(r.finished_at), "http_status": r.http_status,
            "attempts": r.attempts, "duration_ms": r.duration_ms, "records": r.records, "error": r.error}


def _event_dict(e):
    return {"id": e.id, "run_id": e.run_id, "source_key": e.source_key, "level": e.level, "message": e.message,
            "at": _iso(e.created_at)}


@dataops_bp.route('/overview', methods=['GET'])
def overview():
    live = request.args.get('live') == '1'
    session = SessionLocal()
    try:
        sources = []
        for src in session.query(DataSource).order_by(DataSource.key).all():
            v = ing.source_view(src)
            v['connectivity'] = _CONNECTIVITY.get(src.last_status, 'NOT_CHECKED')
            if live:  # real network probe, on request only
                status, detail = ing.ADAPTERS[src.key].probe()
                v['connectivity'], v['probe_detail'] = status, detail
            sources.append(v)
        failed = session.query(func.count(IngestionRun.id)).filter(IngestionRun.status.in_(('FAILED', 'INVALID'))).scalar()
        running = session.query(func.count(IngestionRun.id)).filter(IngestionRun.status == 'RUNNING').scalar()
        total_runs = session.query(func.count(IngestionRun.id)).scalar()
        last_ok = session.query(func.max(DataSource.last_success_at)).scalar()
        return jsonify({
            "success": True,
            "api": health_service.api_status(),
            "database": health_service.check_database(),
            "sources": sources,
            "ingestion": {"total_runs": total_runs, "failed_runs": failed, "running": running,
                          "last_successful_retrieval": _iso(last_ok),
                          "scheduler": f"every {Config.INGEST_INTERVAL_MINUTES} min" if Config.INGEST_INTERVAL_MINUTES else "off (manual refresh)"},
            "live_probe": live,
        })
    finally:
        session.close()


@dataops_bp.route('/datasets', methods=['GET'])
def datasets():
    """Inventory of datasets the platform needs, whether an authoritative version is in use, and what is missing."""
    session = SessionLocal()
    try:
        def n(model, *flt):
            return session.query(func.count(model.id)).filter(*flt).scalar()

        def src_state(key):
            s = session.get(DataSource, key)
            return ing.source_view(s) if s else None

        def row(id_, label, source_key, in_use, unverified, note):
            sv = src_state(source_key) if source_key else None
            state = sv['classification'] if sv else 'UNAVAILABLE'
            if in_use and unverified:
                state = 'UNVERIFIED'
            return {"id": id_, "label": label, "source_key": source_key, "state": state, "records_in_use": in_use,
                    "unverified_records": unverified, "provider_status": sv['last_status'] if sv else None,
                    "missing_credentials": sv['missing_credentials'] if sv else [], "note": note}

        nb, nb_u = n(Neighbourhood), n(Neighbourhood, Neighbourhood.verification_status != 'VERIFIED')
        fc, fc_u = n(Facility), n(Facility, Facility.verification_status != 'VERIFIED')
        sh, sh_u = n(Shelter), n(Shelter, Shelter.verification_status != 'VERIFIED')
        rt, rt_u = n(RescueTeam), n(RescueTeam, RescueTeam.verification_status != 'VERIFIED')
        edges = graph_service.baseline_graph.number_of_edges()
        return jsonify({"success": True, "datasets": [
            row('wards', 'Ward boundaries & population', 'gba', nb, nb_u,
                'Official GBA/BBMP boundaries; population needs an official census/ward source. Ingested files are validated but not auto-imported into the wards table.'),
            row('roads', 'Road network', 'osm_roads', edges, edges if Config.LOAD_PILOT_DATASET else 0,
                'OpenStreetMap extract is retrievable via Data Operations. The routing graph is not yet rebuilt from it (Part 2).'),
            row('facilities', 'Hospitals / critical facilities', None, fc, fc_u, 'No authorised source adapter. Needs the state health facility registry.'),
            row('shelters', 'Shelters & capacity', None, sh, sh_u, 'No authorised source. Needs an officially supplied shelter list.'),
            row('teams', 'Response teams & resources', None, rt, rt_u, 'No authorised source. Needs the authority resource register.'),
            row('rainfall_obs', 'Rainfall observations (gauges)', 'ksndmc', 0, 0, 'KSNDMC telemetry requires authorised access.'),
            row('imd', 'IMD observations & warnings', 'imd', 0, 0, 'IMD data requires authorised access.'),
            row('water_level', 'River/water levels', 'cwc', 0, 0, 'CWC/India-WRIS requires an authorised endpoint; relevance to Bengaluru catchments to be confirmed.'),
            row('flood_hazard', 'Flood-hazard layers', 'bhuvan', 0, 0, 'NRSC Bhuvan layer endpoint/token required.'),
            row('forecast', 'Weather forecast (supplementary)', 'open_meteo', 0, 0, 'Model forecast, not observation.'),
        ]})
    finally:
        session.close()


@dataops_bp.route('/runs', methods=['GET'])
def runs():
    limit = min(int(request.args.get('limit', 50)), 200)
    key = request.args.get('source')
    session = SessionLocal()
    try:
        q = session.query(IngestionRun)
        if key:
            q = q.filter(IngestionRun.source_key == key)
        return jsonify({"success": True, "runs": [_run_dict(r) for r in q.order_by(IngestionRun.id.desc()).limit(limit).all()]})
    finally:
        session.close()


@dataops_bp.route('/events', methods=['GET'])
def events():
    """Polling feed of real execution events. Client passes the last id it has (after_id)."""
    after = int(request.args.get('after_id', 0))
    limit = min(int(request.args.get('limit', 100)), 500)
    session = SessionLocal()
    try:
        rows = (session.query(IngestionEvent).filter(IngestionEvent.id > after)
                .order_by(IngestionEvent.id.asc()).limit(limit).all())
        if after == 0:  # first load: most recent window rather than the oldest
            rows = list(reversed(session.query(IngestionEvent).order_by(IngestionEvent.id.desc()).limit(limit).all()))
        running = session.query(func.count(IngestionRun.id)).filter(IngestionRun.status == 'RUNNING').scalar()
        return jsonify({"success": True, "events": [_event_dict(e) for e in rows], "running": running,
                        "last_id": rows[-1].id if rows else after})
    finally:
        session.close()


@dataops_bp.route('/sources/<key>/refresh', methods=['POST'])
def refresh(key):
    if key not in ing.ADAPTERS:
        return jsonify({"success": False, "error": "Unknown data source."}), 404
    run_id = ing.start_async(key, g.current_user.email)
    from models import LoginAudit
    from security import client_ip
    session = SessionLocal()
    try:
        session.add(LoginAudit(user_id=g.current_user.id, email=g.current_user.email, event='DATA_REFRESH',
                               ip_address=client_ip(), detail=(key + (' (already running)' if run_id is None else ''))[:255]))
        session.commit()
    finally:
        session.close()
    if run_id is None:
        return jsonify({"success": False, "error": "A retrieval for this source is already running."}), 409
    return jsonify({"success": True, "run_id": run_id, "message": "Retrieval started."}), 202
