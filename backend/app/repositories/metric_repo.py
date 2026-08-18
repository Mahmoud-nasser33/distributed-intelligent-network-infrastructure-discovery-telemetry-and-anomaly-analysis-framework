from typing import List, Optional
from app.config.database import db
from app.models.telemetry import Metric


class MetricRepository:

    @staticmethod
    def record(data: dict) -> Metric:
        metric = Metric(
            device_id=data["device_id"],
            metric_type=data["metric_type"],
            value=data["value"],
            unit=data.get("unit"),
            source=data.get("source"),
            agent_id=data.get("agent_id"),
            tags=data.get("tags"),
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @staticmethod
    def find_by_device(device_id: str, metric_type: str = None,
                       limit: int = 500) -> List[Metric]:
        query = Metric.query.filter_by(device_id=device_id)
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        return query.order_by(Metric.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_latest(device_id: str, metric_type: str) -> Optional[Metric]:
        return Metric.query.filter_by(
            device_id=device_id, metric_type=metric_type
        ).order_by(Metric.timestamp.desc()).first()

    @staticmethod
    def get_stats(device_id: str, metric_type: str) -> dict:
        from sqlalchemy import func
        result = db.session.query(
            func.avg(Metric.value),
            func.min(Metric.value),
            func.max(Metric.value),
            func.count(Metric.id)
        ).filter_by(device_id=device_id, metric_type=metric_type).first()

        avg, min_val, max_val, count = result
        return {
            "average": round(avg, 4) if avg else None,
            "min": min_val,
            "max": max_val,
            "count": count,
        }

    @staticmethod
    def find_time_range(device_id: str, metric_type: str,
                        start, end) -> List[Metric]:
        return Metric.query.filter(
            Metric.device_id == device_id,
            Metric.metric_type == metric_type,
            Metric.timestamp >= start,
            Metric.timestamp <= end,
        ).order_by(Metric.timestamp.asc()).all()
