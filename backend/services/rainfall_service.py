"""
Rainfall service: checks KSNDMC_API_KEY and IMD_API_KEY env vars.
If not set: returns UNAVAILABLE with explanation.
If set: attempts real API call. Never substitutes fake values.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

log = logging.getLogger('pravah.rainfall')

# Pilot zone coordinates
PILOT_LAT = 12.9698
PILOT_LON = 77.7499
PILOT_ZONE = "Whitefield-Mahadevapura, Bengaluru (BBMP)"


class RainfallService:
    """
    Wraps IMD and KSNDMC real-time rainfall APIs.
    Returns UNAVAILABLE if credentials are not configured.
    Never fabricates rainfall data.
    """

    def get_rainfall(self) -> Dict[str, Any]:
        """
        Attempt to retrieve real-time rainfall data.
        Priority: KSNDMC → IMD → UNAVAILABLE
        """
        ksndmc_key = os.environ.get('KSNDMC_API_KEY', '').strip()
        imd_key = os.environ.get('IMD_API_KEY', '').strip()

        if ksndmc_key:
            result = self._fetch_ksndmc(ksndmc_key)
            if result.get('status') != 'UNAVAILABLE':
                return result

        if imd_key:
            result = self._fetch_imd(imd_key)
            if result.get('status') != 'UNAVAILABLE':
                return result

        # Neither credential set
        missing = []
        if not ksndmc_key:
            missing.append('KSNDMC_API_KEY')
        if not imd_key:
            missing.append('IMD_API_KEY')

        return {
            "status": "UNAVAILABLE",
            "classification": "UNAVAILABLE",
            "source": "KSNDMC / IMD (not configured)",
            "reason": f"Credentials not set: {', '.join(missing)}. "
                      "Real-time gauge data cannot be retrieved without API credentials. "
                      "Register at ksndmc.org or imd.gov.in to obtain access.",
            "missing_credentials": missing,
            "rainfall_mm": None,
            "disclaimer": "No rainfall value is substituted when real data is unavailable.",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    def _fetch_ksndmc(self, api_key: str) -> Dict[str, Any]:
        """
        Attempt to call KSNDMC (Karnataka State Natural Disaster Monitoring Centre) API.
        KSNDMC provides automatic weather station (AWS) data for Karnataka.
        Registration: https://ksndmc.org
        """
        import time
        try:
            import requests
            # KSNDMC API endpoint (requires registration)
            url = "https://ksndmc.org/api/v1/aws/rainfall"
            params = {
                "api_key": api_key,
                "district": "Bengaluru Urban",
                "station": "Whitefield",
                "format": "json",
            }
            start = time.time()
            resp = requests.get(url, params=params, timeout=10)
            duration_ms = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                rainfall_mm = data.get('current_rainfall_mm') or data.get('rainfall_mm')
                if rainfall_mm is not None:
                    return {
                        "status": "OBSERVED",
                        "classification": "OBSERVED",
                        "source": "KSNDMC AWS Network",
                        "source_url": url,
                        "rainfall_mm": float(rainfall_mm),
                        "station": data.get('station_name', 'Whitefield AWS'),
                        "observation_time": data.get('observation_time'),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": round(duration_ms, 1),
                        "disclaimer": "Real-time gauge observation from KSNDMC AWS network.",
                    }
            elif resp.status_code == 401:
                log.warning("KSNDMC: Invalid API key")
                return {"status": "UNAVAILABLE", "reason": "KSNDMC: Invalid API key (401 Unauthorized)"}
            elif resp.status_code == 404:
                log.warning("KSNDMC: Station not found")
                return {"status": "UNAVAILABLE", "reason": "KSNDMC: Station not found (404)"}
            else:
                log.warning("KSNDMC: HTTP %s", resp.status_code)
                return {"status": "UNAVAILABLE", "reason": f"KSNDMC: HTTP {resp.status_code}"}

        except ImportError:
            return {"status": "UNAVAILABLE", "reason": "requests library not installed"}
        except Exception as e:
            log.error("KSNDMC fetch error: %s", e)
            return {"status": "UNAVAILABLE", "reason": f"KSNDMC fetch error: {str(e)[:200]}"}

    def _fetch_imd(self, api_key: str) -> Dict[str, Any]:
        """
        Attempt to call IMD (India Meteorological Department) API.
        IMD provides daily/hourly rainfall for Karnataka stations.
        Registration: https://mausam.imd.gov.in (requires institutional access)
        """
        import time
        try:
            import requests
            url = "https://api.weather.gov.in/v1/rainfall/current"
            params = {
                "api_key": api_key,
                "station_id": "VOBG",  # Bengaluru / HAL airport station
                "format": "json",
            }
            start = time.time()
            resp = requests.get(url, params=params, timeout=10)
            duration_ms = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                rainfall_mm = data.get('rainfall_mm') or data.get('current_rainfall')
                if rainfall_mm is not None:
                    return {
                        "status": "OBSERVED",
                        "classification": "OBSERVED",
                        "source": "India Meteorological Department (IMD)",
                        "source_url": url,
                        "rainfall_mm": float(rainfall_mm),
                        "station": data.get('station_name', 'Bengaluru (VOBG)'),
                        "observation_time": data.get('observation_time'),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": round(duration_ms, 1),
                        "disclaimer": "IMD station rainfall observation. Station may be ~12 km from pilot zone.",
                    }
            elif resp.status_code == 401:
                return {"status": "UNAVAILABLE", "reason": "IMD: Invalid or expired API key (401)"}
            else:
                return {"status": "UNAVAILABLE", "reason": f"IMD: HTTP {resp.status_code}"}

        except ImportError:
            return {"status": "UNAVAILABLE", "reason": "requests library not installed"}
        except Exception as e:
            log.error("IMD fetch error: %s", e)
            return {"status": "UNAVAILABLE", "reason": f"IMD fetch error: {str(e)[:200]}"}

    def get_bbmp_unavailable_response(self, api_type: str) -> Dict[str, Any]:
        """
        BBMP does not provide public APIs for road closures, drainage, or flood incidents.
        Always returns a documented UNAVAILABLE response.
        """
        descriptions = {
            "road_closure": "BBMP Road Closure API — no public API available. Manual input required via BBMP control room.",
            "drainage": "BBMP Drainage Network API — no public API available. Field inspection data only.",
            "flood_incident": "BBMP Flood Incident API — no public API available. Reports collected via BBMP helpline (080-22221188).",
        }
        return {
            "status": "UNAVAILABLE",
            "classification": "UNAVAILABLE",
            "api_type": api_type,
            "source": "BBMP",
            "reason": descriptions.get(api_type, "BBMP API: no public API available"),
            "public_api_available": False,
            "workaround": "Contact BBMP control room directly or use manual data entry in PRAVAH AI.",
            "bbmp_helpline": "080-22221188",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }


# Singleton
rainfall_service = RainfallService()
