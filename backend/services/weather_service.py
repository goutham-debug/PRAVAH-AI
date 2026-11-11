import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from config import Config
from providers.adapters import OpenMeteoAdapter

log = logging.getLogger('pravah.weather')

class WeatherService:
    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None
        self._last_fetched_timestamp: float = 0
        self._cache_duration_sec: int = Config.WEATHER_CACHE_SECONDS

    def get_weather(self, lat: float = Config.PILOT_LAT, lon: float = Config.PILOT_LON) -> Dict[str, Any]:
        """
        Retrieves weather with in-memory caching and resilient fallback.
        """
        current_time = time.time()
        
        # Check cache validity
        if self._cache and (current_time - self._last_fetched_timestamp < self._cache_duration_sec):
            cached_data = dict(self._cache)
            cached_data["is_cached"] = True
            cached_data["cache_age_seconds"] = int(current_time - self._last_fetched_timestamp)
            return cached_data

        adapter = OpenMeteoAdapter(lat, lon)
        result = adapter.run()
        try:  # keep the data registry truthful about this retrieval (best-effort)
            from services.ingestion_service import record_external_run
            record_external_run('open_meteo', result, 'weather-panel')
        except Exception as e:  # noqa: BLE001
            log.warning("registry update skipped: %s", e)

        if result.status == 'OK':
            p = result.payload
            cur, hourly = p["current"], p["hourly"]
            forecast = []
            for t, r, tmp in list(zip(hourly["time"], hourly["precipitation"], hourly["temperature_2m"] or [None] * 99))[:12]:
                forecast.append({"time": t.split("T")[-1] if "T" in t else t,
                                 "precipitation_mm": round(float(r or 0), 1),
                                 "temperature_c": round(float(tmp), 1) if tmp is not None else None})
            weather_result = {
                "source": "Open-Meteo Weather API",
                "source_url": adapter.source_url,
                "status": "FORECAST_MODEL",
                "classification": "FORECAST",
                "location": Config.PILOT_ZONE,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": cur["temperature_2m"],
                "rainfall_current_mm": cur["precipitation"],
                "wind_speed_kmh": cur["wind_speed_10m"],
                "humidity_pct": cur["relative_humidity_2m"],
                "weather_description": self._describe_weather_code(cur.get("weather_code")),
                "hourly_forecast": forecast,
                "observation_time": result.observed_at,
                "last_updated": result.retrieved_at,
                "is_cached": False,
                "disclaimer": "Open-Meteo model output (forecast/reanalysis), not a direct gauge observation, and not a flood warning."
            }
            self._cache = weather_result
            self._last_fetched_timestamp = current_time
            return weather_result

        return self._unavailable()

    def _unavailable(self) -> Dict[str, Any]:
        """No substitute values are generated when the provider cannot be reached."""
        return {
            "source": "Open-Meteo",
            "status": "UNAVAILABLE",
            "classification": "UNAVAILABLE",
            "last_updated": None,
            "disclaimer": "Weather data could not be retrieved. No substitute values are shown."
        }

    def _describe_weather_code(self, code: int) -> str:
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            51: "Light drizzle",
            53: "Moderate drizzle",
            61: "Slight rain showers",
            63: "Moderate monsoon rain",
            65: "Heavy convective downpour",
            80: "Heavy rain showers",
            81: "Violent rain showers",
            95: "Thunderstorm with torrential rain"
        }
        return codes.get(code, "Not classified")

# Singleton instance
weather_service = WeatherService()
