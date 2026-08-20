from flask import Blueprint
from app.api.health import health_bp
from app.api.devices import devices_bp
from app.api.agents import agents_bp
from app.api.discovery import discovery_bp
from app.api.telemetry import telemetry_bp
from app.api.topology import topology_bp
from app.api.anomalies import anomalies_bp
from app.api.tasks import tasks_bp

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(health_bp)
api_bp.register_blueprint(devices_bp)
api_bp.register_blueprint(agents_bp)
api_bp.register_blueprint(discovery_bp)
api_bp.register_blueprint(telemetry_bp)
api_bp.register_blueprint(topology_bp)
api_bp.register_blueprint(anomalies_bp)
api_bp.register_blueprint(tasks_bp)
