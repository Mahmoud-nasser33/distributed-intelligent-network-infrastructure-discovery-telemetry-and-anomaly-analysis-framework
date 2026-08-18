from flask import Blueprint, jsonify, request
from app.repositories.metric_repo import MetricRepository
from app.repositories.device_repo import DeviceRepository
from app.telemetry.collector import TelemetryCollector
from app.utils.errors import NotFoundError, ValidationError
from app.config.database import db
from flask import current_app
import threading

telemetry_bp = Blueprint("telemetry", __name__)


@telemetry_bp.route("/telemetry/<device_id>", methods=["GET"])
def get_device_telemetry(device_id):
    device = DeviceRepository.find_by_id(device_id)
    if not device:
        raise NotFoundError(f"Device {device_id} not found")

    metric_type = request.args.get("type")
    limit = request.args.get("limit", 100, type=int)

    metrics = MetricRepository.find_by_device(device_id, metric_type=metric_type, limit=limit)
    return jsonify({
        "device_id": device_id,
        "metrics": [m.to_dict() for m in metrics],
        "count": len(metrics),
    })


@telemetry_bp.route("/telemetry/<device_id>/stats", methods=["GET"])
def get_device_telemetry_stats(device_id):
    device = DeviceRepository.find_by_id(device_id)
    if not device:
        raise NotFoundError(f"Device {device_id} not found")

    stats = {}
    for mt in ["latency", "availability", "packet_loss", "cpu_usage", "memory_usage"]:
        s = MetricRepository.get_stats(device_id, mt)
        latest = MetricRepository.get_latest(device_id, mt)
        if s["count"] > 0:
            stats[mt] = {**s, "latest": latest.to_dict() if latest else None}

    return jsonify({
        "device_id": device_id,
        "stats": stats,
    })


@telemetry_bp.route("/telemetry/collect", methods=["POST"])
def collect_telemetry():
    data = request.get_json() or {}
    device_id = data.get("device_id")

    if device_id:
        device = DeviceRepository.find_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        collector = TelemetryCollector()
        result = collector.collect_ping_metrics(device.id, device.ip_address)
        return jsonify({"device_id": device_id, "metrics": result})
    else:
        def _collect():
            with current_app.app_context():
                collector = TelemetryCollector()
                collector.collect_all_devices()

        thread = threading.Thread(target=_collect, daemon=True)
        thread.start()
        return jsonify({"message": "Telemetry collection started"}), 202


@telemetry_bp.route("/telemetry/overview", methods=["GET"])
def telemetry_overview():
    from app.models.device import Device
    online = Device.query.filter_by(status="online").count()
    offline = Device.query.filter_by(status="offline").count()
    unknown = Device.query.filter_by(status="unknown").count()

    return jsonify({
        "online": online,
        "offline": offline,
        "unknown": unknown,
        "total": online + offline + unknown,
    })
