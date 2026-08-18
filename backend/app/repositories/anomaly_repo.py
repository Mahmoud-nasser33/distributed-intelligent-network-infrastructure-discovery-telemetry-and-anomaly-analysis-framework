from typing import List, Optional
from app.config.database import db
from app.models.anomaly import Anomaly


class AnomalyRepository:

    @staticmethod
    def create(data: dict) -> Anomaly:
        anomaly = Anomaly(
            device_id=data["device_id"],
            detector=data["detector"],
            category=data["category"],
            severity=data["severity"],
            metric_type=data.get("metric_type"),
            observed_value=data.get("observed_value"),
            expected_value=data.get("expected_value"),
            threshold=data.get("threshold"),
            confidence=data.get("confidence"),
            evidence=data.get("evidence"),
            explanation=data.get("explanation"),
        )
        db.session.add(anomaly)
        db.session.commit()
        return anomaly

    @staticmethod
    def find_by_id(anomaly_id: str) -> Optional[Anomaly]:
        return Anomaly.query.get(anomaly_id)

    @staticmethod
    def find_by_device(device_id: str, limit: int = 50) -> List[Anomaly]:
        return Anomaly.query.filter_by(device_id=device_id)\
            .order_by(Anomaly.detected_at.desc()).limit(limit).all()

    @staticmethod
    def find_open(status: str = None, severity: str = None) -> List[Anomaly]:
        query = Anomaly.query
        if status:
            query = query.filter_by(status=status)
        else:
            query = query.filter(Anomaly.status.in_(["open", "investigating"]))
        if severity:
            query = query.filter_by(severity=severity)
        return query.order_by(Anomaly.detected_at.desc()).all()

    @staticmethod
    def find_recent(limit: int = 50) -> List[Anomaly]:
        return Anomaly.query.order_by(Anomaly.detected_at.desc()).limit(limit).all()

    @staticmethod
    def update_status(anomaly_id: str, status: str) -> Optional[Anomaly]:
        from datetime import datetime, timezone
        anomaly = Anomaly.query.get(anomaly_id)
        if anomaly:
            anomaly.status = status
            if status in ("resolved", "false_positive"):
                anomaly.resolved_at = datetime.now(timezone.utc)
            db.session.commit()
        return anomaly

    @staticmethod
    def count_open() -> int:
        return Anomaly.query.filter(
            Anomaly.status.in_(["open", "investigating"])
        ).count()
