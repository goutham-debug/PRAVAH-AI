import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import init_db

# Import all route blueprints
from routes.auth_routes import auth_bp
from routes.incident_routes import incident_bp
from routes.geo_routes import geo_bp
from routes.road_routes import road_bp
from routes.flood_routes import flood_bp
from routes.scenario_routes import scenario_bp
from routes.facility_routes import facility_bp
from routes.shelter_routes import shelter_bp
from routes.rescue_routes import rescue_bp
from routes.situation_report_routes import sitrep_bp
from routes.weather_routes import weather_bp
from routes.admin_routes import admin_bp
from routes.system_routes import system_bp
from routes.dataops_routes import dataops_bp
from routes.ai_routes import ai_bp
from routes.monitor_routes import monitor_bp
from services.event_logger import event_logger
from security import enforce_request_policy
import time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.validate()
    
    # Enable Cross-Origin Resource Sharing
    if Config.CORS_ORIGINS:
        CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})
    app.before_request(enforce_request_policy)

    @app.before_request
    def record_start_time():
        from flask import request, g
        g.req_start_time = time.time()

    @app.after_request
    def log_api_event(response):
        from flask import request, g
        # Don't recurse on monitor polling
        if request.path.startswith('/api/') and not request.path.startswith('/api/monitor'):
            start = getattr(g, 'req_start_time', None)
            duration_ms = (time.time() - start) * 1000.0 if start else None
            status = "success" if response.status_code < 400 else "failed"
            event_logger.log(
                event_name=f"api_request",
                status=status,
                duration_ms=duration_ms,
                details={
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code
                }
            )
        return response

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(incident_bp, url_prefix='/api/incidents')
    app.register_blueprint(geo_bp, url_prefix='/api/geo')
    app.register_blueprint(road_bp, url_prefix='/api/roads')
    app.register_blueprint(flood_bp, url_prefix='/api/flood')
    app.register_blueprint(scenario_bp, url_prefix='/api/scenarios')
    app.register_blueprint(facility_bp, url_prefix='/api/facilities')
    app.register_blueprint(shelter_bp, url_prefix='/api/shelters')
    app.register_blueprint(rescue_bp, url_prefix='/api/rescue')
    app.register_blueprint(sitrep_bp, url_prefix='/api/sitrep')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(dataops_bp, url_prefix='/api/dataops')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')

    # Health check & system status
    @app.route('/api/health', methods=['GET'])
    def health_check():
        from services.health_service import check_database
        db_up = check_database()['status'] == 'UP'   # real SELECT 1; details are authority-only (/api/dataops/overview)
        return jsonify({"status": "healthy" if db_up else "degraded", "product": "PRAVAH AI"}), (200 if db_up else 503)

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error. Check server logs."}), 500

    return app

app = create_app()
init_db()

from services.ingestion_service import start_scheduler_if_configured  # noqa: E402
start_scheduler_if_configured()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=False)
