import pytest
from services.event_logger import event_logger

def test_event_logger_ring_buffer():
    """EventLogger must store events thread-safely in a ring buffer."""
    event_logger.clear()
    
    event_logger.log(
        event_name="test_geospatial_calc",
        status="success",
        assessment_id="TEST-001",
        duration_ms=45.2,
        details={"wards": 8}
    )

    events = event_logger.get_events(limit=10)
    assert len(events) == 1
    ev = events[0]
    assert ev["event_name"] == "test_geospatial_calc"
    assert ev["status"] == "success"
    assert ev["assessment_id"] == "TEST-001"
    assert ev["duration_ms"] == 45.2

def test_monitor_health_endpoint(client):
    """GET /api/monitor/health returns real system health for API, DB, and external providers."""
    res = client.get('/api/monitor/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "api" in data
    assert "database" in data
    assert "providers" in data
    assert "open_meteo" in data["providers"]
    assert "ksndmc" in data["providers"]
    assert "imd" in data["providers"]

def test_monitor_events_endpoint(client):
    """GET /api/monitor/events returns recorded execution events."""
    event_logger.log(
        event_name="test_route_calc",
        status="success",
        duration_ms=12.5
    )
    res = client.get('/api/monitor/events?limit=20')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["events"]) >= 1
