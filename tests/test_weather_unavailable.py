import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))


def test_weather_never_fabricates_values(monkeypatch):
    import requests
    from services.weather_service import WeatherService

    def boom(*a, **k):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, 'get', boom)
    w = WeatherService().get_weather()
    assert w['status'] == 'UNAVAILABLE'
    assert 'temperature_c' not in w and 'rainfall_current_mm' not in w
