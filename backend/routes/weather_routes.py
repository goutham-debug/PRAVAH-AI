from flask import Blueprint, request, jsonify
from services.weather_service import weather_service
from config import Config

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('', methods=['GET'])
def get_weather():
    try:
        lat = float(request.args.get('lat', Config.PILOT_LAT))
        lon = float(request.args.get('lon', Config.PILOT_LON))
    except (TypeError, ValueError):
        lat, lon = Config.PILOT_LAT, Config.PILOT_LON

    data = weather_service.get_weather(lat, lon)
    return jsonify({"success": True, "weather": data})
