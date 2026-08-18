import uuid
import enum
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class AnomalySeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Anomaly(db.Model):
    __tablename__ = "anomalies"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=False, index=True)

    detector = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    status = db.Column(db.String(20), default="open", index=True)

    metric_type = db.Column(db.String(30), nullable=True)
    observed_value = db.Column(db.Float, nullable=True)
    expected_value = db.Column(db.Float, nullable=True)
    threshold = db.Column(db.Float, nullable=True)

    confidence = db.Column(db.Float, nullable=True)
    evidence = db.Column(db.JSON, nullable=True)
    explanation = db.Column(db.Text, nullable=True)

    detected_at = db.Column(db.DateTime, default=_now, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "detector": self.detector,
            "category": self.category,
            "severity": self.severity,
            "status": self.status,
            "metric_type": self.metric_type,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "threshold": self.threshold,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "explanation": self.explanation,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
