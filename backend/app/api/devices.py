from flask import Blueprint, jsonify, request
from app.repositories.device_repo import DeviceRepository
from app.repositories.observation_repo import ObservationRepository
from app.repositories.metric_repo import MetricRepository
from app.utils.errors import NotFoundError

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/devices", methods=["GET"])
def list_devices():
    status = request.args.get("status")
    device_type = request.args.get("type")
    agent_id = request.args.get("agent_id")
    devices = DeviceRepository.find_all(status=status, device_type=device_type, agent_id=agent_id)
    return jsonify({
        "devices": [d.to_dict() for d in devices],
        "count": len(devices),
    })


@devices_bp.route("/devices/<device_id>", methods=["GET"])
def get_device(device_id):
    device = DeviceRepository.find_by_id(device_id)
    if not device:
        raise NotFoundError(f"Device {device_id} not found")

    observations = ObservationRepository.find_by_device(device_id, limit=20)
    metrics_summary = {}
    for mt in ["latency", "availability", "packet_loss"]:
        stats = MetricRepository.get_stats(device_id, mt)
        latest = MetricRepository.get_latest(device_id, mt)
        metrics_summary[mt] = {
            "stats": stats,
            "latest": latest.to_dict() if latest else None,
        }

    return jsonify({
        "device": device.to_dict(),
        "metrics_summary": metrics_summary,
        "recent_observations": [o.to_dict() for o in observations],
    })


@devices_bp.route("/devices/stats", methods=["GET"])
def device_stats():
    status_counts = DeviceRepository.count_by_status()
    from app.config.database import db
    from app.models.device import Device
    type_counts = dict(
        db.session.query(Device.device_type, db.func.count(Device.id))
        .group_by(Device.device_type).all()
    )
    total = Device.query.count()
    return jsonify({
        "total": total,
        "by_status": status_counts,
        "by_type": type_counts,
    })


@devices_bp.route("/observations", methods=["GET"])
def list_observations():
    device_id = request.args.get("device_id")
    limit = request.args.get("limit", 100, type=int)
    if device_id:
        observations = ObservationRepository.find_by_device(device_id, limit=limit)
    else:
        observations = ObservationRepository.find_recent(limit=limit)
    return jsonify({
        "observations": [o.to_dict() for o in observations],
        "count": len(observations),
    })
