"""Adapter contract, classification vocabulary and shared result type."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Information classification (every stored/served dataset carries exactly one)
OBSERVED, OFFICIAL, FORECAST, MODELLED = "OBSERVED", "OFFICIAL", "FORECAST", "MODELLED"
UNVERIFIED, STALE, UNAVAILABLE, NOT_ASSESSED = "UNVERIFIED", "STALE", "UNAVAILABLE", "NOT_ASSESSED"
CLASSIFICATIONS = (OBSERVED, OFFICIAL, FORECAST, MODELLED, UNVERIFIED, STALE, UNAVAILABLE, NOT_ASSESSED)

# Run outcomes
OK, FAILED, NOT_CONFIGURED, INVALID = "OK", "FAILED", "NOT_CONFIGURED", "INVALID"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AdapterResult:
    status: str                                  # OK | FAILED | NOT_CONFIGURED | INVALID
    classification: str = UNAVAILABLE
    records: int = 0
    payload: Any = None                          # parsed data (not persisted by the registry itself)
    observed_at: Optional[str] = None            # observation / reference time reported by the provider
    retrieved_at: str = field(default_factory=now_iso)
    validation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    http_status: Optional[int] = None
    attempts: int = 0
    duration_ms: int = 0
    checksum: Optional[str] = None
    storage_path: Optional[str] = None
    missing_credentials: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)   # real steps executed, in order


class Adapter:
    key = ""
    provider = ""
    name = ""
    dataset_type = ""
    source_url = ""            # reference/portal or API base
    licence = ""
    coverage = ""
    fmt = "json"
    ttl_seconds = 3600         # a successful retrieval older than 3x this is reported STALE
    required_env: List[str] = []
    notes = ""

    def missing_env(self) -> List[str]:
        return [e for e in self.required_env if not os.environ.get(e, "").strip()]

    def configured(self) -> bool:
        return not self.missing_env()

    def describe(self) -> Dict[str, Any]:
        return {
            "key": self.key, "provider": self.provider, "name": self.name, "dataset_type": self.dataset_type,
            "source_url": self.source_url, "licence": self.licence, "coverage": self.coverage, "format": self.fmt,
            "ttl_seconds": self.ttl_seconds, "required_env": list(self.required_env),
            "missing_credentials": self.missing_env(), "notes": self.notes,
        }

    def run(self) -> AdapterResult:  # pragma: no cover - interface
        raise NotImplementedError

    def probe(self):  # pragma: no cover - interface
        """Lightweight reachability check. Returns (status, detail)."""
        raise NotImplementedError
