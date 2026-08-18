import uuid
import enum
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class ScanJobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ScanJob(db.Model):
    __tablename__ = "scan_jobs"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True, index=True)

    target = db.Column(db.String(255), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False, default="discovery")
    scan_arguments = db.Column(db.JSON, nullable=True)

    status = db.Column(db.String(20), default="pending", index=True)
    progress = db.Column(db.Float, default=0.0)

    total_targets = db.Column(db.Integer, default=0)
    completed_targets = db.Column(db.Integer, default=0)
    failed_targets = db.Column(db.Integer, default=0)
    observations_count = db.Column(db.Integer, default=0)
    devices_found = db.Column(db.Integer, default=0)

    error_message = db.Column(db.Text, nullable=True)
    result_summary = db.Column(db.JSON, nullable=True)

    queued_at = db.Column(db.DateTime, default=_now)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    observations = db.relationship("Observation", backref="scan_job", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "target": self.target,
            "scan_type": self.scan_type,
            "scan_arguments": self.scan_arguments,
            "status": self.status,
            "progress": self.progress,
            "total_targets": self.total_targets,
            "completed_targets": self.completed_targets,
            "failed_targets": self.failed_targets,
            "observations_count": self.observations_count,
            "devices_found": self.devices_found,
            "error_message": self.error_message,
            "result_summary": self.result_summary,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
