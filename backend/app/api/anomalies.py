from flask import Blueprint, jsonify, request, current_app
from app.repositories.anomaly_repo import AnomalyRepository
from app.repositories.device_repo import DeviceRepository
from app.anomaly.detectors import AnomalyDetector, ThresholdDetector
from app.utils.errors import NotFoundError

anomalies_bp = Blueprint("anomalies", __name__)


@anomalies_bp.route("/anomalies", methods=["GET"])
def list_anomalies():
    status = request.args.get("status")
    severity = request.args.get("severity")
    device_id = request.args.get("device_id")
    limit = request.args.get("limit", 50, type=int)

    if device_id:
        anomalies = AnomalyRepository.find_by_device(device_id, limit=limit)
    elif status or severity:
        anomalies = AnomalyRepository.find_open(status=status, severity=severity)
    else:
        anomalies = AnomalyRepository.find_recent(limit=limit)

    return jsonify({
        "anomalies": [a.to_dict() for a in anomalies],
        "count": len(anomalies),
    })


@anomalies_bp.route("/anomalies/<anomaly_id>", methods=["GET"])
def get_anomaly(anomaly_id):
    anomaly = AnomalyRepository.find_by_id(anomaly_id)
    if not anomaly:
        raise NotFoundError(f"Anomaly {anomaly_id} not found")
    return jsonify({"anomaly": anomaly.to_dict()})


@anomalies_bp.route("/anomalies/<anomaly_id>/status", methods=["PUT"])
def update_anomaly_status(anomaly_id):
    data = request.get_json()
    if not data or not data.get("status"):
        return jsonify({"error": "Status is required"}), 400
    anomaly = AnomalyRepository.update_status(anomaly_id, data["status"])
    if not anomaly:
        raise NotFoundError(f"Anomaly {anomaly_id} not found")
    return jsonify({"anomaly": anomaly.to_dict()})


@anomalies_bp.route("/anomalies/detect", methods=["POST"])
def detect_anomalies():
    data = request.get_json() or {}
    device_id = data.get("device_id")
    run_async = data.get("run_async", False)

    if run_async:
        task_id = current_app.task_manager.submit_anomaly_detection(
            device_id=device_id,
        )
        return jsonify({
            "task_id": task_id,
            "message": "Anomaly detection started",
        }), 202

    detector = AnomalyDetector()
    threshold_detector = ThresholdDetector()

    if device_id:
        device = DeviceRepository.find_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        zscore_anomalies = detector.detect_and_store(device_id)
        threshold_anomalies_data = threshold_detector.check_device(device_id)
        for ad in threshold_anomalies_data:
            AnomalyRepository.create(ad)

        return jsonify({
            "device_id": device_id,
            "anomalies_found": len(zscore_anomalies),
            "anomalies": [a.to_dict() for a in zscore_anomalies],
        })
    else:
        from app.models.device import Device
        devices = Device.query.filter(Device.status != "offline").all()
        total_found = 0
        for device in devices:
            detector.detect_and_store(device.id)
            threshold_data = threshold_detector.check_device(device.id)
            for ad in threshold_data:
                AnomalyRepository.create(ad)
            total_found += len(threshold_data)

        return jsonify({
            "message": "Anomaly detection completed",
            "devices_analyzed": len(devices),
        })


@anomalies_bp.route("/anomalies/stats", methods=["GET"])
def anomaly_stats():
    open_count = AnomalyRepository.count_open()
    from app.models.anomaly import Anomaly
    from app.config.database import db
    severity_counts = dict(
        db.session.query(Anomaly.severity, db.func.count(Anomaly.id))
        .filter(Anomaly.status.in_(["open", "investigating"]))
        .group_by(Anomaly.severity).all()
    )
    category_counts = dict(
        db.session.query(Anomaly.category, db.func.count(Anomaly.id))
        .filter(Anomaly.status.in_(["open", "investigating"]))
        .group_by(Anomaly.category).all()
    )
    return jsonify({
        "open_count": open_count,
        "by_severity": severity_counts,
        "by_category": category_counts,
    })
