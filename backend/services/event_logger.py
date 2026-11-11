"""
Thread-safe in-memory ring buffer of backend execution events (last 200 events).
Never generates synthetic events. Only logs what actually executes.
"""
import threading
import uuid
from datetime import datetime, timezone
from collections import deque
from typing import Optional, Dict, Any


class EventLogger:
    """Thread-safe in-memory ring buffer of backend events (last 200 events)."""
    _events: deque = deque(maxlen=200)
    _lock = threading.Lock()

    @classmethod
    def log(
        cls,
        event_name: str,
        status: str,
        assessment_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log a real backend event.
        
        :param event_name: Descriptive name (e.g. 'flood_risk_calculation', 'api_request')
        :param status: 'started' | 'success' | 'failed' | 'skipped'
        :param assessment_id: Optional assessment/session ID for correlation
        :param duration_ms: Elapsed time in milliseconds (None if still running)
        :param details: Optional dict of supplementary fields
        :param error: Error message if status == 'failed'
        """
        event = {
            "id": str(uuid.uuid4())[:8],
            "event_name": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "assessment_id": assessment_id,
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "details": details or {},
            "error": error,
        }
        with cls._lock:
            cls._events.appendleft(event)

    @classmethod
    def get_events(cls, limit: int = 50) -> list:
        """Return the most recent events (up to limit)."""
        with cls._lock:
            return list(cls._events)[:limit]

    @classmethod
    def clear(cls) -> None:
        """Clear all events (for testing)."""
        with cls._lock:
            cls._events.clear()


# Singleton
event_logger = EventLogger()
