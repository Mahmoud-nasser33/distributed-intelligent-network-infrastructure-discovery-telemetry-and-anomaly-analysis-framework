import uuid
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Observation(db.Model):
    __tablename__ = "observations"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True, index=True)
    scan_job_id = db.Column(db.String(36), db.ForeignKey("scan_jobs.id"), nullable=True, index=True)

    source = db.Column(db.String(50), nullable=False)
    target_ip = db.Column(db.String(45), nullable=False, index=True)
    target_mac = db.Column(db.String(17), nullable=True)
    observation_type = db.Column(db.String(50), nullable=False, index=True)

    raw_data = db.Column(db.JSON, nullable=True)
    normalized_data = db.Column(db.JSON, nullable=True)

    confidence = db.Column(db.Float, nullable=True)

    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=True, index=True)

    timestamp = db.Column(db.DateTime, default=_now, index=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "scan_job_id": self.scan_job_id,
            "source": self.source,
            "target_ip": self.target_ip,
            "target_mac": self.target_mac,
            "observation_type": self.observation_type,
            "raw_data": self.raw_data,
            "normalized_data": self.normalized_data,
            "confidence": self.confidence,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
